import csv
import hashlib
import json
import re
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageDraw, ImageTk


APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
CAPTURE_DIR = DATA_DIR / "captures"
MANIFEST_PATH = DATA_DIR / "captures_manifest.csv"
ANNOTATION_DIR = DATA_DIR / "annotations"
VIDEOS_CSV = ANNOTATION_DIR / "videos.csv"
SEGMENTS_CSV = ANNOTATION_DIR / "segments.csv"
EVENTS_CSV = ANNOTATION_DIR / "events.csv"
ZONES_JSON = ANNOTATION_DIR / "zones.json"
DELETED_CLIPS_CSV = ANNOTATION_DIR / "deleted_clips.csv"

ZONE_ID = "machine_danger_volume"
CANVAS_MAX_W = 1080
CANVAS_MAX_H = 540
TARGET_REFRESH_HZ = 165
REFRESH_DELAY_MS = max(1, round(1000 / TARGET_REFRESH_HZ))
ZONE_HANDLE_RADIUS = 11

ATTENTION_LABELS = ("attentive", "distracted")
BLOUSE_LABELS = ("properly_worn", "badly_worn")
BODY_PARTS = (
    "hand_or_arm",
    "head",
    "right_wrist",
    "left_wrist",
    "right_elbow",
    "left_elbow",
    "right_arm",
    "left_arm",
    "none",
)
PRIMARY_BODY_PARTS = ("hand_or_arm", "head")
SPATIAL_RELATIONS = (
    "inside_volume",
    "near_volume",
    "outside_volume",
)
EVENT_ROLES = ("physical_entry", "risk_onset", "no_danger")
EVENT_TYPES = ("entered_danger_volume", "near_miss", "no_danger_event")
SHORTCUT_HELP = (
    "Playback: Space play/pause | Left/Right frame | Shift+Left/Right second | Home/End jump\n"
    "Review: F zone review at 8x | Auto-next follows the filtered queue | smooth loop targets 165 Hz\n"
    "Labels: A attentive | D distracted | R proper blouse | B bad blouse\n"
    "Danger sources: 1 hand/arm | 2 head | click/press multiple\n"
    "Save: S start segment | E end segment | W whole clip | M danger | G no danger\n"
    "Zone: Z edit | drag points | click empty area add | right-click point delete | Ctrl+S save"
)
PLAYBACK_SPEEDS = ("1x", "2x", "4x", "8x", "16x", "24x")

VIDEO_HEADERS = (
    "video_id",
    "path",
    "actor",
    "coarse_label",
    "fps",
    "frames",
    "duration_s",
    "width",
    "height",
)
SEGMENT_HEADERS = ("video_id", "start_s", "end_s", "attention", "blouse", "notes")
EVENT_HEADERS = (
    "video_id",
    "event_time_s",
    "frame",
    "event_role",
    "body_part",
    "event_type",
    "zone_id",
    "spatial_relation",
    "notes",
)


def read_csv(path, headers):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append({header: row.get(header, "") for header in headers})
        return rows


def write_csv(path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path, headers, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        if not exists:
            writer.writeheader()
        writer.writerow({header: row.get(header, "") for header in headers})


def parse_fps(value):
    if not value:
        return 30.0
    text = str(value).strip()
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        try:
            denominator_value = float(denominator)
            return float(numerator) / denominator_value if denominator_value else 30.0
        except ValueError:
            return 30.0
    try:
        return float(text)
    except ValueError:
        return 30.0


def stable_video_id(relative_path):
    normalized = str(relative_path).replace("\\", "/")
    stem = re.sub(r"[^A-Za-z0-9]+", "_", Path(normalized).with_suffix("").as_posix()).strip("_")
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:8]
    return f"{stem}_{digest}"


def media_probe(path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return 30.0, 0, 0.0, 0, 0
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    duration = frames / fps if fps else 0.0
    return fps, frames, duration, width, height


def discover_videos():
    videos = []
    seen_paths = set()

    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open("r", newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                actor = row.get("person", "")
                coarse_label = row.get("zone", "")
                name = row.get("name", "")
                path = CAPTURE_DIR / actor / coarse_label / name
                if not path.exists():
                    continue
                relative_path = path.relative_to(DATA_DIR)
                fps = parse_fps(row.get("fps", "30"))
                frames = int(float(row.get("frames") or 0))
                duration = float(row.get("duration_s") or 0.0)
                width, height = (row.get("resolution") or "0x0").lower().split("x", 1)
                videos.append(
                    {
                        "video_id": stable_video_id(relative_path),
                        "path": str(relative_path),
                        "actor": actor,
                        "coarse_label": coarse_label,
                        "fps": f"{fps:.3f}",
                        "frames": str(frames),
                        "duration_s": f"{duration:.3f}",
                        "width": width,
                        "height": height,
                    }
                )
                seen_paths.add(str(relative_path))

    for path in sorted(CAPTURE_DIR.rglob("*.mp4")):
        relative_path = path.relative_to(DATA_DIR)
        if str(relative_path) in seen_paths:
            continue
        parts = relative_path.parts
        actor = parts[1] if len(parts) > 1 else ""
        coarse_label = parts[2] if len(parts) > 2 else ""
        fps, frames, duration, width, height = media_probe(path)
        videos.append(
            {
                "video_id": stable_video_id(relative_path),
                "path": str(relative_path),
                "actor": actor,
                "coarse_label": coarse_label,
                "fps": f"{fps:.3f}",
                "frames": str(frames),
                "duration_s": f"{duration:.3f}",
                "width": str(width),
                "height": str(height),
            }
        )

    return sorted(videos, key=lambda item: (item["actor"], item["coarse_label"], item["path"]))


def ensure_video_index():
    ANNOTATION_DIR.mkdir(parents=True, exist_ok=True)
    deleted_ids = {row.get("video_id", "") for row in read_csv(DELETED_CLIPS_CSV, VIDEO_HEADERS)}
    existing = [row for row in read_csv(VIDEOS_CSV, VIDEO_HEADERS) if row.get("video_id") not in deleted_ids]
    existing_by_id = {row["video_id"]: row for row in existing}
    changed = False

    for video in discover_videos():
        if video["video_id"] in deleted_ids:
            continue
        if video["video_id"] not in existing_by_id:
            existing.append(video)
            existing_by_id[video["video_id"]] = video
            changed = True

    if changed or not VIDEOS_CSV.exists() or len(existing_by_id) != len(read_csv(VIDEOS_CSV, VIDEO_HEADERS)):
        write_csv(VIDEOS_CSV, VIDEO_HEADERS, existing)
    if not SEGMENTS_CSV.exists():
        write_csv(SEGMENTS_CSV, SEGMENT_HEADERS, [])
    if not EVENTS_CSV.exists():
        write_csv(EVENTS_CSV, EVENT_HEADERS, [])

    return existing


def default_zone(width=1440, height=720):
    return {
        "zone_id": ZONE_ID,
        "shape": "projected_volume_polygon",
        "image_width": width,
        "image_height": height,
        "points": [],
        "active_body_parts": [
            "hand_or_arm",
            "right_wrist",
            "left_wrist",
            "right_elbow",
            "left_elbow",
            "head",
            "torso",
        ],
        "notes": (
            "Single fixed-camera projection of the machine danger volume. "
            "Use body part, motion, and z/pseudo-depth features downstream; "
            "do not treat this polygon as true metric 3D."
        ),
    }


class AnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Machine Safety Dataset Annotation Tool")
        self.root.minsize(1180, 780)
        self.configure_style()
        self.videos = ensure_video_index()
        self.filtered_indices = list(range(len(self.videos)))
        self.current_index = 0
        self.cap = None
        self.current_frame = 0
        self.frame_count = 0
        self.fps = 30.0
        self.duration = 0.0
        self.playback_position_frame = 0.0
        self.video_width = 1440
        self.video_height = 720
        self.display_width = 960
        self.display_height = 480
        self.playing = False
        self.slider_busy = False
        self.updating_video_list = False
        self.zone_draw_mode = False
        self.dragging_zone_point = None
        self.selected_zone_point = None
        self.timeline_markers = []
        self.dragging_event_index = None
        self.dragging_event_time = None
        self.segment_start = None
        self.last_tick = time.monotonic()

        self.photo = None
        self.zone = self.load_zone()

        self.attention_var = tk.StringVar(value="attentive")
        self.blouse_var = tk.StringVar(value="properly_worn")
        self.body_part_var = tk.StringVar(value="hand_or_arm")
        self.body_part_vars = {label: tk.BooleanVar(value=label == "hand_or_arm") for label in PRIMARY_BODY_PARTS}
        self.spatial_var = tk.StringVar(value="inside_volume")
        self.event_type_var = tk.StringVar(value="entered_danger_volume")
        self.notes_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="all")
        self.speed_var = tk.StringVar(value="1x")
        self.auto_next_var = tk.BooleanVar(value=False)
        self.video_info_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")
        self.segment_start_var = tk.StringVar(value="Segment start: none")
        self.progress_var = tk.StringVar(value="")
        self.review_status_var = tk.StringVar(value="")

        self.build_ui()
        self.bind_shortcuts()

        if self.videos:
            self.load_video(0)
        else:
            messagebox.showwarning("No videos", f"No .mp4 files found under {CAPTURE_DIR}")

    def configure_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#f5f6f8")
        style.configure("TLabel", background="#f5f6f8", foreground="#172033")
        style.configure("Header.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Meta.TLabel", foreground="#5e6878")
        style.configure("Status.TLabel", foreground="#172033")
        style.configure("TButton", padding=(10, 5))
        style.configure("Primary.TButton", padding=(12, 6))
        style.configure("Danger.TButton", padding=(12, 6), foreground="#8a1f17")
        style.configure("Panel.TLabelframe", background="#f5f6f8")
        style.configure("Panel.TLabelframe.Label", background="#f5f6f8", foreground="#172033", font=("Segoe UI", 10, "bold"))

    def build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        left.rowconfigure(4, weight=1)

        ttk.Label(left, text="Annotation Queue", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(left, textvariable=self.progress_var, style="Meta.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 8))

        filters = ttk.Frame(left)
        filters.grid(row=2, column=0, sticky="ew")
        filters.columnconfigure(0, weight=1)
        ttk.Entry(filters, textvariable=self.search_var).grid(row=0, column=0, sticky="ew")
        ttk.Combobox(
            filters,
            textvariable=self.filter_var,
            values=("all", "safe", "unsafe", "needs_review", "reviewed"),
            state="readonly",
            width=13,
        ).grid(row=0, column=1, sticky="e", padx=(6, 0))
        self.search_var.trace_add("write", lambda *_args: self.populate_video_list())
        self.filter_var.trace_add("write", lambda *_args: self.populate_video_list())

        ttk.Label(
            left,
            text="Legend: ✓ reviewed, E event only, S segment only, ○ untouched",
            style="Meta.TLabel",
        ).grid(row=3, column=0, sticky="w", pady=(6, 3))

        self.video_list = tk.Listbox(
            left,
            width=54,
            height=26,
            exportselection=False,
            borderwidth=0,
            highlightthickness=1,
            activestyle="dotbox",
        )
        self.video_list.grid(row=4, column=0, sticky="nsew")
        self.video_list.bind("<<ListboxSelect>>", self.on_video_selected)

        self.populate_video_list(select_current=False)

        nav = ttk.Frame(left)
        nav.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(nav, text="P  Prev", command=lambda: self.change_video(-1)).grid(row=0, column=0, sticky="ew")
        ttk.Button(nav, text="N  Next", command=lambda: self.change_video(1)).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        nav.columnconfigure((0, 1), weight=1)

        shortcut_panel = ttk.LabelFrame(left, text="Shortcuts", style="Panel.TLabelframe")
        shortcut_panel.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(
            shortcut_panel,
            text=SHORTCUT_HELP,
            justify="left",
            style="Meta.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=8, pady=8)

        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        header = ttk.Frame(right)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Frame Workspace", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.review_status_var, style="Meta.TLabel").grid(row=0, column=1, sticky="e")

        self.canvas = tk.Canvas(right, width=self.display_width, height=self.display_height, bg="#111111", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)

        self.slider = ttk.Scale(right, from_=0, to=1, orient="horizontal", command=self.on_slider)
        self.slider.grid(row=2, column=0, sticky="ew", pady=(6, 4))

        self.timeline = tk.Canvas(
            right,
            width=self.display_width,
            height=86,
            bg="#f5f6f8",
            highlightthickness=1,
            highlightbackground="#d9e0e7",
        )
        self.timeline.grid(row=3, column=0, sticky="ew", pady=(2, 6))
        self.timeline.bind("<ButtonPress-1>", self.on_timeline_press)
        self.timeline.bind("<B1-Motion>", self.on_timeline_drag)
        self.timeline.bind("<ButtonRelease-1>", self.on_timeline_release)

        transport = ttk.Frame(right)
        transport.grid(row=4, column=0, sticky="ew")
        ttk.Button(transport, text="Space  Play/Pause", command=self.toggle_play).grid(row=0, column=0)
        ttk.Button(transport, text="<  Frame", command=lambda: self.step_frames(-1)).grid(row=0, column=1, padx=(6, 0))
        ttk.Button(transport, text="Frame  >", command=lambda: self.step_frames(1)).grid(row=0, column=2, padx=(6, 0))
        ttk.Button(transport, text="-1 sec", command=lambda: self.jump_seconds(-1)).grid(row=0, column=3, padx=(6, 0))
        ttk.Button(transport, text="+1 sec", command=lambda: self.jump_seconds(1)).grid(row=0, column=4, padx=(6, 0))
        ttk.Label(transport, text="Speed").grid(row=0, column=5, sticky="e", padx=(12, 4))
        ttk.Combobox(
            transport,
            textvariable=self.speed_var,
            values=PLAYBACK_SPEEDS,
            state="readonly",
            width=6,
        ).grid(row=0, column=6, sticky="w")
        ttk.Checkbutton(transport, text="Auto-next", variable=self.auto_next_var).grid(row=0, column=7, padx=(8, 0))
        ttk.Button(transport, text="F  Zone Review 8x", command=self.start_zone_review).grid(row=0, column=8, padx=(8, 0))
        ttk.Label(transport, textvariable=self.video_info_var).grid(row=0, column=9, sticky="w", padx=(12, 0))
        transport.columnconfigure(9, weight=1)

        forms = ttk.Frame(right)
        forms.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        forms.columnconfigure(0, weight=1)
        forms.columnconfigure(1, weight=1)
        forms.columnconfigure(2, weight=1)

        label_panel = ttk.LabelFrame(forms, text="Clip Labels", style="Panel.TLabelframe")
        label_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.add_choice_buttons(
            label_panel,
            "Attention",
            self.attention_var,
            (("A", "attentive"), ("D", "distracted"), ("U", "unknown")),
            0,
        )
        self.add_choice_buttons(
            label_panel,
            "Blouse",
            self.blouse_var,
            (("R", "properly_worn"), ("B", "badly_worn"), ("", "unknown")),
            1,
        )

        event_panel = ttk.LabelFrame(forms, text="Danger Event", style="Panel.TLabelframe")
        event_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 8))
        self.add_multi_body_source(event_panel)
        ttk.Label(event_panel, text="Spatial").grid(row=1, column=0, sticky="w", padx=8, pady=(8, 0))
        ttk.Combobox(event_panel, textvariable=self.spatial_var, values=SPATIAL_RELATIONS, state="readonly", width=18).grid(
            row=1, column=1, sticky="ew", padx=8, pady=(8, 0)
        )
        ttk.Label(event_panel, text="Event").grid(row=2, column=0, sticky="w", padx=8, pady=(8, 8))
        ttk.Combobox(event_panel, textvariable=self.event_type_var, values=EVENT_TYPES, state="readonly", width=18).grid(
            row=2, column=1, sticky="ew", padx=8, pady=(8, 8)
        )
        event_panel.columnconfigure(1, weight=1)

        notes_panel = ttk.LabelFrame(forms, text="Notes", style="Panel.TLabelframe")
        notes_panel.grid(row=0, column=2, sticky="nsew")
        ttk.Entry(notes_panel, textvariable=self.notes_var).grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        ttk.Label(
            notes_panel,
            text="Use notes only for ambiguity: occlusion, above projection, unclear body part.",
            style="Meta.TLabel",
            wraplength=260,
        ).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        notes_panel.columnconfigure(0, weight=1)

        actions = ttk.Frame(right)
        actions.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(actions, text="S  Start Segment", command=self.start_segment).grid(row=0, column=0)
        ttk.Button(actions, text="E  End + Save", command=self.end_segment).grid(row=0, column=1, padx=(6, 0))
        ttk.Button(actions, text="W  Whole Clip", command=self.save_whole_clip_segment).grid(row=0, column=2, padx=(6, 0))
        ttk.Button(actions, text="M  Mark Danger", style="Danger.TButton", command=self.save_event).grid(row=0, column=3, padx=(12, 0))
        ttk.Button(actions, text="G  No Danger", style="Primary.TButton", command=self.save_no_danger).grid(row=0, column=4, padx=(6, 0))
        ttk.Button(actions, text="Undo Event", command=lambda: self.undo_last(EVENTS_CSV, EVENT_HEADERS)).grid(
            row=0, column=5, padx=(12, 0)
        )
        ttk.Button(actions, text="Undo Segment", command=lambda: self.undo_last(SEGMENTS_CSV, SEGMENT_HEADERS)).grid(
            row=0, column=6, padx=(6, 0)
        )

        zone_actions = ttk.Frame(right)
        zone_actions.grid(row=7, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(zone_actions, text="Z  Edit Zone", command=self.toggle_zone_draw).grid(row=0, column=0)
        ttk.Button(zone_actions, text="Undo Last Point", command=self.undo_zone_point).grid(row=0, column=1, padx=(6, 0))
        ttk.Button(zone_actions, text="Clear Zone", command=self.clear_zone).grid(row=0, column=2, padx=(6, 0))
        ttk.Button(zone_actions, text="Ctrl+S  Save Zone", command=self.save_zone).grid(row=0, column=3, padx=(6, 0))
        ttk.Label(zone_actions, textvariable=self.segment_start_var).grid(row=0, column=4, sticky="w", padx=(12, 0))

        ttk.Label(right, text="Saved annotations for this video").grid(row=8, column=0, sticky="w", pady=(8, 0))
        self.summary = tk.Text(right, height=9, wrap="word")
        self.summary.grid(row=9, column=0, sticky="ew")
        self.summary.configure(state="disabled")

        ttk.Label(right, textvariable=self.status_var, style="Status.TLabel").grid(row=10, column=0, sticky="ew", pady=(6, 0))

    def add_choice_buttons(self, parent, label, variable, choices, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=(8, 0))
        button_row = ttk.Frame(parent)
        button_row.grid(row=row, column=1, sticky="ew", padx=8, pady=(8, 0))
        for column, (shortcut, value) in enumerate(choices):
            text = f"{shortcut}  {value}" if shortcut else value
            ttk.Button(
                button_row,
                text=text,
                command=lambda target=value, var=variable: self.set_choice(var, target),
            ).grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 4, 0))
            button_row.columnconfigure(column, weight=1)
        parent.columnconfigure(1, weight=1)

    def set_choice(self, variable, value):
        variable.set(value)
        self.set_status(f"Selected {value}")

    def add_multi_body_source(self, parent):
        ttk.Label(parent, text="Danger sources").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 0))
        source_row = ttk.Frame(parent)
        source_row.grid(row=0, column=1, sticky="ew", padx=8, pady=(8, 0))
        choices = (("1", "hand_or_arm"), ("2", "head"), ("3", "torso"), ("4", "unknown"))
        for column, (shortcut, label) in enumerate(choices):
            ttk.Checkbutton(
                source_row,
                text=f"{shortcut}  {label}",
                variable=self.body_part_vars[label],
                command=self.sync_body_part_var,
            ).grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 4, 0))
            source_row.columnconfigure(column, weight=1)
        parent.columnconfigure(1, weight=1)

    def selected_body_parts(self):
        selected = [label for label in PRIMARY_BODY_PARTS if self.body_part_vars[label].get()]
        if not selected:
            return ["hand_or_arm"]
        return selected

    def body_part_value(self):
        return "|".join(self.selected_body_parts())

    def sync_body_part_var(self):
        value = self.body_part_value()
        self.body_part_var.set(value)
        self.set_status(f"Danger source set to {value}")

    def toggle_body_part(self, label):
        if label not in self.body_part_vars:
            return
        self.body_part_vars[label].set(not self.body_part_vars[label].get())
        self.sync_body_part_var()

    def bind_shortcuts(self):
        self.root.bind("<space>", lambda event: self.shortcut(event, self.toggle_play))
        self.root.bind("<Left>", lambda event: self.shortcut(event, lambda: self.step_frames(-1)))
        self.root.bind("<Right>", lambda event: self.shortcut(event, lambda: self.step_frames(1)))
        self.root.bind("<Shift-Left>", lambda event: self.shortcut(event, lambda: self.jump_seconds(-1)))
        self.root.bind("<Shift-Right>", lambda event: self.shortcut(event, lambda: self.jump_seconds(1)))
        self.root.bind("<Home>", lambda event: self.shortcut(event, lambda: self.show_frame(0)))
        self.root.bind("<End>", lambda event: self.shortcut(event, lambda: self.show_frame(self.frame_count - 1)))
        self.root.bind("s", lambda event: self.shortcut(event, self.start_segment))
        self.root.bind("e", lambda event: self.shortcut(event, self.end_segment))
        self.root.bind("w", lambda event: self.shortcut(event, self.save_whole_clip_segment))
        self.root.bind("m", lambda event: self.shortcut(event, self.save_event))
        self.root.bind("g", lambda event: self.shortcut(event, self.save_no_danger))
        self.root.bind("n", lambda event: self.shortcut(event, lambda: self.change_video(1)))
        self.root.bind("p", lambda event: self.shortcut(event, lambda: self.change_video(-1)))
        self.root.bind("f", lambda event: self.shortcut(event, self.start_zone_review))
        self.root.bind("z", lambda event: self.shortcut(event, self.toggle_zone_draw))
        self.root.bind("<Control-s>", lambda event: self.shortcut(event, self.save_zone))
        self.root.bind("<Control-z>", lambda event: self.shortcut(event, lambda: self.undo_last(EVENTS_CSV, EVENT_HEADERS)))
        self.root.bind("<Control-Shift-Z>", lambda event: self.shortcut(event, lambda: self.undo_last(SEGMENTS_CSV, SEGMENT_HEADERS)))
        self.root.bind("a", lambda event: self.shortcut(event, lambda: self.set_choice(self.attention_var, "attentive")))
        self.root.bind("d", lambda event: self.shortcut(event, lambda: self.set_choice(self.attention_var, "distracted")))
        self.root.bind("r", lambda event: self.shortcut(event, lambda: self.set_choice(self.blouse_var, "properly_worn")))
        self.root.bind("b", lambda event: self.shortcut(event, lambda: self.set_choice(self.blouse_var, "badly_worn")))
        self.root.bind("1", lambda event: self.shortcut(event, lambda: self.toggle_body_part("hand_or_arm")))
        self.root.bind("2", lambda event: self.shortcut(event, lambda: self.toggle_body_part("head")))

    def shortcut(self, event, action):
        if isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Text)):
            return
        action()
        return "break"

    def load_zone(self):
        if not ZONES_JSON.exists():
            return default_zone()
        try:
            data = json.loads(ZONES_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default_zone()
        if isinstance(data, dict) and "zones" in data and data["zones"]:
            return data["zones"][0]
        if isinstance(data, dict) and "points" in data:
            return data
        return default_zone()

    def save_zone(self):
        self.zone["image_width"] = self.video_width
        self.zone["image_height"] = self.video_height
        ZONES_JSON.write_text(json.dumps({"zones": [self.zone]}, indent=2), encoding="utf-8")
        self.zone_draw_mode = False
        self.dragging_zone_point = None
        self.selected_zone_point = None
        self.set_status(f"Saved zone with {len(self.zone.get('points', []))} points to {ZONES_JSON}")
        self.show_frame(self.current_frame)

    def toggle_zone_draw(self):
        self.zone_draw_mode = not self.zone_draw_mode
        mode = "on" if self.zone_draw_mode else "off"
        if self.zone_draw_mode:
            self.playing = False
            self.set_status(
                "Zone edit is on. Drag yellow points to adjust, click empty area to add, right-click a point to delete."
            )
        else:
            self.dragging_zone_point = None
            self.selected_zone_point = None
            self.set_status("Zone edit is off.")
        self.show_frame(self.current_frame)

    def undo_zone_point(self):
        points = self.zone.setdefault("points", [])
        if points:
            points.pop()
        self.dragging_zone_point = None
        self.selected_zone_point = None
        self.show_frame(self.current_frame)

    def clear_zone(self):
        if messagebox.askyesno("Clear zone", "Clear the current projected danger-volume polygon?"):
            self.zone["points"] = []
            self.dragging_zone_point = None
            self.selected_zone_point = None
            self.show_frame(self.current_frame)

    def current_video(self):
        if not self.videos:
            return None
        return self.videos[self.current_index]

    def current_time_s(self):
        return self.current_frame / self.fps if self.fps else 0.0

    def annotation_sets(self):
        segments = read_csv(SEGMENTS_CSV, SEGMENT_HEADERS)
        events = read_csv(EVENTS_CSV, EVENT_HEADERS)
        segment_ids = {row["video_id"] for row in segments if row.get("video_id")}
        event_ids = {row["video_id"] for row in events if row.get("video_id")}
        return segment_ids, event_ids

    def review_marker(self, video_id, segment_ids=None, event_ids=None):
        if segment_ids is None or event_ids is None:
            segment_ids, event_ids = self.annotation_sets()
        has_segment = video_id in segment_ids
        has_event = video_id in event_ids
        if has_segment and has_event:
            return "✓"
        if has_event:
            return "E"
        if has_segment:
            return "S"
        return "○"

    def video_matches_filter(self, video, marker, search, filter_value):
        searchable = f"{video['actor']} {video['coarse_label']} {video['path']}".lower()
        if search and search not in searchable:
            return False
        if filter_value in ("safe", "unsafe") and video["coarse_label"] != filter_value:
            return False
        if filter_value == "needs_review" and marker == "✓":
            return False
        if filter_value == "reviewed" and marker != "✓":
            return False
        return True

    def populate_video_list(self, select_current=True):
        if not hasattr(self, "video_list"):
            return
        segment_ids, event_ids = self.annotation_sets()
        search = self.search_var.get().strip().lower()
        filter_value = self.filter_var.get()
        self.filtered_indices = []
        self.updating_video_list = True
        self.video_list.delete(0, tk.END)
        for idx, video in enumerate(self.videos):
            marker = self.review_marker(video["video_id"], segment_ids, event_ids)
            if not self.video_matches_filter(video, marker, search, filter_value):
                continue
            self.filtered_indices.append(idx)
            duration = float(video.get("duration_s") or 0.0)
            label = (
                f"{marker} {video['actor']}/{video['coarse_label']} "
                f"{duration:05.1f}s  {Path(video['path']).name}"
            )
            self.video_list.insert(tk.END, label)
            list_idx = self.video_list.size() - 1
            if video["coarse_label"] == "unsafe":
                self.video_list.itemconfig(list_idx, foreground="#8a1f17")
            elif video["coarse_label"] == "safe":
                self.video_list.itemconfig(list_idx, foreground="#145a3c")

        if select_current and self.current_index in self.filtered_indices:
            list_index = self.filtered_indices.index(self.current_index)
            self.video_list.selection_set(list_index)
            self.video_list.see(list_index)
        self.updating_video_list = False
        self.refresh_progress(segment_ids, event_ids)

    def refresh_progress(self, segment_ids=None, event_ids=None):
        if segment_ids is None or event_ids is None:
            segment_ids, event_ids = self.annotation_sets()
        reviewed = sum(
            1 for video in self.videos if video["video_id"] in segment_ids and video["video_id"] in event_ids
        )
        self.progress_var.set(f"{reviewed}/{len(self.videos)} videos fully reviewed")

    def update_review_status(self):
        video = self.current_video()
        if not video:
            self.review_status_var.set("")
            return
        marker = self.review_marker(video["video_id"])
        status = {
            "✓": "Reviewed: segment + event saved",
            "E": "Partial: event saved, segment missing",
            "S": "Partial: segment saved, event missing",
            "○": "Needs review",
        }[marker]
        self.review_status_var.set(status)

    def load_video(self, index):
        if not (0 <= index < len(self.videos)):
            return
        self.playing = False
        self.current_index = index
        video = self.current_video()
        path = APP_DIR / video["path"]

        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            messagebox.showerror("Open failed", f"Could not open video:\n{path}")
            return

        self.fps = float(self.cap.get(cv2.CAP_PROP_FPS) or parse_fps(video["fps"]))
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or int(video["frames"] or 0))
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or int(float(video["width"] or 1440)))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or int(float(video["height"] or 720)))
        self.duration = self.frame_count / self.fps if self.fps else 0.0
        self.current_frame = 0
        self.playback_position_frame = 0.0
        self.segment_start = None
        self.segment_start_var.set("Segment start: none")

        self.display_width, self.display_height = self.fit_dimensions(self.video_width, self.video_height)
        self.canvas.configure(width=self.display_width, height=self.display_height)
        self.timeline.configure(width=self.display_width)
        self.slider.configure(to=max(1, self.frame_count - 1))

        self.video_list.selection_clear(0, tk.END)
        if index in self.filtered_indices:
            list_index = self.filtered_indices.index(index)
            self.video_list.selection_set(list_index)
            self.video_list.see(list_index)

        self.refresh_summary()
        self.show_frame(0)
        self.set_status(f"Loaded {video['path']}")

    def fit_dimensions(self, width, height):
        scale = min(CANVAS_MAX_W / max(1, width), CANVAS_MAX_H / max(1, height), 1.0)
        return max(1, int(width * scale)), max(1, int(height * scale))

    def on_video_selected(self, _event=None):
        if self.updating_video_list:
            return
        selection = self.video_list.curselection()
        if selection and selection[0] < len(self.filtered_indices):
            self.load_video(self.filtered_indices[selection[0]])

    def change_video(self, delta):
        if not self.videos:
            return
        queue = self.filtered_indices or list(range(len(self.videos)))
        if self.current_index in queue:
            queue_pos = queue.index(self.current_index)
        else:
            queue_pos = 0
        new_pos = min(max(0, queue_pos + delta), len(queue) - 1)
        new_index = queue[new_pos]
        if new_index != self.current_index:
            self.load_video(new_index)
            return True
        return False

    def on_slider(self, value):
        if self.slider_busy or self.cap is None:
            return
        try:
            frame = int(float(value))
        except ValueError:
            return
        if abs(frame - self.current_frame) > 1:
            self.playing = False
            self.show_frame(frame)

    def show_frame(self, frame_index, sync_position=True):
        if self.cap is None:
            return
        frame_index = max(0, min(int(frame_index), max(0, self.frame_count - 1)))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = self.cap.read()
        if not ok:
            self.playing = False
            return

        self.current_frame = frame_index
        if sync_position:
            self.playback_position_frame = float(frame_index)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb).resize((self.display_width, self.display_height), Image.Resampling.BILINEAR)
        self.draw_overlay(image)
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        self.slider_busy = True
        self.slider.set(frame_index)
        self.slider_busy = False

        video = self.current_video()
        time_s = self.current_time_s()
        self.video_info_var.set(
            f"{self.current_index + 1}/{len(self.videos)} | {video['coarse_label']} | "
            f"frame {self.current_frame}/{max(0, self.frame_count - 1)} | {time_s:.2f}s/{self.duration:.2f}s"
        )
        self.draw_timeline()

    def timeline_width(self):
        if not hasattr(self, "timeline"):
            return self.display_width
        width = self.timeline.winfo_width()
        return max(360, width if width > 1 else self.display_width)

    def timeline_bounds(self):
        width = self.timeline_width()
        return 64, width - 16

    def time_to_timeline_x(self, time_s):
        left, right = self.timeline_bounds()
        if self.duration <= 0:
            return left
        ratio = max(0.0, min(1.0, time_s / self.duration))
        return left + ratio * (right - left)

    def timeline_x_to_time(self, x):
        left, right = self.timeline_bounds()
        if right <= left or self.duration <= 0:
            return 0.0
        ratio = max(0.0, min(1.0, (x - left) / (right - left)))
        return ratio * self.duration

    def current_annotation_rows(self):
        video = self.current_video()
        if not video:
            return [], []
        video_id = video["video_id"]
        segments = [row for row in read_csv(SEGMENTS_CSV, SEGMENT_HEADERS) if row["video_id"] == video_id]
        event_rows = read_csv(EVENTS_CSV, EVENT_HEADERS)
        events = [(idx, row) for idx, row in enumerate(event_rows) if row["video_id"] == video_id]
        return segments, events

    def draw_timeline(self):
        if not hasattr(self, "timeline"):
            return
        width = self.timeline_width()
        height = 86
        left, right = self.timeline_bounds()
        self.timeline.delete("all")
        self.timeline_markers = []

        self.timeline.create_rectangle(0, 0, width, height, fill="#f5f6f8", outline="")
        self.timeline.create_text(10, 17, text="Events", anchor="w", fill="#5e6878")
        self.timeline.create_text(10, 52, text="Segments", anchor="w", fill="#5e6878")
        self.timeline.create_line(left, 24, right, 24, fill="#b9c3cf")
        self.timeline.create_line(left, 58, right, 58, fill="#d4dbe3")

        for tick in range(5):
            ratio = tick / 4
            x = left + ratio * (right - left)
            time_s = ratio * self.duration
            self.timeline.create_line(x, 20, x, 64, fill="#e1e6ec")
            self.timeline.create_text(x, 75, text=f"{time_s:.1f}s", fill="#768191", font=("Segoe UI", 8))

        segments, events = self.current_annotation_rows()
        if not segments:
            self.timeline.create_text(left + 4, 52, text="no segment labels yet", anchor="w", fill="#9aa4b2")
        for segment in segments:
            start = float(segment.get("start_s") or 0.0)
            end = float(segment.get("end_s") or start)
            x1 = self.time_to_timeline_x(start)
            x2 = max(x1 + 2, self.time_to_timeline_x(end))
            attention = segment.get("attention", "")
            blouse = segment.get("blouse", "")
            if attention == "distracted":
                fill_color = "#f3b64a"
            elif blouse == "badly_worn":
                fill_color = "#4aa3b5"
            else:
                fill_color = "#4aa66a"
            self.timeline.create_rectangle(x1, 46, x2, 66, fill=fill_color, outline="")
            label = f"{attention}/{blouse}"
            if x2 - x1 > 95:
                self.timeline.create_text(x1 + 5, 56, text=label, anchor="w", fill="#ffffff", font=("Segoe UI", 8))

        for global_index, event in events:
            event_type = event.get("event_type", "")
            if event_type == "no_danger_event" or not event.get("event_time_s"):
                self.timeline.create_text(right - 4, 24, text="no danger marked", anchor="e", fill="#4aa66a")
                continue
            event_time = float(event.get("event_time_s") or 0.0)
            if self.dragging_event_index == global_index and self.dragging_event_time is not None:
                event_time = self.dragging_event_time
            x = self.time_to_timeline_x(event_time)
            marker_fill = "#d63f3a"
            if self.dragging_event_index == global_index:
                marker_fill = "#ffffff"
            self.timeline.create_polygon(x, 10, x - 7, 22, x + 7, 22, fill=marker_fill, outline="#8a1f17")
            self.timeline.create_line(x, 22, x, 69, fill="#d63f3a", width=2)
            self.timeline.create_text(
                x + 8,
                13,
                text=event.get("body_part", "event"),
                anchor="w",
                fill="#8a1f17",
                font=("Segoe UI", 8),
            )
            self.timeline_markers.append({"index": global_index, "x": x, "event": event})

        playhead_x = self.time_to_timeline_x(self.current_time_s())
        self.timeline.create_line(playhead_x, 5, playhead_x, height - 8, fill="#1864ff", width=2)
        self.timeline.create_polygon(playhead_x, 4, playhead_x - 5, 12, playhead_x + 5, 12, fill="#1864ff")

    def nearest_timeline_marker(self, x, y):
        if y > 40:
            return None
        best = None
        best_distance = 10
        for marker in self.timeline_markers:
            distance = abs(marker["x"] - x)
            if distance <= best_distance:
                best = marker
                best_distance = distance
        return best

    def jump_to_time(self, time_s):
        frame = int(round(time_s * self.fps))
        self.playing = False
        self.show_frame(frame)

    def on_timeline_press(self, event):
        marker = self.nearest_timeline_marker(event.x, event.y)
        if marker is not None:
            self.dragging_event_index = marker["index"]
            self.dragging_event_time = self.timeline_x_to_time(event.x)
            self.jump_to_time(self.dragging_event_time)
            self.set_status("Dragging danger event marker. Release to save the new timestamp.")
            return
        self.dragging_event_index = None
        self.dragging_event_time = None
        self.jump_to_time(self.timeline_x_to_time(event.x))

    def on_timeline_drag(self, event):
        if self.dragging_event_index is None:
            return
        self.dragging_event_time = self.timeline_x_to_time(event.x)
        self.jump_to_time(self.dragging_event_time)
        self.draw_timeline()

    def on_timeline_release(self, event):
        if self.dragging_event_index is None:
            return
        new_time = self.timeline_x_to_time(event.x)
        self.update_event_timestamp(self.dragging_event_index, new_time)
        self.jump_to_time(new_time)
        self.dragging_event_index = None
        self.dragging_event_time = None
        self.refresh_summary()
        self.set_status(f"Moved danger event marker to {new_time:.3f}s.")

    def update_event_timestamp(self, event_index, time_s):
        rows = read_csv(EVENTS_CSV, EVENT_HEADERS)
        if not (0 <= event_index < len(rows)):
            return
        time_s = max(0.0, min(float(time_s), self.duration))
        frame = max(0, min(int(round(time_s * self.fps)), max(0, self.frame_count - 1)))
        rows[event_index]["event_time_s"] = f"{time_s:.3f}"
        rows[event_index]["frame"] = str(frame)
        write_csv(EVENTS_CSV, EVENT_HEADERS, rows)

    def draw_overlay(self, image):
        draw = ImageDraw.Draw(image, "RGBA")
        sx = self.display_width / max(1, self.video_width)
        sy = self.display_height / max(1, self.video_height)
        points = self.zone.get("points", [])
        scaled = [(int(point[0] * sx), int(point[1] * sy)) for point in points]
        if len(scaled) >= 3:
            draw.polygon(scaled, fill=(255, 185, 0, 45), outline=(255, 185, 0, 230))
        if len(scaled) >= 2:
            draw.line(scaled + ([scaled[0]] if len(scaled) >= 3 else []), fill=(255, 185, 0, 230), width=3)
        for idx, point in enumerate(scaled, start=1):
            x, y = point
            point_index = idx - 1
            radius = 8 if point_index == self.selected_zone_point else 5
            fill_color = (255, 255, 255, 255) if point_index == self.selected_zone_point else (255, 185, 0, 255)
            outline_color = (255, 185, 0, 255) if point_index == self.selected_zone_point else (0, 0, 0, 120)
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=fill_color,
                outline=outline_color,
                width=2,
            )
            draw.text((x + 7, y - 8), str(idx), fill=(255, 255, 255, 255))

        if self.zone_draw_mode:
            draw.rectangle((8, 8, 590, 38), fill=(0, 0, 0, 170))
            draw.text(
                (16, 17),
                "EDIT ZONE: drag points | click empty area add | right-click point delete | Ctrl+S save",
                fill=(255, 255, 255, 255),
            )
        elif not points:
            draw.rectangle((8, 8, 360, 38), fill=(0, 0, 0, 150))
            draw.text((16, 17), "No danger volume yet: press Z, draw points, Ctrl+S", fill=(255, 255, 255, 255))

        video = self.current_video()
        if video:
            footer = (
                f"{video['coarse_label'].upper()} | {self.current_time_s():.2f}s | "
                f"attention={self.attention_var.get()} | blouse={self.blouse_var.get()} | "
                f"sources={self.body_part_value()}"
            )
            y0 = self.display_height - 34
            draw.rectangle((0, y0, self.display_width, self.display_height), fill=(0, 0, 0, 150))
            draw.text((12, y0 + 10), footer, fill=(255, 255, 255, 255))

    def canvas_to_video(self, x, y):
        video_x = int(x * self.video_width / max(1, self.display_width))
        video_y = int(y * self.video_height / max(1, self.display_height))
        return [
            max(0, min(self.video_width - 1, video_x)),
            max(0, min(self.video_height - 1, video_y)),
        ]

    def zone_points_display(self):
        sx = self.display_width / max(1, self.video_width)
        sy = self.display_height / max(1, self.video_height)
        return [(point[0] * sx, point[1] * sy) for point in self.zone.get("points", [])]

    def nearest_zone_point(self, x, y):
        nearest_index = None
        nearest_distance_sq = ZONE_HANDLE_RADIUS * ZONE_HANDLE_RADIUS
        for idx, (point_x, point_y) in enumerate(self.zone_points_display()):
            distance_sq = (point_x - x) ** 2 + (point_y - y) ** 2
            if distance_sq <= nearest_distance_sq:
                nearest_index = idx
                nearest_distance_sq = distance_sq
        return nearest_index

    def set_zone_point_from_canvas(self, index, x, y):
        points = self.zone.setdefault("points", [])
        if not (0 <= index < len(points)):
            return
        points[index] = self.canvas_to_video(x, y)

    def on_canvas_press(self, event):
        if not self.zone_draw_mode:
            return
        nearest = self.nearest_zone_point(event.x, event.y)
        if nearest is None:
            points = self.zone.setdefault("points", [])
            points.append(self.canvas_to_video(event.x, event.y))
            nearest = len(points) - 1
        self.dragging_zone_point = nearest
        self.selected_zone_point = nearest
        self.show_frame(self.current_frame)

    def on_canvas_drag(self, event):
        if not self.zone_draw_mode or self.dragging_zone_point is None:
            return
        self.set_zone_point_from_canvas(self.dragging_zone_point, event.x, event.y)
        self.selected_zone_point = self.dragging_zone_point
        self.show_frame(self.current_frame)

    def on_canvas_release(self, _event):
        if not self.zone_draw_mode:
            return
        self.dragging_zone_point = None
        self.show_frame(self.current_frame)

    def on_canvas_right_click(self, event):
        if not self.zone_draw_mode:
            return
        nearest = self.nearest_zone_point(event.x, event.y)
        if nearest is None:
            self.set_status("Right-click a yellow zone point to delete it.")
            return
        points = self.zone.setdefault("points", [])
        removed = points.pop(nearest)
        self.dragging_zone_point = None
        self.selected_zone_point = None
        self.set_status(f"Deleted zone point {nearest + 1}: {removed}. Press Ctrl+S to save.")
        self.show_frame(self.current_frame)

    def toggle_play(self):
        self.playing = not self.playing
        self.last_tick = time.monotonic()
        self.playback_position_frame = float(self.current_frame)
        if self.playing:
            self.play_loop()

    def playback_speed(self):
        value = self.speed_var.get().lower().replace("x", "")
        try:
            return max(1, int(float(value)))
        except ValueError:
            return 1

    def start_zone_review(self):
        self.speed_var.set("8x")
        self.auto_next_var.set(True)
        if self.zone_draw_mode:
            self.zone_draw_mode = False
        self.playback_position_frame = float(self.current_frame)
        self.last_tick = time.monotonic()
        self.set_status(f"Zone review mode: 8x, auto-next enabled, smooth loop targeting {TARGET_REFRESH_HZ} Hz.")
        if not self.playing:
            self.playing = True
            self.play_loop()

    def play_loop(self):
        if not self.playing:
            return

        now = time.monotonic()
        elapsed = max(0.0, now - self.last_tick)
        self.last_tick = now
        speed = self.playback_speed()
        next_position = self.playback_position_frame + elapsed * self.fps * speed
        last_frame = max(0, self.frame_count - 1)

        if next_position >= last_frame:
            self.playback_position_frame = float(last_frame)
            self.show_frame(last_frame, sync_position=False)
            if self.auto_next_var.get() and self.change_video(1):
                self.playback_position_frame = float(self.current_frame)
                self.last_tick = time.monotonic()
                self.playing = True
                self.root.after(REFRESH_DELAY_MS, self.play_loop)
                return
            self.playing = False
            self.set_status("Playback finished.")
            return

        self.playback_position_frame = next_position
        frame_index = int(next_position)
        if frame_index != self.current_frame:
            self.show_frame(frame_index, sync_position=False)
        self.root.after(REFRESH_DELAY_MS, self.play_loop)

    def step_frames(self, delta):
        self.playing = False
        self.show_frame(self.current_frame + delta)

    def jump_seconds(self, seconds):
        self.playing = False
        self.show_frame(self.current_frame + int(seconds * self.fps))

    def start_segment(self):
        self.segment_start = self.current_time_s()
        self.segment_start_var.set(f"Segment start: {self.segment_start:.2f}s")
        self.set_status("Segment start set. Move to the end time, then press End + Save Segment.")

    def end_segment(self):
        if self.segment_start is None:
            messagebox.showinfo("No start", "Press Start Segment first.")
            return
        start_s = min(self.segment_start, self.current_time_s())
        end_s = max(self.segment_start, self.current_time_s())
        if end_s - start_s < 0.03:
            messagebox.showinfo("Too short", "Segment is too short. Move at least one frame before saving.")
            return
        self.save_segment(start_s, end_s)
        self.segment_start = None
        self.segment_start_var.set("Segment start: none")

    def save_whole_clip_segment(self):
        self.save_segment(0.0, self.duration)

    def save_segment(self, start_s, end_s):
        video = self.current_video()
        row = {
            "video_id": video["video_id"],
            "start_s": f"{start_s:.3f}",
            "end_s": f"{end_s:.3f}",
            "attention": self.attention_var.get(),
            "blouse": self.blouse_var.get(),
            "notes": self.notes_var.get().strip(),
        }
        append_csv(SEGMENTS_CSV, SEGMENT_HEADERS, row)
        self.refresh_summary()
        self.set_status(
            f"Saved segment {row['start_s']}s-{row['end_s']}s: "
            f"{row['attention']}, {row['blouse']}"
        )

    def save_event(self):
        video = self.current_video()
        event_type = self.event_type_var.get()
        row = {
            "video_id": video["video_id"],
            "event_time_s": f"{self.current_time_s():.3f}",
            "frame": str(self.current_frame),
            "event_role": "physical_entry",
            "body_part": self.body_part_value(),
            "event_type": event_type,
            "zone_id": ZONE_ID,
            "spatial_relation": self.spatial_var.get(),
            "notes": self.notes_var.get().strip(),
        }
        append_csv(EVENTS_CSV, EVENT_HEADERS, row)
        self.refresh_summary()
        self.set_status(
            f"Saved {event_type} at {row['event_time_s']}s, frame {row['frame']}, {row['body_part']}"
        )

    def save_no_danger(self):
        video = self.current_video()
        row = {
            "video_id": video["video_id"],
            "event_time_s": "",
            "frame": "",
            "event_role": "no_danger",
            "body_part": "none",
            "event_type": "no_danger_event",
            "zone_id": ZONE_ID,
            "spatial_relation": "outside_volume",
            "notes": self.notes_var.get().strip(),
        }
        append_csv(EVENTS_CSV, EVENT_HEADERS, row)
        self.refresh_summary()
        self.set_status("Marked this video as reviewed with no danger event.")

    def undo_last(self, path, headers):
        video = self.current_video()
        rows = read_csv(path, headers)
        for idx in range(len(rows) - 1, -1, -1):
            if rows[idx].get("video_id") == video["video_id"]:
                removed = rows.pop(idx)
                write_csv(path, headers, rows)
                self.refresh_summary()
                self.set_status(f"Removed last row from {path.name}: {removed}")
                return
        self.set_status(f"No rows to remove in {path.name} for this video.")

    def refresh_summary(self):
        video = self.current_video()
        if not video:
            return
        segments = [row for row in read_csv(SEGMENTS_CSV, SEGMENT_HEADERS) if row["video_id"] == video["video_id"]]
        events = [row for row in read_csv(EVENTS_CSV, EVENT_HEADERS) if row["video_id"] == video["video_id"]]

        lines = []
        if segments:
            lines.append("Segments:")
            for row in segments[-6:]:
                lines.append(
                    f"  {row['start_s']}-{row['end_s']}s | "
                    f"attention={row['attention']} | blouse={row['blouse']}"
                )
        else:
            lines.append("Segments: none")

        if events:
            lines.append("Events:")
            for row in events[-6:]:
                when = row["event_time_s"] or "whole_clip"
                lines.append(
                    f"  {when}s | {row['event_type']} | {row['body_part']} | "
                    f"{row['spatial_relation']}"
                )
        else:
            lines.append("Events: none")

        self.summary.configure(state="normal")
        self.summary.delete("1.0", tk.END)
        self.summary.insert("1.0", "\n".join(lines))
        self.summary.configure(state="disabled")
        self.update_review_status()
        self.populate_video_list(select_current=True)
        self.draw_timeline()

    def set_status(self, text):
        self.status_var.set(text)


def main():
    root = tk.Tk()
    app = AnnotationTool(root)

    def on_close():
        app.playing = False
        if app.cap is not None:
            app.cap.release()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
