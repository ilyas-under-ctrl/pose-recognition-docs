# Rapport académique - sécurité machine

Ce dossier contient la version française du rapport, les figures, les tables et les notebooks exécutés.

## Fichiers principaux

- `rapport_securite_machine.pdf`: version PDF à présenter.
- `rapport_securite_machine.tex`: source LaTeX française.
- `machine_safety_academic_report.pdf`: même contenu, gardé pour compatibilité avec le nom précédent.
- `report_metrics.json`: métriques extraites automatiquement depuis les résultats dans `runs/`.
- `notebooks/`: notebooks français déjà exécutés.

## Régénérer le paquet

Depuis la racine du projet:

```powershell
python build_academic_report_package.py
```

Le script est volontairement simple:

1. lire les CSV/JSON déjà produits par les expériences;
2. recalculer les métriques clés;
3. régénérer les figures;
4. écrire le rapport LaTeX;
5. écrire les notebooks français.

## Réexécuter les notebooks

Depuis la racine du projet:

```powershell
@'
from pathlib import Path
import nbformat
from nbclient import NotebookClient

folder = Path("academic_report/notebooks")
for path in sorted(folder.glob("*.ipynb")):
    nb = nbformat.read(path, as_version=4)
    nb.setdefault("metadata", {})["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    client = NotebookClient(
        nb,
        timeout=300,
        kernel_name="python3",
        resources={"metadata": {"path": str(folder.resolve())}},
    )
    client.execute()
    nbformat.write(nb, path)
    print(path.name)
'@ | python -
```

## Recompiler le PDF

Depuis `academic_report/`:

```powershell
pdflatex -interaction=nonstopmode rapport_securite_machine.tex
pdflatex -interaction=nonstopmode rapport_securite_machine.tex
```

## Interprétation courte

Le modèle principal retenu pour l'alerte est le TCN60 à sortie unique `risk_present_now`. Le signal `survival_gru_exact_entry / score_by_02` au seuil `0.95` est présenté comme signal court horizon pour l'arrêt automatique. Les modèles attention et blouse/PPE ne sont pas une fusion apprise avec le danger physique; ils modifient seulement la politique d'alerte.
