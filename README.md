# Phone Live Feed Prototype

This prototype shows a live MJPEG/IP-camera stream from a phone on the laptop and saves snapshots or recordings on the laptop.

## Phone setup

1. On Windows, enable **Mobile hotspot**.
2. Connect the phone to that hotspot.
3. Open an IP camera app on the phone and start the stream.
4. Copy the stream URL shown by the app. It usually looks like one of these:

```text
http://192.168.137.x:8080/video
http://192.168.137.x:8080/stream.mjpg
```

Use the actual URL displayed by the app.

## Laptop setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the viewer:

```powershell
python phone_feed_app.py
```

Paste the phone stream URL, then click **Connect**.

To test whether the phone stream is the bottleneck, choose **Webcam 0** or **Webcam 2** from the source dropdown and click **Connect**.

Enable pose detection to draw live person keypoints/skeletons on the stream. Use **MediaPipe** for the lowest latency and **YOLO** for heavier comparison. The first MediaPipe use downloads `pose_landmarker_lite.task`; the first YOLO use may download `yolo11n-pose.pt`.

If the preview lags, lower **Pose FPS** or **Size** first. The live video stays current while YOLO runs in the background.

## Notes

- Start with 1280x720 at 30 FPS if the phone app lets you choose.
- For lower latency, use **MediaPipe**, 640x480, **Pose FPS** around 15, and **Size** around 320.
- For YOLO on CPU, keep **Size** at 320 and reduce **Pose FPS** if needed. On CUDA GPUs, 320-480 is usually usable.
- Recordings and snapshots are saved in `captures/`.
- If **YOLO Pose** is enabled, recordings and snapshots include the pose overlay.
- Recording is laptop-side, so it works even if the phone app only streams video.

## Annotation workflow

Recommended: use the browser-based annotation tool to label the existing dataset for the real-time safety models:

```powershell
python web_annotator_server.py
```

Then open:

```text
http://127.0.0.1:8765
```

or run `run_web_annotation_tool.bat`.

The older Tkinter tool is still available:

```powershell
python annotation_tool.py
```

or run `run_annotation_tool.bat`.

If browser playback is slow the first time a clip opens, prepare all browser-playable video copies up front:

```powershell
python prepare_web_media_cache.py
```

This writes cached H.264 copies under `.web_media_cache/` and leaves the original dataset unchanged.

The tool writes simple CSV/JSON annotations under `annotations/`:

- `videos.csv` for the indexed clips.
- `segments.csv` for attention and blouse state over time.
- `events.csv` for danger/no-danger events.
- `zones.json` for the fixed projected danger-volume polygon.

Validate saved annotations with:

```powershell
python validate_annotations.py
```

See `docs/architecture_and_annotation.md` and `docs/annotation_tool_usage.md` for the architecture and labeling rules.
