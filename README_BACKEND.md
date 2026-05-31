# Web Annotator - CSV/JSON Database Schema Documentation

This document describes the schemas and vocabulary definitions for the local annotation database files stored under [`data/annotations/`](data/annotations).

The data is saved as standard UTF-8 encoded files with headers, ensuring easy consumption by Pandas, PyTorch dataset loaders, or ensembling scripts.

---

## 📋 1. Video Index (`videos.csv`)
This file is the primary registry of all video assets whitelisted and indexed by the application.

* **File Path**: [`data/annotations/videos.csv`](data/annotations/videos.csv)
* **Headers**: `video_id,path,actor,coarse_label,fps,frames,duration_s,width,height`

### Column Definitions:
| Column | Type | Description | Example |
|---|---|---|---|
| `video_id` | `string` | Unique, stable SHA-1 hash-derived string identifying the video | `unsafe_blooza_good_20260512_190928_e128f9d0` |
| `path` | `string` | Relative path to the video file from the workspace root | `data/captures/ilyas/unsafe/unsafe blooza good  20260512_190928.mp4` |
| `actor` | `string` | Name of the person in the video | `ilyas` |
| `coarse_label` | `string` | Folder-level categorization: `safe` or `unsafe` | `unsafe` |
| `fps` | `float` | Capture frame rate (frames per second) | `30.0` |
| `frames` | `integer` | Total number of frames in the video clip | `119` |
| `duration_s` | `float` | Duration of the clip in seconds | `3.967` |
| `width` | `integer` | Horizontal resolution of the video in pixels | `1440` |
| `height` | `integer` | Vertical resolution of the video in pixels | `720` |

---

## ⏱️ 2. Temporal State Segments (`segments.csv`)
This file stores time-range annotations marking the actor's attention level and blouse clothing state.

* **File Path**: [`data/annotations/segments.csv`](data/annotations/segments.csv)
* **Headers**: `video_id,start_s,end_s,attention,blouse,notes`

### Column Definitions:
| Column | Type | Description | Example |
|---|---|---|---|
| `video_id` | `string` | ID matching the indexed video in `videos.csv` | `unsafe_blooza_good_20260512_190928_e128f9d0` |
| `start_s` | `float` | Start timestamp of the segment in seconds | `0.000` |
| `end_s` | `float` | End timestamp of the segment in seconds | `3.967` |
| `attention` | `string` | Actor's attention state: `attentive` or `distracted` | `attentive` |
| `blouse` | `string` | Actor's clothing closure state: `properly_worn` or `badly_worn` | `properly_worn` |
| `notes` | `string` | Free-form researcher or operator notes | `Operator wears fully zipped clothing` |

---

## 📍 3. Danger Onset Events (`events.csv`)
This file records exact frame-accurate pins indicating when and how a hazard began (i.e. physical penetration of the safety volume).

* **File Path**: [`data/annotations/events.csv`](data/annotations/events.csv)
* **Headers**: `video_id,event_time_s,frame,event_role,body_part,event_type,zone_id,spatial_relation,notes`

### Column Definitions:
| Column | Type | Description | Example |
|---|---|---|---|
| `video_id` | `string` | ID matching the indexed video in `videos.csv` | `unsafe_blooza_good_20260512_190928_e128f9d0` |
| `event_time_s` | `float` | Precise time in seconds of the danger onset | `1.450` |
| `frame` | `integer` | 0-indexed frame number of the danger onset | `44` |
| `event_role` | `string` | The causal role of this event: `physical_entry`, `risk_onset`, or `no_danger` | `physical_entry` |
| `body_part` | `string` | The body parts entering the zone. Can be combined using pipe `\|` characters | `hand_or_arm` or `hand_or_arm\|head` |
| `event_type` | `string` | Type of event: `entered_danger_volume`, `near_miss`, or `no_danger_event` | `entered_danger_volume` |
| `zone_id` | `string` | Danger region key, always matches the ID inside `zones.json` | `machine_danger_volume` |
| `spatial_relation` | `string` | Spatial layout relative to the polygon: `inside_volume`, `near_volume`, `outside_volume` | `inside_volume` |
| `notes` | `string` | Details about the penetration or movement | `Right wrist crosses the top polygon boundary` |

### Allowed Vocabulary Lists:
* **`body_part`**: `hand_or_arm`, `head`, `right_wrist`, `left_wrist`, `right_elbow`, `left_elbow`, `right_arm`, `left_arm`, `torso`, `none`
* **`event_role`**: `physical_entry`, `risk_onset`, `no_danger`
* **`event_type`**: `entered_danger_volume`, `near_miss`, `no_danger_event`
* **`spatial_relation`**: `inside_volume`, `near_volume`, `outside_volume`, `above_projection`

---

## 📐 4. Danger Zone Definition (`zones.json`)
A JSON file containing the 2D projected outline polygon of the machine's safety zone, scaled to the capture resolution coordinates.

* **File Path**: [`data/annotations/zones.json`](data/annotations/zones.json)
* **Structure**:
  ```json
  {
    "zones": [
      {
        "zone_id": "machine_danger_volume",
        "shape": "projected_volume_polygon",
        "image_width": 1440,
        "image_height": 720,
        "points": [
          [640, 522],
          [575, 714],
          [916, 715],
          [942, 545],
          [913, 499],
          [836, 528]
        ],
        "active_body_parts": [
          "right_wrist",
          "left_wrist",
          "right_elbow",
          "left_elbow",
          "head",
          "torso"
        ],
        "notes": "Single fixed-camera projection of the machine danger volume."
      }
    ]
  }
  ```

---

## 🗑️ 5. Deleted / Excluded Clips (`deleted_clips.csv`)
Logs clips that were intentionally removed or skipped during processing, alongside the reason for exclusion (e.g. framing errors, corrupt files).

* **File Path**: [`data/annotations/deleted_clips.csv`](data/annotations/deleted_clips.csv)
* **Headers**: `video_id,path,reason`
