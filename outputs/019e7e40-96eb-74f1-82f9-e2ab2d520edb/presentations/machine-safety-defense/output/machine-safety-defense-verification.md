# Vérification de la présentation

## Livrables

- Deck PowerPoint: `machine-safety-defense-presentation.pptx`
- Script oral et artefacts à montrer: `machine-safety-defense-speaker-script.md`
- Contact sheet de contrôle: `../preview/contact-sheet.png`
- Rapport layout: `../qa/layout-quality.txt`

## Contrôles effectués

- Export PPTX réussi: 11 slides, format 1280 x 720.
- Toutes les slides ont été rendues en PNG dans `../preview/`.
- Contact sheet générée et inspectée visuellement.
- Layout checker exécuté sur les 11 fichiers de layout: 0 erreur, uniquement des avertissements tolérables liés à des métriques alignées ou à des labels train/val/test volontairement côte à côte.
- Le deck et le script sont en français.
- Les sources de slides et le script oral ont été réalignés avec le paradigme final: TCN pour l'alerte opérateur, GRU exact-entry pour le stop court horizon.
- Le PPTX et les previews présents dans ce dossier proviennent du dernier export disponible; cette passe locale a mis à jour les sources et le script, sans réexport automatique du deck faute de script de build reproductible dans ce dossier.

## Points vérifiés contre la demande

- Pacing: problème, cible opérationnelle, dataset, annotation, variables, modèles, évaluation, résultats, politique, déploiement, conclusion.
- Thème: visuel sobre d'ingénierie/sécurité, palette cohérente, figures du rapport intégrées.
- Script: timing par diapo, texte à dire, transitions.
- Artefacts: annotation tool, pipeline, résultats TCN/GRU, crops attention/blouse, timing.
- Vérification par images: previews PNG et contact sheet disponibles.
