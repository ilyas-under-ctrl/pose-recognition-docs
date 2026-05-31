# ML Autonomous Training Runbook

This file is the durable context for the machine-safety ML phase. Use it as the source of truth after model compaction or thread resets.

## Current Dataset State

- Project root: `C:\Users\ilyas\Desktop\pose recognision`
- Annotation app: `http://127.0.0.1:8765/`
- Annotation files:
  - `annotations/videos.csv`
  - `annotations/segments.csv`
  - `annotations/events.csv`
  - `annotations/zones.json`
  - `annotations/deleted_clips.csv`
- Current validated dataset:
  - `72` videos
  - `72` segment rows
  - `72` event rows
  - `63` danger events
  - `9` no-danger events
  - validation status: OK
- One useless unannotated clip was excluded, not deleted:
  - `captures\zaayd\unsafe\unsafe blooza bad 20260512_185739.mp4`
  - recorded in `annotations/deleted_clips.csv`
- Existing annotations are complete enough to start training. Do not require new video recording.

## Hardware And Environment

- CPU: AMD Ryzen 7 7435HS, 8 cores / 16 threads
- RAM: about 16 GB
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU
- VRAM: about 8 GB from `nvidia-smi`
- CUDA available in PyTorch
- Main Python: `Python 3.13.5`
- Installed and usable:
  - `torch 2.10.0+cu130`
  - `torchvision`
  - `cv2`
  - `mediapipe`
  - `ultralytics`
  - `sklearn`
  - `xgboost`
  - `numpy`
  - `pandas`
- Missing but optional:
  - `lightgbm`
  - `optuna`
  - `pyarrow`
  - `matplotlib` / `seaborn`
  - `albumentations`
- Main bottleneck: disk space. C drive had only about `8 GB` free. Keep outputs compact unless the user gives another drive/folder.

## Project Scope

This is an academic proof-of-concept, not a regulated industrial deployment.

Current safety assumption:

```text
2D danger polygon entry ~= danger-volume entry
```

Reason:

- Camera and machine are fixed.
- Existing videos do not include above-danger-zone motion.
- 3D danger volume, multiple camera angles, and depth-aware geometry are future work.

Future-work language:

```text
In this proof-of-concept, the danger region is approximated as a fixed 2D image-space polygon due to the fixed camera and absence of above-zone motion in the recorded dataset. Extension to multi-view or depth-aware 3D danger volume estimation is left for future work.
```

## ML Targets

Build three model families:

1. Danger risk model
2. Attention classifier
3. Blouse/PPE classifier

The final deliverable is not only three independent models. The final deliverable must include a fused operational risk score that combines:

```text
trajectory danger risk
attention/distraction risk
blouse/PPE risk
```

The fused score should become more sensitive when the worker is distracted or the blouse/PPE is badly worn. The intuition is:

```text
worker distracted + moving/accelerating toward danger zone = risk should rise earlier
worker PPE/blouse badly worn + moving/accelerating toward danger zone = risk should rise earlier
worker attentive + PPE good + same trajectory = risk can be slightly less sensitive
```

This fused score must be trained/evaluated as a research artifact, not hard-coded without evidence. At minimum, compare:

- late fusion rule using calibrated probabilities
- learned meta-classifier using danger score, attention score, blouse score, speed, acceleration, and distance-to-zone features
- ablation without attention/blouse scores to prove whether fusion helps

Required fused outputs:

```text
danger_risk_0.5s
danger_risk_1.0s
danger_risk_1.5s
danger_risk_2.0s
attention_risk
ppe_risk
final_fused_risk
recommended_operating_thresholds
```

### Danger Risk Model

Output a continuous score, not only a hard alarm:

```text
risk_score(t, H) = probability that a tracked body part enters the 2D danger polygon within horizon H
```

Evaluate horizons:

```text
H = 0.5s, 1.0s, 1.5s, 2.0s
```

Primary horizon:

```text
H = 1.0s
```

Risk thresholds are selected after evaluation, not fixed upfront:

```text
0.30 -> early caution, likely many false alarms
0.50 -> moderate warning
0.80 -> urgent warning
0.90 -> high-confidence alarm
```

Main desired behavior:

```text
Catch dangerous cases at least 1.0 second early if possible.
False-alarm tolerance is unknown, so produce threshold sweeps.
```

The danger risk model must be evaluated both alone and as part of the final fused risk score. The final risk score should be optimized for early warning, with special attention to "pre-danger" situations where the worker is still outside the zone but is accelerating toward it while distracted or wearing PPE badly.

### Attention Model

Classes:

```text
attentive
distracted
unknown
```

The dataset has visibly distinct looking-away behavior. Start simple.

The attention model must output a probability-like score, not only a class:

```text
attention_risk = P(distracted or not paying attention)
```

This score feeds the final fused risk model. It should increase sensitivity before the worker reaches the machine when trajectory risk is already rising.

### Blouse/PPE Model

Classes:

```text
properly_worn
badly_worn
unknown
```

Use torso/upper-body crops if training an image model.

The blouse/PPE model must output:

```text
ppe_risk = P(badly_worn)
```

This score feeds the final fused risk model. Bad PPE should make the fused score more conservative/sensitive, especially when motion toward the danger zone is detected.

## Annotation Semantics

The human event timestamp is not necessarily exact physical entry. The user often labeled:

```text
T_ann = first frame where a human notices something wrong
```

Therefore, treat event timestamps as noisy risk-onset labels.

Use geometry to derive:

```text
T_geo = first persistent frame where relevant body part enters 2D danger polygon
```

Use both:

```text
human_event_time_s = annotation timestamp
geo_entry_time_s = pose + polygon derived entry timestamp
```

Recommended policy:

- If human event is danger and pose enters polygon, use `T_geo` as the main entry time.
- If human event is danger but pose never enters polygon, generate review screenshot.
- If pose enters polygon but human label is no danger, generate review screenshot.
- Keep annotation timestamp as risk-onset metadata.

Timestamp grace:

```text
event timestamp uncertainty = +/- 0.5s
0.5s at 30 FPS = 15 frames
```

Training can use event-time jitter around `T_ann` or `T_geo` where appropriate.

## Data Splitting Rule

Hard rule:

```text
Split by clip first. Augment only training split. Never augment validation/test.
```

Reason:

- Augmenting before split causes near-duplicate leakage.
- Validation/test metrics become fake-good if derived versions of the same clip appear in training.

Recommended first split:

```text
train: 70%
val: 15%
test: 15%
```

Stratify by:

- danger vs no-danger
- actor where possible
- blouse class where possible
- attention class where possible

There are only `72` parent videos, but they are not the training sample count. The valid procedure is:

- split parent videos first
- derive crops/windows/subclips only after the parent split is known
- keep every derived sample inside the same split as its parent video

The current granularity audit proves this inheritance for window features, sequence windows, crop images, and subclip evaluation:

```text
runs/dataset_granularity_audit/granularity_summary.md
```

Randomly splitting derived windows/crops/subclips is not allowed because adjacent frames from the same parent video would leak across train/validation/test.

## Feature Pipeline

For every frame, extract pose/keypoint data:

- wrists
- elbows
- shoulders
- head/nose
- torso center

Compute:

- x/y position
- confidence
- velocity
- acceleration
- distance to danger polygon
- signed/inside-polygon flag
- motion direction toward polygon
- speed toward polygon
- recent trajectory window statistics

Window inputs for danger:

```text
last 15-60 frames
0.5s to 2.0s of motion history at 30 FPS
```

Labels:

```text
danger_within_0.5s
danger_within_1.0s
danger_within_1.5s
danger_within_2.0s
time_to_danger
body_part
geo_entry_time_s
human_event_time_s
```

For safe/no-danger clips:

```text
danger_within_H = 0
time_to_danger = null
```

For unsafe clips:

```text
frames/windows ending before entry receive horizon labels based on time_to_danger
frames after entry should not dominate prediction training
```

## Augmentation Policy

Apply augmentation only to training data.

Augmentation must be implemented as a first-class, auditable pipeline stage, not only as invisible in-memory noise. Every augmentation experiment must create artifacts proving:

```text
which source samples were augmented
which augmentation method was applied
which split each sample belongs to
that validation/test were not augmented
before/after class counts
augmentation parameter ranges
random seed
```

Required artifacts:

```text
features/augmented_train_windows.csv or .parquet
features/augmentation_manifest.csv
metrics/augmentation_audit.json
error_review/augmentation_examples/
```

The report must include screenshot/contact-sheet proof for visual augmentations and numeric before/after plots for trajectory augmentations.

### Danger Trajectory Augmentation

Most important augmentation for this project.

Use:

- keypoint jitter
- small confidence-aware keypoint noise
- velocity/acceleration noise
- temporal resampling, slightly faster/slower motion
- timestamp jitter around event/entry time, about `+/- 0.5s`
- window start/end jitter
- small pose dropout for occlusion robustness
- class balancing for danger/no-danger windows
- hard-negative mining from near-zone safe windows

Required concrete danger augmentations:

- temporal window jitter: shift window start/end by a few frames without crossing split boundaries
- timestamp jitter: sample event time from `T +/- 0.5s` only for training labels
- time warp: resample trajectories to simulate slower/faster approach speeds
- keypoint jitter: confidence-aware x/y noise with documented pixel/std ranges
- keypoint dropout: randomly hide low-confidence or single-limb points to simulate partial occlusion
- hard-negative mining: oversample safe/negative windows close to the danger polygon
- class-balanced sampling: keep positives from being drowned by easy negatives
- optional mixup-style feature interpolation only if it preserves physical plausibility

The model report must compare:

```text
baseline without augmentation
feature/keypoint jitter only
temporal jitter/resampling only
hard-negative mining only
full augmentation stack
```

Avoid:

- full-frame flips/rotations unless keypoints and danger polygon are transformed exactly the same way
- augmenting validation/test
- destroying geometry consistency

### Attention Image Augmentation

Use for training crops only:

- brightness/contrast
- mild blur
- compression noise
- small crop/scale jitter
- small rotation if it does not break the visual task

Required proof:

- save a contact sheet showing original and augmented attention crops
- save augmentation parameters per crop in `augmentation_manifest.csv`
- train at least one non-augmented and one augmented attention model for comparison

Avoid:

- horizontal flips if left/right machine orientation matters
- aggressive crops that remove head/face

### Blouse/PPE Image Augmentation

Use for torso/upper-body crops:

- torso crop jitter
- brightness/contrast
- mild blur
- compression artifacts

Required proof:

- save a contact sheet showing original and augmented blouse/PPE crops
- avoid hiding the neck/chest opening region
- train at least one non-augmented and one augmented blouse model for comparison

Avoid:

- aggressive hue/color changes
- occluding chest/neck opening region
- large rotations/crops that hide the blouse state

## Research Execution Plan

This project must be executed as a staged research pipeline with a clear final state. A baseline is only a measurement reference, not the goal.

### Phase 1: Dataset Freeze And Audit

Goal:

```text
Prove the dataset is internally consistent and safe to use for experiments.
```

Required steps:

1. Validate annotations.
2. Save dataset version metadata.
3. Create a fixed train/val/test split by clip.
4. Confirm no validation/test leakage.
5. Summarize class balance for danger, attention, and blouse/PPE.
6. Save an audit report.

Testable outputs:

```text
runs/<exp>/config.json
runs/<exp>/split.csv
runs/<exp>/report.md
metrics/dataset_audit.json
```

### Phase 2: Pose, Geometry, And Label Derivation

Goal:

```text
Convert videos and annotations into frame/window-level supervised ML data.
```

Required steps:

1. Extract pose/keypoints for all frames.
2. Smooth/interpolate keypoints conservatively.
3. Compute distance-to-danger-zone and polygon-entry signals.
4. Derive geometry-based entry time where possible.
5. Keep human annotation time as risk-onset metadata.
6. Generate mismatch screenshots for geometry-vs-human disagreements.

Testable outputs:

```text
features/pose_features.csv or .parquet
features/entry_times.csv
features/window_features.csv or .parquet
error_review/geometry_disagreements/
metrics/geometry_audit.json
```

### Phase 3: Baseline Reference Models

Goal:

```text
Create simple reference models so every later trick has a measured comparison.
```

Baseline models:

- danger: logistic regression and/or XGBoost on pose/geometry windows
- attention: simple crop-feature classifier
- blouse/PPE: simple torso/person-crop classifier

Testable outputs:

```text
metrics/baseline_metrics.json
metrics/baseline_threshold_sweeps.csv
models/baseline_*
report.md baseline section
```

### Phase 4: Full Auditable Augmentation

Goal:

```text
Improve robustness using training-only augmentation with proof that validation/test were untouched.
```

Required steps:

1. Generate explicit augmented training artifacts.
2. Save augmentation manifest.
3. Save before/after class counts.
4. Save screenshot/contact-sheet proof for image augmentations.
5. Save numeric plots for trajectory augmentations.
6. Run augmentation ablations.

Required ablations:

- no augmentation
- keypoint/feature jitter only
- temporal jitter/resampling only
- hard-negative mining only
- image augmentation only for attention/blouse
- full augmentation stack

Testable outputs:

```text
features/augmented_train_windows.csv or .parquet
features/augmentation_manifest.csv
metrics/augmentation_audit.json
metrics/augmentation_ablation.csv
error_review/augmentation_examples/
report.md augmentation section
```

### Phase 5: Architecture Search

Goal:

```text
Train multiple viable model families and choose based on evidence, not convenience.
```

Required danger architectures:

- calibrated logistic/linear model
- random forest or extra trees
- XGBoost/gradient boosting
- small MLP on engineered window features
- sequence model over pose windows, such as GRU/LSTM or TCN, if tabular models plateau

Required attention/blouse architectures:

- crop-feature baseline
- frozen pretrained CNN embedding plus linear classifier
- fine-tuned lightweight CNN if dataset size and runtime allow
- augmented vs non-augmented versions

For each architecture, report:

```text
train/val/test metrics
threshold sweep
latency
model size
failure modes
whether it is viable for real-time proof-of-concept
```

Testable outputs:

```text
metrics/architecture_comparison.csv
metrics/model_size_report.json
models/<architecture_name>/
report.md architecture comparison section
```

### Phase 6: Final Fused Risk Model

Goal:

```text
Produce one final operational risk score that combines trajectory danger, attention, and PPE/blouse state.
```

Required fusion variants:

- trajectory-only danger risk
- trajectory + attention risk
- trajectory + PPE risk
- trajectory + attention + PPE risk
- transparent rule/policy fusion with human-specified attention/PPE sensitivity
- learned meta-classifier fusion as an ablation/comparator

Fusion is policy-first. The dataset trains the component estimators and measures the tradeoff, but it does not need to discover the safety prior. The fused score should become more sensitive when:

```text
worker is distracted
worker PPE/blouse is badly worn
worker is moving or accelerating toward the danger polygon
```

Testable outputs:

```text
models/fused_risk_model.*
metrics/fused_risk_metrics.json
metrics/fused_risk_ablation.csv
metrics/fused_threshold_sweep.csv
error_review/fused_risk_failures/
report.md final fused model section
```

### Phase 7: Latency And Real-Time Viability

Goal:

```text
Prove whether the system can run as a real-time proof-of-concept.
```

Required latency tests:

- pose inference latency per frame
- attention model latency
- blouse/PPE model latency
- danger model latency
- fusion latency
- end-to-end latency
- FPS on RTX 4060 laptop
- CPU fallback estimate if feasible

Testable outputs:

```text
metrics/latency_report.json
metrics/realtime_viability.md
report.md latency section
```

### Phase 8: Final Research Report

Goal:

```text
Create a defensible academic-project report from the experiments.
```

The final report must include:

- dataset and annotation protocol
- 2D danger-zone assumption and future 3D extension
- preprocessing and pose extraction
- augmentation methodology with proof
- architecture comparison
- fused risk model
- threshold selection
- latency results
- screenshots of failures and qualitative examples
- limitations and future work

Testable output:

```text
runs/<best_exp>/final_report.md
```

## Evaluation Metrics

Danger:

- recall by horizon
- false alarms per minute
- average early warning time
- median early warning time
- missed dangerous clips
- late detections
- threshold sweep from `0.05` to `0.95`
- precision/recall curve
- ROC-AUC and PR-AUC where meaningful
- clip-level success/failure table

Timing categories:

```text
early_hit: model warns >= 1.0s before entry
good_hit: model warns between T-1.0s and T
grace_hit: model warns between T and T+0.5s
late_or_miss: model warns after T+0.5s or never
```

Attention/blouse:

- accuracy
- balanced accuracy
- per-class precision/recall/F1
- confusion matrix
- failure screenshots

Fused final risk:

- fused risk threshold sweep
- comparison against trajectory-only danger risk
- early warning time with and without attention/PPE modifiers
- false alarms per minute with and without fusion
- missed danger clips with and without fusion
- ablation table:
  - trajectory only
  - trajectory + attention
  - trajectory + PPE
  - trajectory + attention + PPE
- calibration curve or reliability table if possible

Latency and deployability:

- pose inference latency per frame
- feature computation latency per frame/window
- danger model inference latency
- attention model inference latency
- blouse/PPE model inference latency
- fused risk computation latency
- total end-to-end latency estimate
- FPS on the local RTX 4060 laptop
- CPU fallback estimate if feasible
- model size on disk
- peak memory/VRAM notes

## Visual Error Review

Generate screenshot sheets for:

- false negatives
- false positives
- late detections
- geometry entry vs human annotation disagreement
- pose failures
- low-confidence body-part tracks
- attention/blouse misclassifications

Screenshots should include overlays:

- video frame
- danger polygon
- pose keypoints
- predicted risk score
- attention risk
- PPE/blouse risk
- final fused risk score
- threshold
- human event time
- geometry entry time
- time-to-danger
- predicted vs ground-truth label

Augmentation screenshots/contact sheets must include:

- original crop/frame
- augmented versions
- augmentation method names
- parameter values
- split label proving only training data was augmented
- target label before/after augmentation

Keep screenshots compact because disk space is low.

## Artifact Structure

Recommended output layout:

```text
runs/
  exp_001_baseline/
    config.json
    experiment_log.md
    split.csv
    features/
      pose_features.parquet or pose_features.csv
      window_features.parquet or window_features.csv
      augmented_train_windows.parquet or augmented_train_windows.csv
      augmentation_manifest.csv
    models/
    metrics/
      metrics.json
      threshold_sweep.csv
      augmentation_audit.json
      architecture_comparison.csv
      latency_report.json
      fused_risk_metrics.json
      confusion_matrices/
    error_review/
      false_negatives/
      false_positives/
      late_detections/
      geometry_disagreements/
      augmentation_examples/
      fused_risk_failures/
    report.md
```

If disk space is tight:

- prefer CSV/parquet features over extracted raw frames
- save only selected review screenshots
- do not dump every frame

## Safety Rules For The Agent

- Do not delete raw videos.
- Do not modify annotations except by making backups first.
- Do not augment validation/test.
- Do not overwrite previous experiment runs.
- Do not trust a metric without checking leakage.
- Do not pick a final threshold without threshold sweep.
- Do not use a large video transformer before a baseline exists.
- Keep all steps reportable and reproducible.

## Final End State

The project is complete only when the run folder contains a defensible final model package and research report, not merely a baseline.

Required final artifacts:

```text
runs/<best_exp>/
  config.json
  split.csv
  final_report.md
  features/
    pose_features.*
    window_features.*
    augmented_train_windows.*
    augmentation_manifest.csv
  models/
    danger/
    attention/
    blouse_ppe/
    fused/
  metrics/
    dataset_audit.json
    geometry_audit.json
    augmentation_audit.json
    augmentation_ablation.csv
    architecture_comparison.csv
    danger_threshold_sweeps.csv
    fused_risk_metrics.json
    fused_risk_ablation.csv
    fused_threshold_sweep.csv
    latency_report.json
  error_review/
    augmentation_examples/
    false_negatives/
    false_positives/
    late_detections/
    geometry_disagreements/
    fused_risk_failures/
```

The final selected system must expose:

```text
danger_risk_0.5s
danger_risk_1.0s
danger_risk_1.5s
danger_risk_2.0s
attention_risk
ppe_risk
final_fused_risk
selected_thresholds
latency_ms_per_frame
```

## Testable Acceptance Criteria

The final state must be testable with explicit files and metrics.

### Data Integrity

- `validate_annotations.py` passes.
- Train/val/test split is by clip.
- No augmented validation/test samples exist.
- Augmentation audit proves only training samples were augmented.

### Augmentation

- `augmentation_manifest.csv` exists.
- `augmentation_audit.json` exists.
- Contact sheets/screenshots prove image augmentations.
- Numeric plots or CSVs prove trajectory augmentations.
- Ablation shows whether each augmentation helped or hurt.

### Model Coverage

- Danger model has at least three architecture families tested.
- Attention model has baseline and at least one augmented or pretrained-feature model.
- Blouse/PPE model has baseline and at least one augmented or pretrained-feature model.
- Fused final risk is compared against trajectory-only danger risk.

### Evaluation

- Danger threshold sweeps exist for `0.5s`, `1.0s`, `1.5s`, and `2.0s`.
- Final fused threshold sweep exists.
- Metrics include recall, precision, false alarms/min, early-warning time, missed clips, and late detections.
- Error screenshots exist for false positives, false negatives, late detections, and fused-risk failures.

### Latency

- Latency report exists.
- End-to-end FPS is measured on the local RTX 4060 laptop.
- Model size and per-stage latency are reported.

### Report

- `final_report.md` exists.
- Report explains:
  - dataset
  - annotations
  - 2D danger-zone assumption
  - augmentation
  - architectures tested
  - fused risk score
  - latency
  - failure cases
  - limitations
  - future 3D/multi-camera extension

## Updated Prompt To Start Or Resume The Autonomous Loop

Use this prompt when ready:

```text
Start or resume the autonomous ML research loop described in docs/ml_autonomous_training_runbook.md.

The end goal is a final testable proof-of-concept system, not only a baseline.

Build and compare:
- danger risk models for 0.5s, 1.0s, 1.5s, 2.0s
- attention risk models
- blouse/PPE risk models
- final fused risk model combining trajectory, attention, and PPE

Use the existing annotated dataset only.
Do not delete raw videos.
Do not modify annotations except by making backups.
Use train/val/test split by clip.
Augment only training data.

Implement full auditable augmentation:
- augmented training artifacts
- augmentation manifest
- augmentation audit
- screenshot/contact-sheet proof
- augmentation ablations

Test multiple model architectures, not only one.
Measure threshold sweeps, error screenshots, calibration where feasible, model size, and latency.

Stop only when the final end state and testable acceptance criteria in the runbook are satisfied, or if blocked by a decision that materially changes the research design.
```

## Current Status Correction: Temporal Danger Models

The earlier `exp_006_final_research` run is now a baseline/fused-risk reference, not the final architecture conclusion.
It trained tabular-window danger models, attention/PPE crop-feature models, and a fused score, but the selected danger MLP was not a true time-series model.

True sequence-model catalogues have now been added:

```text
runs/exp_009_sequence_len15_catalogue
runs/exp_007_sequence_catalogue
runs/exp_008_sequence_len60_catalogue
runs/exp_010_sequence_len60_focal_catalogue
runs/exp_011_sequence_len60_smooth_catalogue
runs/exp_012_sequence_stability_shortlist
runs/exp_015_sequence_stability_10seed_shortlist
runs/exp_021_sequence_stability_extra10
runs/exp_022_sequence_stability_20seed_combined
runs/exp_023_sequence_feature_ablation
runs/exp_024_sequence_negative_control
runs/exp_025_sequence_negative_control_exact
runs/exp_038_label_timing_uncertainty
runs/exp_028_sequence_ensemble
runs/exp_029_sequence_ensemble_stability
runs/exp_033_final_operating_points
runs/exp_034_final_error_review
runs/exp_013_crop_cnn_catalogue
runs/exp_016_crop_cnn_stability
runs/exp_066_crop_actor_holdout
runs/exp_067_crop_augmentation_ablation
runs/exp_031_temporal_crop_catalogue
runs/exp_032_temporal_crop_stability
runs/exp_026_crop_negative_control
runs/exp_027_crop_permutation_significance
runs/exp_017_actor_holdout_sequence
runs/exp_030_actor_holdout_ensemble
runs/exp_035_actor_holdout_feature_ablation
runs/exp_036_actor_holdout_feature_arch_extension
runs/exp_037_actor_holdout_feature_stability
runs/exp_014_sequence_crop_fusion
runs/exp_020_same_split_fusion
runs/exp_039_final_aggregated_score
runs/exp_068_final_fusion_meta_model_ablation
runs/exp_069_final_policy_guardrail_grid
runs/dataset_granularity_audit
runs/exp_018_inference_smoke_tcn_aug
runs/exp_019_raw_video_inference_smoke_tcn_aug
runs/exp_010_sequence_len60_focal_catalogue/calibration_tcn_aug
runs/exp_014_sequence_crop_fusion/calibration_tcn_aug_meta
runs/exp_010_sequence_len60_focal_catalogue/subclip_eval_tcn_aug
runs/exp_014_sequence_crop_fusion/subclip_eval_tcn_aug_fusion
runs/sequence_master_catalogue/master_sequence_catalogue_summary.md
runs/final_research_report.md
```

Sequence architectures tested so far:

- flatten MLP over raw sequence
- 1D CNN
- TCN
- GRU
- LSTM
- CNN-GRU
- temporal Transformer
- TCN without stochastic sequence augmentation
- GRU without stochastic sequence augmentation

Sequence augmentations tested so far:

- Gaussian feature jitter
- feature channel dropout
- temporal cutout
- temporal speed resampling

Training objectives tested so far:

- weighted BCE
- focal BCE
- label-smoothed weighted BCE

Current practical conclusion:

- Real sequence models are the correct architecture family for danger prediction.
- Sequence models improve validation performance over the tabular-window MLP baseline.
- Focal loss on the 60-frame TCN currently gives the strongest test AP diagnostic, but test-set diagnostics must not be used as final selection.
- Test ranking remains unstable because the dataset is small, even after repeated video-level split and actor-held-out experiments.
- Candidate families tested include TCN, GRU, LSTM, 1D CNN, CNN-GRU, temporal Transformer, and flatten MLP sequence baselines.
- The first repeated split stability check favors TCN-family models, but shows enough variance that final claims must use mean and standard deviation across repeats, not only one split.
- The expanded 10-seed repeated split stability check again favors TCN-family models, but AP standard deviations remain large enough that the report must present mean/std rather than a single best split.
- The combined 20-seed repeated split stability check keeps the same conclusion: TCN variants are the best-supported danger family, but variance remains material. The leading repeated-split candidates are `tcn_aug_bce`, `tcn_aug_focal`, `tcn_noaug_bce`, `cnn1d_aug_focal`, and `tcn_noaug_focal`.
- Sequence feature-group ablation has been added. It supports using motion/geometry features, but the `no_zone_geometry` result also shows the fixed staged dataset contains shortcut cues. Final wording must not claim pure geometric reasoning.
- Sequence negative controls have been added. The primary exact-prevalence window-label shuffle control collapses to chance-level AP near prevalence (`~0.13` on test), which supports that the real sequence results are not just a metric bug or direct leakage. The earlier parent-sequence shuffle control is kept as a caveat because it distorted prevalence when source and target clip lengths differed.
- Label-timing uncertainty has been audited. For the final `mean_temporal_conv` high-sensitivity operating point, strict current-label AP is `0.684`; adding `0.5s` boundary slack raises AP to `0.745`. If the true event timestamp is shifted `0.5s` earlier, AP drops to `0.236` and pre-entry hit falls to `0.566`. Final reporting must treat event-time annotation as a meaningful uncertainty source.
- Sequence ensemble/stacking has been added. The fixed-split result was mixed, but repeated-split ensemble stability shows temporal-convolution/T C N-family averaging improves mean test AP over single models. Treat the operational candidate as an ensemble over the strongest temporal-convolution family, while still reporting the single-model TCN baseline.
- Final operating-point and latency auditing has been added. Thresholds are selected on validation splits and then applied to corresponding test splits. The main tradeoff is explicit: `mean_temporal_conv` high-hit mode reaches test hit `0.878` with `3.384` safe false alarms/min, while its balanced mode reaches hit `0.798` with `2.433` safe false alarms/min and higher precision. Estimated reference FPS remains above `90` because YOLO pose dominates latency.
- Final visual error review has been added. Contact sheets show good early hits, weak early hits, missed danger, and safe false alarms for the final operating candidates. This gives qualitative evidence for where thresholds fail: safe false alarms occur when workers are close to the machine but annotated safe, while many misses have high scores that do not cross stricter thresholds.
- Crop CNN and transfer-learning models have now been trained for attention and blouse/PPE. Their scores are high, but attention/PPE test splits are tiny, so they should be reported as proof-of-concept classifiers, not robust generalization proof.
- Crop label-shuffle controls and parent-label permutation significance have been added. Blouse/PPE remains meaningfully above random parent-label assignment in the fixed test split. Attention remains fragile because the fixed test split has only one positive attention parent.
- Short temporal crop/clip models have now been added for attention and blouse/PPE. They test mean-pooling, flat MLP, GRU, and TCN heads over four sampled person crops. Repeated parent-split stability shows they do not clearly beat the still-image crop CNN for attention; blouse/PPE is already near-saturated and temporal GRU/flat heads tie or slightly improve the video-level AP. This supports keeping still-image crop CNNs as the simple operational default while documenting temporal crop models as an ablation.
- Sequence + crop-CNN fusion has been tested. It improves the validation-selected sequence model slightly, but does not clearly dominate the strongest sequence-only test diagnostic, so fusion remains an ablation rather than a proven final win.
- Parent-safe subclip evaluation has been added. Videos are divided into 1s, 2s, and 3s bins for metrics, but train/val/test membership is inherited from the parent video to avoid correlated-window leakage.
- Dataset granularity audit has been added. It confirms `72` parent videos expand into `4,585` temporal windows, `712` crop images, and parent-safe subclips without split leakage. It also confirms unsafe parent videos produce both positive near-entry windows and negative far-before-entry windows.
- Crop CNN repeated-split validation has been added. Blouse/PPE is more stable than attention; attention remains weaker because the distracted class has fewer parent clips.
- Crop actor-held-out validation has been added. It holds out one actor entirely for attention and blouse/PPE crop classifiers. The stress result confirms that same-parent-split crop scores are optimistic: held-out `zaayd` attention crop AP tops out near `0.380`, while blouse/PPE is stronger but still only proven on two actors.
- Crop augmentation ablation has been added. It tests `none`, `photometric_only`, `geometry_only`, `standard_no_flip`, and `standard_with_flip` on attention `small_cnn` and blouse/PPE `resnet18` across 5 parent-video split seeds. Validation/test crops remain unaugmented. Attention benefits from some spatial/standard augmentation, but validation/test ranking differs; blouse/PPE is near-saturated across policies.
- Temporal crop repeated-split validation has been added. It directly answers whether attention/blouse should use smaller clips instead of pictures: short crop clips are viable, but the repeated-split result does not justify replacing the simpler still-image attention/PPE crop CNNs as the main model.
- Calibration and parent-video bootstrap confidence intervals have been added for the strongest sequence-only and learned sequence/crop fused candidates. They show the core tradeoff: high-hit validation thresholds can create many false alarms, while the learned fused threshold improves precision but sacrifices hit rate.
- Final operating-point thresholds are now reported as policy choices, not universal constants. The report should present at least a high-sensitivity operating point and a lower-false-alarm operating point.
- Actor-held-out sequence validation has been added. It exposes a real generalization gap: performance is much worse when `zaayd` is the held-out actor than when `ilyas` is the held-out actor. This prevents any honest claim of actor-robustness on the current dataset.
- Actor-held-out sequence ensembling has been added. It does not fix the actor gap: `zaayd` holdout AP remains around `0.33-0.34`, far below same-split repeated-split ensemble AP. Actor robustness remains unproven.
- Actor-held-out feature mitigation has been added. Reducing the sequence input to head/torso geometry-motion improves the weak `zaayd` holdout in repeated-seed stability (`head_torso_geometry_motion + cnn1d_aug_focal` AP mean `0.378`, `head_torso_geometry_motion + tcn_noaug_bce` AP mean `0.371`) compared with all-feature alternatives, but this remains far below same-split performance. It is a mitigation and a clue about shortcut/actor cues, not a solved robustness claim.
- Actor-held-out score ensembling over the repeated feature-mitigation candidates has been added. The best weak-actor score variant is `mean_head_torso_geometry_motion` for held-out `zaayd` with AP mean `0.425`, hit `0.933`, FA/min `8.353`, and precision `0.059`. This improves the ranking metric, but the false-alarm/precision tradeoff remains weak, so actor robustness remains unproven.
- Deployment-style inference smoke tests have been added for the 60-frame focal TCN candidate. One uses precomputed pose features and one starts from the raw MP4, runs YOLO pose extraction, then produces per-frame risk predictions and a top-risk contact sheet.
- Same-parent-split sequence/crop fusion validation has been added. For the `tcn_aug_focal` candidate, learned meta fusion improves mean test AP over sequence-only, but validation still ranks sequence-only slightly higher, so fusion is promising but not a universal win.
- Final aggregated trajectory+attention+PPE score auditing has been added. The best AP fused option is `final_learned_meta_mean` (`AP 0.744`, hit `0.875`, FA/min `5.574`, precision `0.459`). A transparent balanced option is `final_attention_ppe_prior` (`AP 0.736`, hit `0.833`, FA/min `2.915`). The intentionally more sensitive attention/PPE rule reaches hit `0.917` and median early warning `1.183s`, but lower precision (`0.208`), so it should be presented as an alerting policy rather than the most accurate ranking model.
- Final fusion meta-model ablation has been added. Logistic L2 fusion is competitive (`AP 0.741`) and nonlinear/meta options were tested, but the final fused score should be policy-first: the dataset trains component estimators and measures tradeoffs, while the safety prior that bad PPE/distraction raises risk is human-specified.
- Final policy guardrail grid auditing has been added. It sweeps `170` transparent attention/PPE policy variants. The best strong-PPE candidate is `prior_aw0p25_pw0p50_iw0p00`, with PPE floor `0.50`, AP `0.736`, hit `0.875`, FA/min `2.659`, precision `0.488`, and median early warning `0.956s`.
- Final deployment runtime auditing has been extended. Optimized CUDA variants, CPU-side lightweight checks, pose-resolution sweeps, and an ONNX pose-backend audit have all been tested. The ONNX artifact is fixed at `320x320`; ONNX Runtime CUDA is not usable in the current environment because required CUDA/cuBLAS DLLs are missing, and ONNX CPU pose does not close the fused real-time gap (`27.19 FPS` optimistic hybrid for the fastest fused candidate, p95 `56.48 ms`, score p95 drift `0.247`).

Current status before claiming finality:

- The final manuscript-style report, model card, claim/evidence matrix, rerun-command manifest, reproducibility manifest, and catalogue completion audit now exist.
- The catalogue is research-demo complete enough to support a proof-of-concept conclusion, but the active goal is not complete because actor robustness, production safety, universal architecture exhaustion, threshold finality, and production real-time final fused runtime remain explicit limitations.
