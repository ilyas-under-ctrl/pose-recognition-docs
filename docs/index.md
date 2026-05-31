# Pose Recognition Machine Safety

This documentation covers the fixed-camera pose recognition proof of concept for machine-safety risk prediction.

The project combines video capture, annotation, pose/keypoint extraction, temporal danger prediction, attention classification, blouse/PPE classification, and a fused operational risk score.

## Visual Overview

![Browser annotation tool preview](assets/images/web_annotator_preview.png)

The browser annotation tool is the main workflow for reviewing clips, drawing the projected danger zone, marking danger events, and saving segment labels.

![Risk pipeline and policy diagram](assets/images/pipeline_policy_diagram.png)

The research pipeline combines trajectory danger risk, attention risk, and blouse/PPE risk into a final operational risk score.

## Documentation Map

- [Architecture and Annotation](architecture_and_annotation.md): project framing, defensible claims, dataset grounding, annotation strategy, and reliability boundaries.
- [Annotation Tool Usage](annotation_tool_usage.md): how to run the browser annotation tool, define the danger zone, label videos, and validate annotations.
- [ML Autonomous Training Runbook](ml_autonomous_training_runbook.md): durable research plan, model targets, augmentation policy, evaluation criteria, experiment status, and final acceptance criteria.

## Quick Start

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the browser annotation tool:

```powershell
python web_annotator_server.py
```

Open:

```text
http://127.0.0.1:8765
```

Validate annotations after labeling:

```powershell
python validate_annotations.py
```

## Scope

This is an academic proof-of-concept, not a production-certified industrial safety system. The current danger region is modeled as a fixed 2D image-space polygon because the camera and machine are fixed and the dataset does not include above-zone motion.

## Result Figures

![Dataset event distribution](assets/images/dataset_event_distribution.png)

![Policy results comparison](assets/images/policy_results_comparison.png)

![Timing budget](assets/images/timing_budget.png)
