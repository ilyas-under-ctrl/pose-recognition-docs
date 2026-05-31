import csv
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import cv2

from annotation_tool import (
    ANNOTATION_DIR,
    APP_DIR,
    BODY_PARTS,
    EVENTS_CSV,
    EVENT_HEADERS,
    EVENT_ROLES,
    SEGMENTS_CSV,
    SEGMENT_HEADERS,
    VIDEOS_CSV,
    VIDEO_HEADERS,
    ZONES_JSON,
    ensure_video_index,
)


WEB_DIR = APP_DIR.parent / "dashboard" / "web_annotator"
WEB_MEDIA_DIR = APP_DIR.parent / "data" / ".web_media_cache"
CACHE_VERSION = "seekv2"
DEFAULT_PORT = 8765
CACHE_JOB = {
    "running": False,
    "total": 0,
    "done": 0,
    "current": "",
    "errors": [],
    "started_at": None,
    "finished_at": None,
}
CACHE_LOCK = threading.Lock()


def read_csv(path, headers):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [{header: row.get(header, "") for header in headers} for row in csv.DictReader(handle)]


def write_csv(path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows([{header: row.get(header, "") for header in headers} for row in rows])


def append_csv(path, headers, row):
    rows = read_csv(path, headers)
    rows.append(row)
    write_csv(path, headers, rows)


def replace_rows(path, headers, predicate, new_rows):
    rows = [row for row in read_csv(path, headers) if not predicate(row)]
    rows.extend(new_rows)
    write_csv(path, headers, rows)


def normalized_event_role(row):
    role = row.get("event_role", "")
    event_type = row.get("event_type", "")
    if event_type == "no_danger_event":
        return "no_danger"
    if role in EVENT_ROLES:
        return role
    return "risk_onset"


def read_json_body(handler):
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}
    body = handler.rfile.read(length)
    return json.loads(body.decode("utf-8"))


def safe_media_path(relative_path):
    candidate = (APP_DIR / relative_path).resolve()
    root = APP_DIR.resolve()
    if os.path.commonpath([str(root), str(candidate)]) != str(root):
        raise ValueError("path escapes project directory")
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def cached_media_path(relative_path):
    source = safe_media_path(relative_path)
    normalized = str(Path(relative_path)).replace("\\", "/")
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
    stem = re.sub(r"[^A-Za-z0-9]+", "_", source.stem).strip("_")[:70]
    return WEB_MEDIA_DIR / f"{stem}_{digest}_{CACHE_VERSION}.mp4", source


def ensure_web_media(relative_path):
    WEB_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    cache_path, source = cached_media_path(relative_path)
    if cache_path.exists() and cache_path.stat().st_mtime >= source.stat().st_mtime:
        return cache_path

    temp_path = cache_path.with_suffix(".tmp.mp4")
    if temp_path.exists():
        temp_path.unlink()

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "30",
        "-g",
        "1",
        "-keyint_min",
        "1",
        "-sc_threshold",
        "0",
        "-bf",
        "0",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(temp_path),
    ]
    subprocess.run(command, check=True)
    temp_path.replace(cache_path)
    return cache_path


def cache_all_videos_worker():
    ensure_video_index()
    videos = read_csv(VIDEOS_CSV, VIDEO_HEADERS)
    with CACHE_LOCK:
        CACHE_JOB.update(
            {
                "running": True,
                "total": len(videos),
                "done": 0,
                "current": "",
                "errors": [],
                "started_at": time.time(),
                "finished_at": None,
            }
        )
    for video in videos:
        relative_path = video.get("path", "")
        with CACHE_LOCK:
            CACHE_JOB["current"] = relative_path
        try:
            ensure_web_media(relative_path)
        except Exception as exc:
            with CACHE_LOCK:
                CACHE_JOB["errors"].append({"path": relative_path, "error": str(exc)})
        finally:
            with CACHE_LOCK:
                CACHE_JOB["done"] += 1
    with CACHE_LOCK:
        CACHE_JOB["running"] = False
        CACHE_JOB["current"] = ""
        CACHE_JOB["finished_at"] = time.time()


def cache_status():
    with CACHE_LOCK:
        status = dict(CACHE_JOB)
        status["errors"] = list(CACHE_JOB["errors"])
    status["cache_dir"] = str(WEB_MEDIA_DIR)
    pattern = f"*_{CACHE_VERSION}.mp4"
    cached = list(WEB_MEDIA_DIR.glob(pattern)) if WEB_MEDIA_DIR.exists() else []
    status["cached_files"] = len(cached)
    status["cached_bytes"] = sum(path.stat().st_size for path in cached)
    status["cache_version"] = CACHE_VERSION
    return status


class WebAnnotatorHandler(BaseHTTPRequestHandler):
    server_version = "WebAnnotator/1.0"

    def log_message(self, format, *args):
        sys.stdout.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format % args))

    def send_json(self, payload, status=HTTPStatus.OK):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, text, status=HTTPStatus.OK):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/":
            self.serve_static(WEB_DIR / "index.html")
            return
        if path == "/api/state":
            self.handle_state()
            return
        if path == "/api/health":
            self.send_json({"ok": True})
            return
        if path == "/api/cache/status":
            self.send_json({"ok": True, "cache": cache_status()})
            return
        if path == "/media":
            query = urllib.parse.parse_qs(parsed.query)
            relative = query.get("path", [""])[0]
            self.serve_media(relative)
            return
        if path == "/web-media":
            query = urllib.parse.parse_qs(parsed.query)
            relative = query.get("path", [""])[0]
            self.serve_web_media(relative)
            return
        if path == "/thumb":
            query = urllib.parse.parse_qs(parsed.query)
            relative = query.get("path", [""])[0]
            seconds = float(query.get("t", ["0.2"])[0] or 0.2)
            self.serve_thumbnail(relative, seconds)
            return
        if path.startswith("/"):
            static_path = (WEB_DIR / path.lstrip("/")).resolve()
            if os.path.commonpath([str(WEB_DIR.resolve()), str(static_path)]) == str(WEB_DIR.resolve()):
                self.serve_static(static_path)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            if parsed.path == "/api/segments":
                self.handle_add_segment()
            elif parsed.path == "/api/events":
                self.handle_add_event()
            elif parsed.path == "/api/zones":
                self.handle_save_zones()
            elif parsed.path == "/api/undo-event":
                self.handle_undo(EVENTS_CSV, EVENT_HEADERS)
            elif parsed.path == "/api/undo-segment":
                self.handle_undo(SEGMENTS_CSV, SEGMENT_HEADERS)
            elif parsed.path == "/api/reset-clip":
                self.handle_reset_clip()
            elif parsed.path == "/api/cache/start":
                self.handle_cache_start()
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        match = re.fullmatch(r"/api/events/(\d+)", parsed.path)
        if not match:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            self.handle_update_event(int(match.group(1)))
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def serve_static(self, path):
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_media(self, relative):
        try:
            path = safe_media_path(relative)
        except (ValueError, FileNotFoundError):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.serve_file_range(path, mimetypes.guess_type(path.name)[0] or "video/mp4")

    def serve_web_media(self, relative):
        try:
            path = ensure_web_media(relative)
        except (ValueError, FileNotFoundError, subprocess.CalledProcessError) as exc:
            self.send_json({"ok": False, "error": f"Could not prepare web video: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.serve_file_range(path, "video/mp4")

    def serve_file_range(self, path, mime):
        file_size = path.stat().st_size
        range_header = self.headers.get("Range")
        start = 0
        end = file_size - 1
        status = HTTPStatus.OK

        if range_header:
            match = re.match(r"bytes=(\d*)-(\d*)", range_header)
            if match:
                if match.group(1):
                    start = int(match.group(1))
                if match.group(2):
                    end = int(match.group(2))
                end = min(end, file_size - 1)
                status = HTTPStatus.PARTIAL_CONTENT

        if start > end or start >= file_size:
            self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            return

        chunk_size = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(chunk_size))
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.end_headers()

        with path.open("rb") as handle:
            handle.seek(start)
            remaining = chunk_size
            while remaining > 0:
                data = handle.read(min(1024 * 1024, remaining))
                if not data:
                    break
                self.wfile.write(data)
                remaining -= len(data)

    def serve_thumbnail(self, relative, seconds):
        try:
            path = safe_media_path(relative)
        except (ValueError, FileNotFoundError):
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
        frame = max(0, int(seconds * fps))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        ok, image = cap.read()
        cap.release()
        if not ok:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        data = encoded.tobytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def state_payload(self):
        ensure_video_index()
        videos = read_csv(VIDEOS_CSV, VIDEO_HEADERS)
        segments = read_csv(SEGMENTS_CSV, SEGMENT_HEADERS)
        events = read_csv(EVENTS_CSV, EVENT_HEADERS)
        for idx, row in enumerate(segments):
            row["_row_index"] = idx
        for idx, row in enumerate(events):
            row["_row_index"] = idx
        zones = {"zones": []}
        if ZONES_JSON.exists():
            zones = json.loads(ZONES_JSON.read_text(encoding="utf-8"))
        return {
            "videos": videos,
            "segments": segments,
            "events": events,
            "zones": zones,
            "bodyParts": BODY_PARTS,
        }

    def handle_state(self):
        self.send_json(self.state_payload())

    def handle_add_segment(self):
        row = read_json_body(self)
        video_id = row.get("video_id", "")
        start = row.get("start_s", "")
        end = row.get("end_s", "")
        attention = row.get("attention", "")
        blouse = row.get("blouse", "")

        def duplicate_segment(existing):
            if existing.get("video_id") != video_id:
                return False
            same_range = existing.get("start_s") == start and existing.get("end_s") == end
            same_labels = existing.get("attention") == attention and existing.get("blouse") == blouse
            full_clip_replacement = start == "0.000" and existing.get("start_s") == "0.000"
            return (same_range and same_labels) or full_clip_replacement

        replace_rows(SEGMENTS_CSV, SEGMENT_HEADERS, duplicate_segment, [row])
        self.send_json({"ok": True, "state": self.state_payload()})

    def handle_add_event(self):
        row = read_json_body(self)
        video_id = row.get("video_id", "")
        role = normalized_event_role(row)
        row["event_role"] = role

        def same_video_event(existing):
            if existing.get("video_id") != video_id:
                return False
            if role == "no_danger":
                return True
            return normalized_event_role(existing) in (role, "no_danger")

        replace_rows(EVENTS_CSV, EVENT_HEADERS, same_video_event, [row])
        self.send_json({"ok": True, "state": self.state_payload()})

    def handle_update_event(self, index):
        payload = read_json_body(self)
        rows = read_csv(EVENTS_CSV, EVENT_HEADERS)
        if not (0 <= index < len(rows)):
            raise ValueError("event index out of range")
        for field in ("event_time_s", "frame", "event_role", "body_part", "event_type", "spatial_relation", "notes"):
            if field in payload:
                rows[index][field] = str(payload[field])
        write_csv(EVENTS_CSV, EVENT_HEADERS, rows)
        self.send_json({"ok": True, "state": self.state_payload()})

    def handle_save_zones(self):
        payload = read_json_body(self)
        if "zones" not in payload:
            raise ValueError("payload must contain zones")
        ZONES_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.send_json({"ok": True, "state": self.state_payload()})

    def handle_undo(self, path, headers):
        payload = read_json_body(self)
        video_id = payload.get("video_id")
        rows = read_csv(path, headers)
        for idx in range(len(rows) - 1, -1, -1):
            if rows[idx].get("video_id") == video_id:
                removed = rows.pop(idx)
                write_csv(path, headers, rows)
                self.send_json({"ok": True, "removed": removed, "state": self.state_payload()})
                return
        self.send_json({"ok": True, "removed": None, "state": self.state_payload()})

    def handle_reset_clip(self):
        payload = read_json_body(self)
        video_id = payload.get("video_id")
        if not video_id:
            raise ValueError("video_id is required")

        segment_rows = read_csv(SEGMENTS_CSV, SEGMENT_HEADERS)
        event_rows = read_csv(EVENTS_CSV, EVENT_HEADERS)
        kept_segments = [row for row in segment_rows if row.get("video_id") != video_id]
        kept_events = [row for row in event_rows if row.get("video_id") != video_id]
        removed_segments = len(segment_rows) - len(kept_segments)
        removed_events = len(event_rows) - len(kept_events)
        write_csv(SEGMENTS_CSV, SEGMENT_HEADERS, kept_segments)
        write_csv(EVENTS_CSV, EVENT_HEADERS, kept_events)
        self.send_json({
            "ok": True,
            "removed_segments": removed_segments,
            "removed_events": removed_events,
            "state": self.state_payload(),
        })

    def handle_cache_start(self):
        already_running = False
        with CACHE_LOCK:
            if CACHE_JOB["running"]:
                already_running = True
            else:
                CACHE_JOB["running"] = True
        if already_running:
            self.send_json({"ok": True, "cache": cache_status()})
            return
        thread = threading.Thread(target=cache_all_videos_worker, daemon=True)
        thread.start()
        self.send_json({"ok": True, "cache": cache_status()})


def main():
    ANNOTATION_DIR.mkdir(parents=True, exist_ok=True)
    ensure_video_index()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    server = ThreadingHTTPServer(("127.0.0.1", port), WebAnnotatorHandler)
    print(f"Web annotator running at http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
