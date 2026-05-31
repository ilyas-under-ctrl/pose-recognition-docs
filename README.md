# Fixed-Camera Machine Safety Proof-of-Concept (POC)

This repository contains the fixed-camera pose recognition proof of concept designed to predict machine-safety risks. The system monitors operator safety by analyzing person keypoints, temporal danger-zone penetration, attention classification, blouse/clothing closure status, and a fused operational risk score.

---

## 📂 Repository Structure

The project files are organized to separate research scripts, backend modules, frontend dashboards, and datasets:

* **`backend/`**: Core application logic.
  * [`annotation_tool.py`](backend/annotation_tool.py): Legacy desktop Tkinter annotation app.
  * [`web_annotator_server.py`](backend/web_annotator_server.py): HTTP Server providing endpoints for the web UI.
  * [`validate_annotations.py`](backend/validate_annotations.py): Local schema and logical database validator.
  * [`prepare_web_media_cache.py`](backend/prepare_web_media_cache.py): FFmpeg transcoding script for browser video support.
  * [`requirements.txt`](backend/requirements.txt): Core application and server dependencies.
* **`dashboard/web_annotator/`**: Web application assets (HTML/CSS/JS) for the browser annotation interface.
* **`data/`**: Project dataset and local database storage.
  * `captures/`: Whitelisted MP4 video clips (including a sample video at `data/captures/ilyas/unsafe/unsafe blooza good  20260512_190928.mp4` for out-of-the-box execution).
  * `annotations/`: Local CSV/JSON databases (`videos.csv`, `segments.csv`, `events.csv`, `zones.json`).
  * `captures_manifest.csv`: Global master list of video files.
* **`jobs/`**: Pre-configured Windows batch script shortcuts (`run_web_annotation_tool.bat`, `run_annotation_tool.bat`, `prepare_web_media_cache.bat`).
* **`ml/` & `pipelines/` & Root Directory**: 39 Machine Learning scripts, sequence training pipelines, ensembling metrics, and Jupyter notebooks (`notebooks_experiences/`) kept at the root level to guarantee uninterrupted importing and reproducible execution.

---

## ⚡ Quick Start & Run Instructions

### 1. Install Application Dependencies
Install the required packages for the annotation tools and servers:
```powershell
python -m pip install -r backend/requirements.txt
```

### 2. Launch the Web Annotation Tool
Start the native-style web browser annotator:
```powershell
python backend/web_annotator_server.py
```
Then navigate to **[http://127.0.0.1:8765](http://127.0.0.1:8765)** in your web browser. 

Alternatively, you can double-click **`jobs/run_web_annotation_tool.bat`**.

### 3. Pre-prepare Browser Playback Cache
Browser-native players require H.264 video. If video seeking or playback is sluggish, transcode your video folder to a fast-seeking H.264 cache:
```powershell
python backend/prepare_web_media_cache.py
```
This saves optimized playable clips under `data/.web_media_cache/` without altering your raw video assets.

### 4. Validate Annotations
After modifying or adding annotations, run the verification tool to check database integrity, segment bounds, and polygon structures:
```powershell
python backend/validate_annotations.py
```

---

## 📱 Phone Live Feed Streamer
The repository includes a live mobile streamer prototype to view IP camera streams from a smartphone with live YOLO / MediaPipe skeleton overlay:
```powershell
python phone_feed_app.py
```
See the in-app instructions to connect your mobile hotspot, stream URL, and configure low-latency pose models.

---

## 📖 Project Documentation
Detailed technical specifications, modeling runbooks, and artifacts are located in the `docs/` folder:
* **[Architecture & Design Principles](docs/architecture_and_annotation.md)**: Claims, dataset design, and labeling logic.
* **[Annotation Tool Guidelines](docs/annotation_tool_usage.md)**: In-depth usage guide and hotkeys.
* **[ML Autonomous Training Runbook](docs/ml_autonomous_training_runbook.md)**: Training pipelines, model configurations, and target metrics.
* **[Deliverables & Downloads](docs/artifacts.md)**: Access to the compiled academic report (PDF) and stakeholders defense presentation (PPTX).
