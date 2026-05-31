# Guide d'Utilisation - Système de Sécurité Machine CV

Ce guide explique comment installer, annoter, et exécuter ce projet de preuve de concept (POC) pour la sécurité des techniciens à proximité des machines.

---

## 1. Installation des Dépendances

Le projet utilise Python (testé avec Python 3.12/3.13) et nécessite quelques bibliothèques standards d'analyse de données et de vision par ordinateur (OpenCV, MediaPipe, Ultralytics, PyTorch, XGBoost).

Pour installer tous les packages requis pour le serveur d'annotation et les pipelines ML, exécutez la commande suivante à la racine du projet :

```powershell
python -m pip install -r backend/requirements.txt
```

---

## 2. Outil d'Annotation Temporelle (Recommandé)

L'outil d'annotation est disponible via une interface Web locale très intuitive (lecteur vidéo natif, overlays Canvas 2D, timeline interactive).

### Lancement rapide :
Pour lancer l'outil d'annotation sous Windows, double-cliquez simplement sur le script dans le dossier `jobs/` :
- **Chemin** : [`jobs/run_web_annotation_tool.bat`](file:///c:/Users/ilyas/Desktop/pose%20recognision/jobs/run_web_annotation_tool.bat)

Ou exécutez manuellement la commande suivante depuis la racine :
```powershell
python backend/web_annotator_server.py
```

Ensuite, ouvrez votre navigateur et accédez à :
```text
http://127.0.0.1:8765
```

### Fonctionnalités de l'interface :
1. **Sélection de la vidéo** : Un clip d'essai léger est déjà inclus dans le dossier [`data/captures/`](file:///c:/Users/ilyas/Desktop/pose%20recognision/data/captures) pour tester immédiatement l'outil.
2. **Polygone de danger** : Cliquez sur `Edit Zone` (ou touche `Z`) pour dessiner le contour 2D de la zone dangereuse de la machine, puis sauvegardez.
3. **Segments d'état** : Sélectionnez l'état d'attention du travailleur (`attentive` ou `distracted`) et l'état de sa blouse (`properly_worn` ou `badly_worn`), puis marquez le segment sur la timeline.
4. **Événements de danger** : Positionnez la tête de lecture sur la première image où une partie du corps (main, bras, tête) pénètre dans la zone de danger, puis cliquez sur `Mark Danger` pour enregistrer le timestamp précis.

### Validation des annotations :
Après chaque session d'étiquetage, vous pouvez vérifier la cohérence de la base de données locale (valider les index, les durées de segments, et la géométrie des polygones) en exécutant :
```powershell
python backend/validate_annotations.py
```

---

## 3. Lancement des Entraînements (ML)

Tous les scripts de recherche expérimentale pour entraîner et évaluer les modèles sont conservés à la racine du projet pour faciliter l'exécution directe des notebooks :
* **Dossier d'expériences** : [`notebooks_experiences/`](file:///c:/Users/ilyas/Desktop/pose%20recognision/notebooks_experiences) (contient 42 notebooks Jupyter expliquant pas à pas la sélection des architectures TCN/GRU, les ablations de features, et la robustesse des modèles).

---

## 4. Structure Globale du Projet

L'organisation des répertoires a été simplifiée pour séparer proprement la recherche ML et les modules de l'application :
- **`backend/`** : Code serveur de l'annotateur, script Tkinter, et validateur de données.
- **`dashboard/`** : Ressources d'interface web (HTML, JavaScript, CSS).
- **`data/`** : Stockage local des vidéos de captures, index de manifestes, et fichiers d'annotations `.csv` / `.json`.
- **`jobs/`** : Lanceurs de scripts rapides `.bat` pour Windows.
- **`logs/`** : Sorties de logs d'exécution en arrière-plan.
- **`ml/`** & **`pipelines/`** : Scripts de recherche Machine Learning, TCN séquentiels, et évaluations de latence.
