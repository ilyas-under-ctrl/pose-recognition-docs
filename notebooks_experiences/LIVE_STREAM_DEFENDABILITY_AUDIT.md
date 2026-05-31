# Audit live-streaming des notebooks

Objectif : supprimer les notebooks qui ne sont pas defendables dans le contexte du probleme final, c'est-a-dire la prediction sur flux video live.

## Regle de decision

Garder seulement si le notebook contribue directement a au moins un element du systeme live : modele causal, alerte precoce, time-to-entry, calibration de seuil, robustesse du candidat live, inference frame-by-frame, latence ou deploiement.

Supprimer si le notebook est principalement un audit de catalogue, une evaluation subclip offline, une demo non causale, un ensemble post-hoc non retenu pour le live, ou un pipeline global trop large.

## Gardes

| Notebook | Pourquoi c'est defendable pour le live |
|---|---|
| `actor_holdout_feature_ablation.ipynb` | Ablation de features pour reduire les echecs actor-holdout du modele live. |
| `actor_holdout_feature_stability.ipynb` | Verifie la stabilite des mitigations actor-holdout pour le modele live. |
| `actor_holdout_sequence_experiments.ipynb` | Teste la generalisation du modele sequence live a des acteurs non vus. |
| `calibration_confidence.ipynb` | Calibre les probabilites/seuils qui seront utilises dans une decision live. |
| `causal_early_warning_audit.ipynb` | Audit explicitement live-stream: decision a t avec seulement l'historique jusqu'a t. |
| `causal_half_second_audit.ipynb` | Audit causal avec exigence d'alarme au moins 0.5 s avant l'entree. |
| `crop_actor_holdout_experiments.ipynb` | Robustesse acteur des modeles crop utilises dans le contexte live. |
| `crop_augmentation_ablation.ipynb` | Teste les augmentations qui rendent les modeles crop plus robustes en streaming. |
| `crop_cnn_experiments.ipynb` | Modele crop image utilisable sur frame courante pour contexte attention/PPE. |
| `crop_cnn_stability_experiments.ipynb` | Stabilite des modeles crop utilisables dans une politique live. |
| `crop_negative_control_experiments.ipynb` | Controle negatif des labels crop avant de les utiliser dans une politique live. |
| `crop_permutation_significance.ipynb` | Teste la significativite des scores crop avant usage dans une politique live. |
| `early_warning_experiments.ipynb` | Entraine directement des modeles d'alerte precoce causale avant entree physique. |
| `early_warning_tabular_experiments.ipynb` | Baseline physique/tabulaire causale pour l'alerte precoce en live. |
| `exact_entry_forecast_experiments.ipynb` | Prevoit l'instant exact d'entree physique avec metriques causales. |
| `final_aggregated_score_audit.ipynb` | Audit des scores finaux par fenetre qui peuvent alimenter une politique live. |
| `final_causal_fused_stream_smoke.ipynb` | Smoke test causal frame-by-frame: frame t utilise seulement frame t et historique <= t. |
| `final_deployment_package_audit.ipynb` | Audit de readiness du package de scoring live et des artefacts runtime. |
| `final_fusion_meta_model_ablation.ipynb` | Compare des familles de fusion finale avant de les tester en mode causal. |
| `final_operating_point_audit.ipynb` | Selectionne les points de fonctionnement et estime la latence pour le live. |
| `final_policy_guardrail_grid_audit.ipynb` | Balaye des politiques transparentes attention/PPE pour score live final. |
| `final_realtime_variant_benchmark.ipynb` | Benchmark temps reel des variantes causales de deploiement. |
| `final_threshold_policy_stress_audit.ipynb` | Stress-test des seuils fixes, indispensable pour une alarme live. |
| `hand_detail_experiment.ipynb` | Teste si les landmarks de main ameliorent la prediction causale d'entree. |
| `label_timing_uncertainty_audit.ipynb` | Teste la sensibilite aux timestamps d'entree, critique pour une alerte live. |
| `runtime_pose_backend_audit.ipynb` | Compare les backends pose pour la latence de streaming. |
| `runtime_resolution_tradeoff_audit.ipynb` | Teste resolution pose vs vitesse/stabilite pour atteindre le live. |
| `same_split_fusion_experiments.ipynb` | Fusion sequence+crop sur split coherent, base des politiques finales testees en streaming. |
| `sequence_augmentation_ablation.ipynb` | Teste les augmentations temporelles pour rendre le modele sequence live plus robuste. |
| `sequence_experiments.ipynb` | Modele sequence causal: utilise une fenetre d'historique jusqu'a t pour predire le danger court horizon. |
| `sequence_feature_ablation_experiments.ipynb` | Teste quelles features causales de pose/geometrie sont utiles au modele live. |
| `sequence_inference_demo.ipynb` | Smoke test d'inference sequence sur video/features pour verifier le chemin live minimal. |
| `sequence_negative_control_experiments.ipynb` | Controle negatif pour verifier que le modele sequence live n'apprend pas un signal artificiel. |
| `sequence_stability_experiments.ipynb` | Verifie que le modele sequence live reste stable sur plusieurs splits/seeds. |
| `sequence_timeseries_arch_extension.ipynb` | Compare des architectures temporelles candidates pour prediction live. |
| `sequence_timeseries_extension_stability.ipynb` | Valide la stabilite des architectures temporelles candidates live. |
| `temporal_crop_experiments.ipynb` | Explore des modeles crop temporels compatibles avec une fenetre recente en streaming. |
| `temporal_crop_stability_experiments.ipynb` | Stabilite des modeles crop temporels candidats streaming. |
| `time_to_entry_experiments.ipynb` | Modele le temps restant avant entree physique avec evaluation causale. |
| `time_to_entry_repeated_split_experiments.ipynb` | Repete l'experience time-to-entry sur splits multiples pour robustesse live. |

## Supprimes

| Notebook | Raison |
|---|---|
| `actor_holdout_ensemble.ipynb` | Ensemble score-level/offline non retenu comme chemin live simple; trop indirect pour la prediction streaming. |
| `actor_holdout_score_ensemble_audit.ipynb` | Audit d'ensemble post-hoc; utile recherche, mais pas une experience a relancer pour le chemin live final. |
| `catalogue_completion_audit.ipynb` | Meta-audit de couverture du catalogue, pas une experience de prediction live. |
| `dataset_granularity_audit.ipynb` | Audit de dataset/leakage; important pour documentation, mais pas une experience live streaming a executer. |
| `final_aggregated_subclip_evaluation.ipynb` | Evaluation subclip offline; le code lui-meme distingue cela d'une preuve temps reel. |
| `final_error_review.ipynb` | Generation de contact sheets pour inspection visuelle, pas une experience de prediction live. |
| `final_fused_inference_demo.ipynb` | Non causal: le script assigne un clip_mean a toutes les frames et dit que ce n'est pas une estimation online causale. |
| `final_statistical_comparison_audit.ipynb` | Comparaison statistique offline entre resultats, pas une experience de prediction streaming. |
| `fusion_sequence_crop.ipynb` | Ancienne fusion initiale remplacee par same_split_fusion et le smoke causal; moins defendable pour le chemin live. |
| `ml_pipeline.ipynb` | Pipeline global de construction d'artefacts, trop large et pas une experience ciblee live streaming. |
| `sequence_combined_ensemble_stability.ipynb` | Ensemble extension/original non retenu comme candidat live simple; trop couteux/indirect. |
| `sequence_ensemble_experiments.ipynb` | Ensembles/stacking offline; la cible live propre est sequence-only ou variante benchmarkee. |
| `sequence_ensemble_stability.ipynb` | Stabilite d'ensemble offline; pas le chemin live principal. |
| `subclip_evaluation.ipynb` | Evaluation subclip offline/chunk ranking, pas une evaluation live a t. |
