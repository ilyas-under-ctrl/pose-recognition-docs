# Web Annotator - API Endpoint Documentation

This document describes the local HTTP and JSON API endpoints provided by the annotation server in [`backend/web_annotator_server.py`](backend/web_annotator_server.py). 

The backend runs on **`http://127.0.0.1:8765`** by default. All POST/PUT payloads and non-media responses use standard JSON format.

---

## 🧭 Static Assets & Client UI
* **`GET /`**: Serves the main web dashboard frontend ([`dashboard/web_annotator/index.html`](dashboard/web_annotator/index.html)).
* **`GET /{asset}`**: Serves static frontend resources (such as `app.js`, `styles.css`) from the dashboard folder.

---

## 📊 Core State API

### `GET /api/state`
Retrieves the entire active database state, including whitelisted videos, segment annotations, marked events, hazard zone polygons, and supported vocabulary lists.

* **Response Payload (JSON)**:
  ```json
  {
    "videos": [
      {
        "video_id": "unsafe_blooza_good_20260512_190928_e128f9d0",
        "path": "data/captures/ilyas/unsafe/unsafe blooza good  20260512_190928.mp4",
        "actor": "ilyas",
        "coarse_label": "unsafe",
        "fps": "30.0",
        "frames": "119",
        "duration_s": "3.967",
        "width": "1440",
        "height": "720"
      }
    ],
    "segments": [],
    "events": [],
    "zones": {
      "zones": [
        {
          "zone_id": "machine_danger_volume",
          "shape": "projected_volume_polygon",
          "image_width": 1440,
          "image_height": 720,
          "points": [[640, 522], [575, 714], [916, 715], [942, 545]],
          "active_body_parts": ["right_wrist", "left_wrist", "head"],
          "notes": "Projected machine danger volume polygon."
        }
      ]
    },
    "bodyParts": ["hand_or_arm", "head", "right_wrist", "left_wrist", "right_elbow", "left_elbow", "right_arm", "left_arm", "none"]
  }
  ```

### `GET /api/health`
Lightweight ping endpoint to verify that the server is alive and responding.
* **Response Payload**: `{"ok": true}`

---

## 🎬 Media Streaming & Transcoding

### `GET /media?path={relative_path}`
Streams the original raw video file from disk. Supports standard HTTP Range requests for fast scrubbing/seeking.

### `GET /web-media?path={relative_path}`
Streams the H.264 browser-playable version of the clip. If the H.264 version is not cached yet, this triggers an on-demand, blocking FFmpeg transcode first.

### `GET /thumb?path={relative_path}&t={seconds}`
Extracts and returns a JPEG thumbnail from the video at the given timestamp using OpenCV. Used to show timeline preview images.

### `GET /api/cache/status`
Checks the progress of the background transcoding queue.
* **Response Payload**:
  ```json
  {
    "ok": true,
    "cache": {
      "running": false,
      "total": 73,
      "done": 73,
      "current": "",
      "errors": [],
      "started_at": 1716949392.12,
      "finished_at": 1716949454.43,
      "cache_dir": "C:\\...\\data\\.web_media_cache",
      "cached_files": 73,
      "cached_bytes": 184920402,
      "cache_version": "seekv2"
    }
  }
  ```

### `POST /api/cache/start`
Triggers the background thread to transcode all indexed videos to fast-seeking H.264 copies under `data/.web_media_cache/`.

---

## 💾 Annotation Writing APIs

### `POST /api/segments`
Saves or replaces a temporal segment annotation (attention/blouse states) for a clip.
* **Request Body**:
  ```json
  {
    "video_id": "unsafe_blooza_good_20260512_190928_e128f9d0",
    "start_s": "0.000",
    "end_s": "3.967",
    "attention": "attentive",
    "blouse": "properly_worn",
    "notes": "Proper clothing throughout"
  }
  ```
* **Response Payload**: `{"ok": true, "state": { ... }}`

### `POST /api/events`
Saves a spatial danger onset event (the exact frame/second where danger begins).
* **Request Body**:
  ```json
  {
    "video_id": "unsafe_blooza_good_20260512_190928_e128f9d0",
    "event_time_s": "1.450",
    "frame": "44",
    "event_role": "physical_entry",
    "body_part": "hand_or_arm",
    "event_type": "entered_danger_volume",
    "zone_id": "machine_danger_volume",
    "spatial_relation": "inside_volume",
    "notes": "Right hand enters danger zone"
  }
  ```

### `PUT /api/events/{index}`
Updates specific fields of an event by its list row index (used when dragging event pins on the timeline).
* **Request Body**: `{"event_time_s": "1.520", "frame": "46"}`

### `POST /api/zones`
Saves the coordinates of the 2D projected safety danger zone polygon.
* **Request Body**:
  ```json
  {
    "zones": [
      {
        "zone_id": "machine_danger_volume",
        "shape": "projected_volume_polygon",
        "image_width": 1440,
        "image_height": 720,
        "points": [[640, 522], [575, 714], [916, 715], [942, 545], [913, 499], [836, 528]],
        "active_body_parts": ["right_wrist", "left_wrist", "right_elbow", "left_elbow", "head", "torso"],
        "notes": "Polygon outline of the danger volume"
      }
    ]
  }
  ```

---

## 🧹 Undo & Reset Actions

### `POST /api/undo-event`
Deletes the last recorded event for a specific video ID.
* **Request Body**: `{"video_id": "unsafe_blooza_good_20260512_190928_e128f9d0"}`

### `POST /api/undo-segment`
Deletes the last recorded segment for a specific video ID.
* **Request Body**: `{"video_id": "unsafe_blooza_good_20260512_190928_e128f9d0"}`

### `POST /api/reset-clip`
Deletes all segments and events associated with a specific video ID.
* **Request Body**: `{"video_id": "unsafe_blooza_good_20260512_190928_e128f9d0"}`
