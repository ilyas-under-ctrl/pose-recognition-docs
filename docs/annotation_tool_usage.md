# Annotation Tool Usage

Recommended browser app:

```powershell
python web_annotator_server.py
```

Open:

```text
http://127.0.0.1:8765
```

or double-click:

```text
run_web_annotation_tool.bat
```

The browser version is the preferred UI. It uses native video playback, canvas overlays, and a video-editor-style timeline while saving the same CSV/JSON annotation files.

## Video Loading Speed

The original clips are encoded as `mp4v`, which many browsers do not play directly. The web annotator keeps your original videos untouched and creates browser-playable H.264 copies in `.web_media_cache/`.

The first time a clip opens, it may be slow because that cached copy is being prepared. To remove that delay for the whole dataset, click `Prepare All Clips` in the browser UI, or run:

```powershell
python prepare_web_media_cache.py
```

This can take several minutes, but it is a one-time setup. After a clip is cached, it opens quickly.

The cache is encoded with dense keyframes for annotation. That makes slider seeking and left/right frame stepping much more reliable than normal playback-optimized MP4 files, at the cost of a larger cache folder.

Legacy Tkinter app:

```powershell
python annotation_tool.py
```

or double-click:

```text
run_annotation_tool.bat
```

## First Pass: Define The Zone

1. Open any representative video.
2. Use the queue filter if useful. `unsafe` is usually the fastest way to see the risky machine area first.
3. Press `F` or `Zone Review 8x` to watch the filtered clips quickly with auto-next enabled.
4. Pause on a clear frame that shows the machine danger area.
5. Press `Edit Zone`.
6. Click points around the visible projection of the machine danger volume.
7. Drag yellow points to adjust the polygon.
8. Click empty space to add another point.
9. Right-click a point to delete it.
10. Press `Save Zone`.

The zone is saved to `annotations/zones.json`.

This is a projected 2D outline of the 3D volume. It is used as a feature and annotation reference, not as proof of true 3D entry.

## Per-Video Workflow

The app uses two annotation types:

- `Segment`: a time range. Use it when a label lasts for part or all of a clip, like `attentive` from 0.0s to 2.4s or `badly_worn` for the whole clip.
- `Event`: one exact timestamp. Use it for the first frame where danger begins. The red timeline marker is an event.

This is the same idea as a video editor: segments are bars over time, events are pins/markers on the timeline.

For a safe video:

1. Choose attention and blouse labels.
2. Press `W` or `Whole Clip` if the labels are constant for the clip.
3. Press `G` or `No Danger`.
4. Press `N` for the next video.

For an unsafe video:

1. Choose attention and blouse labels.
2. Save a full-clip segment, or use `Start Segment` / `End + Save Segment` if the state changes.
3. Scrub to the first frame where the hand, arm, head, or torso enters the danger volume.
4. Select one or more `Danger sources`.
5. Select `Spatial`.
6. Press `Mark Danger Event`.
7. If the marker is slightly off, drag the red timeline marker left/right to adjust the exact timestamp.
8. Press `Next`.

## Keyboard Shortcuts

| Key | Action |
| --- | --- |
| Space | Play/pause |
| Left / Right | Move one frame |
| Shift+Left / Shift+Right | Move one second |
| Home / End | Jump to first / last frame |
| `F` | Zone review: play filtered queue at 8x and auto-advance |
| `A` / `D` / `U` | Set attention: attentive / distracted / unknown |
| `R` / `B` | Set blouse: properly worn / badly worn |
| `1` | Toggle danger source: hand or arm |
| `2` | Toggle danger source: head |
| `3` | Toggle danger source: torso |
| `4` | Toggle danger source: unknown |
| `s` | Start segment |
| `e` | End and save segment |
| `w` | Save whole-clip segment |
| `m` | Mark danger event |
| `g` | Mark no danger |
| `n` | Next video |
| `p` | Previous video |
| `z` | Toggle danger-zone editing |
| Ctrl+S | Save danger-zone polygon |
| Ctrl+Z | Undo last event for current video |
| Ctrl+Shift+Z | Undo last segment for current video |

## Timeline

The timeline under the video behaves like a lightweight video editor:

- Blue vertical line: current playhead.
- Colored bars: saved attention/blouse segments.
- Red pins: danger events.
- Click the timeline to jump.
- Drag a red pin to move a danger event timestamp.

Use the red pin to fine-tune danger marking after pressing `M`.

## Queue UI

The video queue shows annotation status:

- `✓`: segment and event/no-danger annotation both exist.
- `E`: event exists but segment is missing.
- `S`: segment exists but event/no-danger annotation is missing.
- `○`: untouched.

Use the search box to filter by filename, actor, or label. Use the dropdown for `safe`, `unsafe`, `needs_review`, or `reviewed`.

For danger-zone setup, filter to `unsafe`, press `F`, and watch the clips at super speed. Playback uses a time-based loop targeting 165 Hz so fast review is smoother than fixed frame skipping. The source videos are still 30 FPS, so the app cannot show more real captured frames than exist in the files. Once you understand where the hand/arm/head repeatedly enters, pause and draw the zone around that projected machine volume.

## Label Definitions

Attention:

- `attentive`: looking toward the task/machine.
- `distracted`: clearly looking away.
- `unknown`: not visible or ambiguous.

Blouse:

- `properly_worn`: closed/proper.
- `badly_worn`: open or incorrect.
- `unknown`: not visible or ambiguous.

Spatial:

- `inside_volume`: body part has entered the danger volume.
- `near_volume`: body part is near but not inside.
- `above_projection`: body part visually overlaps the projected zone but appears above/not inside.
- `outside_volume`: clearly outside.
- `occluded`: cannot see the body part.
- `unknown`: unclear.

Danger sources are multi-label. If both hands/arms and head enter the volume at the same event timestamp, select both `hand_or_arm` and `head`. The saved CSV stores that as `hand_or_arm|head`.

## Output Files

- `annotations/videos.csv`
- `annotations/segments.csv`
- `annotations/events.csv`
- `annotations/zones.json`

Do not edit the video files. The tool only writes annotations.

## Validate The Work

Run this after an annotation session:

```powershell
python validate_annotations.py
```

The validator checks that video IDs exist, segment times are inside the clip, event frames are valid, labels are from the allowed set, and the saved danger-zone polygon is well formed.
