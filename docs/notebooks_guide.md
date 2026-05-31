# Experiment Notebooks Guide

This guide describes the **42 interactive Jupyter notebooks** tracked in the repository under [`notebooks_experiences/`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences). 

Every single notebook is designed specifically for **causal, live-streaming inference**—meaning that predictions are computed at frame $t$ using only current and historical data ($t \le \text{current}$), without any future-frame leakage.

---

## 1. Sequence Modeling & Time-Series Extensions
These notebooks focus on training and evaluating temporal sequence models (TCN, CNN1D, GRU, LSTM, Transformers) over multi-frame pose history windows.

* **[`sequence_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/sequence_experiments.ipynb)**: Implements the core TCN, GRU, and LSTM models, training them on sliding sequence windows to predict imminent danger-zone entry.
* **[`sequence_stability_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/sequence_stability_experiments.ipynb)**: Tests the generalization stability of TCN and CNN1D danger architectures across different random splits.
* **[`sequence_augmentation_ablation.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/sequence_augmentation_ablation.ipynb)**: Evaluates temporal resamplings, channel dropout, and Gaussian feature jitter to regularize sequence training.
* **[`sequence_timeseries_arch_extension.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/sequence_timeseries_arch_extension.ipynb)**: Compares advanced models like ResNet1D, InceptionTime, Attention BiGRU, and Conv Transformers.
* **[`sequence_timeseries_extension_stability.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/sequence_timeseries_extension_stability.ipynb)**: Tests the 20-seed split stability of these advanced time-series extensions.

---

## 2. Feature Ablations & Causal Audits
These notebooks perform structural ablations, statistical testing, and causal validations to verify that model decisions are scientifically sound.

* **[`sequence_feature_ablation_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/sequence_feature_ablation_experiments.ipynb)**: Systematically disables feature groups (e.g., coordinates, velocities, polygon distances) to determine which signals are most predictive.
* **[`causal_early_warning_audit.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/causal_early_warning_audit.ipynb)**: Verifies that early warnings are triggered before the annotated event using causal, step-by-step rolling evaluation.
* **[`causal_half_second_audit.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/causal_half_second_audit.ipynb)**: Tests alarms under a strict constraint that triggers must occur at least 0.5 seconds before physical entry.
* **[`label_timing_uncertainty_audit.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/label_timing_uncertainty_audit.ipynb)**: Audits how annotation shift noise impacts hit rates and precision.
* **[`sequence_negative_control_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/sequence_negative_control_experiments.ipynb)**: Runs randomized label shuffling to confirm the sequence pipeline does not learn random background noise.

---

## 3. Crop CNN & Attention/PPE Models
These notebooks train image and temporal crop classifiers to detect worker attention and clothing closure status from bounding-box crops.

* **[`crop_cnn_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/crop_cnn_experiments.ipynb)**: Trains still-image custom CNNs, MobileNetV3, and ResNet18 on torso crops.
* **[`crop_cnn_stability_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/crop_cnn_stability_experiments.ipynb)**: Analyzes split stability for still-image crop classifiers.
* **[`crop_augmentation_ablation.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/crop_augmentation_ablation.ipynb)**: Tests photometric, geometric, and standard flipping augmentations on training crops only.
* **[`temporal_crop_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/temporal_crop_experiments.ipynb)**: Implements short GRU and TCN temporal crop classifiers to evaluate sequential crop contexts.
* **[`crop_permutation_significance.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/crop_permutation_significance.ipynb)**: Performs parent-label permutations to verify visual classification significance.
* **[`crop_negative_control_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/crop_negative_control_experiments.ipynb)**: Shuffles crop labels to establish a baseline negative reference.

---

## 4. Generalization & Actor-Holdout Audits
These notebooks stress-test models on unseen actors to determine how well they generalize outside the training staging.

* **[`actor_holdout_sequence_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/actor_holdout_sequence_experiments.ipynb)**: Trains on one actor and tests on the other, revealing the spatial staging gap.
* **[`actor_holdout_feature_ablation.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/actor_holdout_feature_ablation.ipynb)**: Restricts inputs to head/torso motion to mitigate actor shortcuts.
* **[`actor_holdout_feature_stability.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/actor_holdout_feature_stability.ipynb)**: Tests the multi-split stability of this head/torso mitigation.
* **[`crop_actor_holdout_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/crop_actor_holdout_experiments.ipynb)**: Audits cross-actor visual classification for attention and blouse status.

---

## 5. Fusion, Calibration, & Guardrail Sweeps
These notebooks fuse trajectory danger, distraction, and clothing risks into a single unified operational score.

* **[`same_split_fusion_experiments.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/same_split_fusion_experiments.ipynb)**: Sets up aligned splits to train sequence danger and crop risk models jointly.
* **[`final_fusion_meta_model_ablation.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/final_fusion_meta_model_ablation.ipynb)**: Evaluates L2-logistic, Gaussian Naive Bayes, Random Forest, and XGBoost meta-classifiers.
* **[`final_policy_guardrail_grid_audit.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/final_policy_guardrail_grid_audit.ipynb)**: Performs a grid sweep over 170 transparent attention/PPE prior-floor formulas.
* **[`calibration_confidence.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/calibration_confidence.ipynb)**: Plaunders Brier scores and ECE metrics to calibrate continuous risk predictions.
* **[`final_aggregated_score_audit.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/final_aggregated_score_audit.ipynb)**: Aggregates continuous window streams into operational caution, warning, and alarm alarms.

---

## 6. Real-Time Benchmarking & Smoke Tests
These notebooks run high-fidelity benchmarks and deployment smoke tests on raw video files to prove streaming viability.

* **[`sequence_inference_demo.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/sequence_inference_demo.ipynb)**: Performs a basic sequence-risk inference smoke test on precomputed pose features.
* **[`final_causal_fused_stream_smoke.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/final_causal_fused_stream_smoke.ipynb)**: Feeds raw video frame-by-frame, updating crop states and sequence danger causally in timestamp order.
* **[`final_realtime_variant_benchmark.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/final_realtime_variant_benchmark.ipynb)**: Benchmarks steady-state FPS and p95 latency for different deployment models on GPU.
* **[`runtime_resolution_tradeoff_audit.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/runtime_resolution_tradeoff_audit.ipynb)**: Sweeps pose input sizes (320, 384, 512, 640) to trade latency for trace stability.
* **[`runtime_pose_backend_audit.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/runtime_pose_backend_audit.ipynb)**: Integrates ONNX Runtime CPU pose tracking to benchmark CPU fallback streams.
* **[`final_deployment_package_audit.ipynb`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences/final_deployment_package_audit.ipynb)**: Validates code, paths, checklist requirements, and contracts before final distribution.
