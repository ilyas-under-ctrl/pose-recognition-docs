# Real-Time Machine Safety CV Architecture and Annotation Plan

Date: 2026-05-29

This project should be framed as a real-time worker safety prediction system for a fixed camera, fixed machine, and staged machine-interaction dataset. The current dataset is enough to build a proof-of-concept annotation and modeling pipeline, but not enough to claim production-grade safety performance.

## Current Dataset Grounding

Observed files:

- `captures_manifest.csv` indexes 73 videos.
- All listed videos are 1440x720 at 30 FPS.
- Total duration is about 622.12 seconds, or 10.37 minutes.
- Actors: `ilyas` and `zaayd`.
- Coarse labels: `safe` and `unsafe`.
- The unsafe behavior visible in sampled screenshots is mainly upper-body interaction with the machine: hand, arm, and sometimes head. Feet/legs are not the primary risk signal.
- The fixed high-angle camera makes a 2D danger polygon useful, but not sufficient for true 3D danger-volume decisions.

Dataset counts computed from the manifest:

| Actor | Label | Clips | Duration |
| --- | ---: | ---: | ---: |
| ilyas | safe | 4 | 185.63s |
| ilyas | unsafe | 42 | 149.85s |
| zaayd | safe | 5 | 196.74s |
| zaayd | unsafe | 22 | 89.90s |

## Defensible Architecture

Recommended pipeline:

```text
video frame
-> person/pose extraction
-> fixed projected danger-volume geometry
-> temporal body-part features
-> attention segment model
-> blouse/PPE crop model
-> short-horizon danger predictor
-> fused risk state
```

Use separate labels and model heads, not one monolithic label:

```text
attention: attentive / distracted / unknown
blouse: properly_worn / badly_worn / unknown
danger event: entered_danger_volume / near_miss / no_danger_event
danger source: multi-label hand_or_arm / head / torso / unknown
spatial relation: inside_volume / near_volume / above_projection / outside_volume / occluded / unknown
```

## Claims, Evidence, and Decisions

Claim: pose keypoints are a defensible intermediate representation for this project.

Evidence: MediaPipe Pose Landmarker outputs normalized body landmarks and world landmarks, including `x`, `y`, `z`, and visibility. BlazePose was designed for real-time body pose tracking and reports over 30 FPS on a Pixel 2 phone. Ultralytics pose models also produce human body keypoints and confidence scores.

Decision: use pose landmarks as the shared representation for attention and danger prediction. Keep RGB torso crops for blouse/PPE state because pose does not describe clothing closure.

Sources:

- https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python
- https://arxiv.org/abs/2006.10204
- https://docs.ultralytics.com/tasks/pose/

Claim: a single RGB camera cannot support a strong claim of accurate metric 3D danger-volume localization.

Evidence: monocular 3D human pose estimation is an ill-posed problem because multiple 3D poses can project to similar 2D images. MediaPipe normalized `z` is relative to the hip midpoint and uses roughly the same scale as normalized `x`; world landmarks are model-estimated, not a calibrated depth sensor measurement of the machine volume.

Decision: call the current approach 2.5D, not true 3D. Use the projected zone polygon plus relative `z`, body-part identity, temporal motion, and uncertainty. Do not claim reliable true 3D safety from this camera alone.

Sources:

- https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python
- https://arxiv.org/abs/2107.13788
- https://www.sciencedirect.com/science/article/pii/S2096579620300887

Claim: danger should be predicted as a short-horizon temporal problem, not a static frame classification problem.

Evidence: the user reports danger often occurs within 1-2 seconds, and sampled clips show fast upper-body movements. Temporal convolution work shows that temporal models over frame/keypoint sequences are appropriate for action segmentation and 3D pose-from-video tasks.

Decision: generate labels for horizons such as 300 ms, 500 ms, and 1000 ms from a single annotated event timestamp. Model inputs should use the last 10-30 frames at 30 FPS.

Sources:

- https://openaccess.thecvf.com/content_cvpr_2017/papers/Lea_Temporal_Convolutional_Networks_CVPR_2017_paper.pdf
- https://openaccess.thecvf.com/content_CVPR_2019/papers/Pavllo_3D_Human_Pose_Estimation_in_Video_With_Temporal_Convolutions_and_CVPR_2019_paper.pdf
- https://arxiv.org/abs/1905.06113

Claim: the first danger model should be a fast feature-based baseline before a larger neural sequence model.

Evidence: the dataset has only about 10.4 minutes of video and two actors. Gradient boosted trees are strong tabular-feature baselines; XGBoost and LightGBM are designed for effective/scalable tree boosting. This makes them a practical first baseline for engineered pose-motion-zone features.

Decision: start with feature extraction plus XGBoost/LightGBM/logistic regression baseline. Add a TCN only after the annotation volume and validation evidence justify it.

Sources:

- https://arxiv.org/pdf/1603.02754
- https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree.pdf

Claim: evaluation must split by video, not by frame.

Evidence: video-derived frames have high spatial and temporal correlation. Random frame splitting can leak near-identical samples between train/test sets and inflate performance.

Decision: split by complete video. Also report actor-holdout validation because the dataset has only two actors.

Source:

- https://doaj.org/article/5252f48f47804fa2861c40cc148adf8f

## Annotation Strategy

Do not annotate every frame. Annotate the minimum human decisions needed to generate frame-level training labels automatically.

Per setup:

- Draw one projected danger-volume polygon over the fixed camera view.
- Approximate the physical 3D shape in notes if known: cuboid/cylinder, height, depth, and active machine opening.

Per video:

- Save attention/blouse segments.
- Mark the first timestamp where a body part enters the danger volume.
- Select one or more coarse danger sources: `hand_or_arm`, `head`, `torso`, or `unknown`.
- Select spatial relation.
- Mark safe clips with `no_danger_event`.

The event timestamp creates danger labels:

```text
event_time - 1.0s to event_time = positive for risk_1000ms
event_time - 0.5s to event_time = positive for risk_500ms
event_time - 0.3s to event_time = positive for risk_300ms
```

This is why one carefully selected event timestamp is more efficient than frame-by-frame labeling.

## Output Annotation Files

The annotation tool writes:

- `annotations/videos.csv`: discovered video index.
- `annotations/segments.csv`: attention and blouse state over time.
- `annotations/events.csv`: danger event or no-danger review labels.
- `annotations/zones.json`: fixed projected danger-volume polygon.

These files are intentionally simple CSV/JSON so training scripts can consume them directly.

## Modeling Roadmap

1. Extract pose landmarks for every frame.
2. Compute body-part features for wrists, elbows, head, and torso:
   - normalized `x/y`
   - relative `z`
   - visibility
   - velocity
   - acceleration
   - distance to projected danger polygon
   - projected polygon overlap
3. Train blouse/PPE from upper-body crops using segment labels.
4. Train attention from pose/head/torso windows using segment labels.
5. Train danger prediction from pose-motion-zone windows using generated short-horizon labels.
6. Fuse risks:

```text
final_risk = motion_zone_risk
           + distraction_penalty
           + badly_worn_penalty
           + uncertainty_penalty
```

## Reliability Boundaries

Defensible claims after this pipeline:

- The system can learn staged same-camera behaviors from this dataset.
- It can predict short-horizon risk for hand/arm/head interaction patterns represented in the dataset.
- It can use relative depth/motion as a feature.
- It can support annotation and experimentation.

Claims that are not defensible from the current dataset alone:

- Production-grade machine-safety certification.
- Accurate metric 3D body-part localization inside a machine volume from one RGB camera.
- Reliable suppression of false positives for "above zone but safe" if that pattern is absent from the dataset.
- Generalization to new camera angles, machines, lighting, clothing, or workers without validation.
