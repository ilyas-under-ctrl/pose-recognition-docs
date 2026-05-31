import csv
import json
import sys
from pathlib import Path

from annotation_tool import (
    ANNOTATION_DIR,
    APP_DIR,
    ATTENTION_LABELS,
    BLOUSE_LABELS,
    BODY_PARTS,
    EVENTS_CSV,
    EVENT_HEADERS,
    EVENT_ROLES,
    EVENT_TYPES,
    SEGMENTS_CSV,
    SEGMENT_HEADERS,
    SPATIAL_RELATIONS,
    VIDEOS_CSV,
    VIDEO_HEADERS,
    ZONES_JSON,
)


def read_csv(path, headers):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [{header: row.get(header, "") for header in headers} for row in csv.DictReader(handle)]


def as_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def main():
    errors = []
    warnings = []

    videos = read_csv(VIDEOS_CSV, VIDEO_HEADERS)
    segments = read_csv(SEGMENTS_CSV, SEGMENT_HEADERS)
    events = read_csv(EVENTS_CSV, EVENT_HEADERS)

    by_id = {}
    for row in videos:
        video_id = row["video_id"]
        if not video_id:
            errors.append("videos.csv contains a row with empty video_id")
            continue
        if video_id in by_id:
            errors.append(f"duplicate video_id in videos.csv: {video_id}")
        by_id[video_id] = row
        if not (APP_DIR / row["path"]).exists():
            errors.append(f"missing video file for {video_id}: {row['path']}")

    for row in segments:
        video = by_id.get(row["video_id"])
        if video is None:
            errors.append(f"segment references unknown video_id: {row['video_id']}")
            continue
        start = as_float(row["start_s"])
        end = as_float(row["end_s"])
        duration = as_float(video["duration_s"], 0.0)
        if start is None or end is None:
            errors.append(f"segment has invalid start/end time: {row}")
        elif start < 0 or end <= start or end > duration + 0.05:
            errors.append(f"segment outside video duration for {row['video_id']}: {start}-{end}s, duration={duration}s")
        if row["attention"] not in ATTENTION_LABELS:
            errors.append(f"segment has invalid attention label: {row}")
        if row["blouse"] not in BLOUSE_LABELS:
            errors.append(f"segment has invalid blouse label: {row}")

    danger_events = 0
    no_danger_events = 0
    for row in events:
        video = by_id.get(row["video_id"])
        if video is None:
            errors.append(f"event references unknown video_id: {row['video_id']}")
            continue
        event_type = row["event_type"]
        event_role = row.get("event_role", "")
        if event_type not in EVENT_TYPES:
            errors.append(f"event has invalid event_type: {row}")
        if event_role and event_role not in EVENT_ROLES:
            errors.append(f"event has invalid event_role: {row}")
        body_parts = [part for part in row["body_part"].split("|") if part]
        if not body_parts:
            errors.append(f"event has empty body_part: {row}")
        for body_part in body_parts:
            if body_part not in BODY_PARTS:
                errors.append(f"event has invalid body_part '{body_part}': {row}")
        if row["spatial_relation"] not in SPATIAL_RELATIONS:
            errors.append(f"event has invalid spatial_relation: {row}")

        if event_type == "no_danger_event":
            no_danger_events += 1
            continue

        danger_events += 1
        event_time = as_float(row["event_time_s"])
        frame = as_float(row["frame"])
        duration = as_float(video["duration_s"], 0.0)
        frame_count = as_float(video["frames"], 0.0)
        if event_time is None:
            errors.append(f"danger event missing event_time_s: {row}")
        elif event_time < 0 or event_time > duration + 0.05:
            errors.append(f"danger event outside duration for {row['video_id']}: {event_time}s, duration={duration}s")
        if frame is None:
            errors.append(f"danger event missing frame: {row}")
        elif frame < 0 or frame > max(0, frame_count - 1):
            errors.append(f"danger event frame outside range for {row['video_id']}: {frame}, frames={frame_count}")

    if not ZONES_JSON.exists():
        warnings.append("annotations/zones.json does not exist yet; draw and save the projected danger-volume zone")
    else:
        try:
            data = json.loads(ZONES_JSON.read_text(encoding="utf-8"))
            zones = data.get("zones", []) if isinstance(data, dict) else []
            if not zones:
                errors.append("zones.json has no zones")
            for zone in zones:
                points = zone.get("points", [])
                width = int(zone.get("image_width", 0) or 0)
                height = int(zone.get("image_height", 0) or 0)
                if len(points) < 3:
                    warnings.append(f"zone {zone.get('zone_id', '<unknown>')} has fewer than 3 points")
                for point in points:
                    if not isinstance(point, list) or len(point) != 2:
                        errors.append(f"invalid zone point: {point}")
                        continue
                    x, y = point
                    if x < 0 or y < 0 or (width and x >= width) or (height and y >= height):
                        errors.append(f"zone point outside image bounds: {point}, size={width}x{height}")
        except json.JSONDecodeError as exc:
            errors.append(f"zones.json is invalid JSON: {exc}")

    print(f"annotation_dir: {ANNOTATION_DIR}")
    print(f"videos: {len(videos)}")
    print(f"segments: {len(segments)}")
    print(f"events: {len(events)}")
    print(f"danger_events: {danger_events}")
    print(f"no_danger_events: {no_danger_events}")

    if warnings:
        print("\nwarnings:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("\nerrors:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nvalidation: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
