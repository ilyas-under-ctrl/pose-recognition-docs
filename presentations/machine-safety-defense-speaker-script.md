# Sécurité machine - Script de présentation

Durée cible: 12 à 14 minutes.

## Diapo 1 - Narratif de soutenance (0:45)
Dire: "Le projet ne consiste pas seulement à reconnaître qu'une frame est déjà dangereuse. L'objectif est de prédire le danger avant l'entrée physique. Avec une caméra fixe, on transforme la vidéo en signaux causaux pose-zone pour deux usages: prévenir le technicien et donner à la machine une courte marge pour initier l'arrêt."

Montrer: la mosaïque du dataset sur la diapo.

Transition: "Avant de parler des modèles, il faut clarifier le temps que l'on veut gagner."

## Diapo 2 - Cible opérationnelle (1:00)
Dire: "Nous séparons deux usages autour du même événement objectif, l'entrée physique. Le TCN sert l'alerte opérateur et peut accepter davantage de faux positifs pour gagner du temps. Le GRU exact-entry sert le stop court horizon, donc avec une logique plus stricte et plus tardive."

Montrer: `timing_budget.png`.

Transition: "Cette distinction est importante parce que le dataset ne se lit pas seulement avec le nombre d'événements."

## Diapo 3 - Réalité du dataset (1:00)
Dire: "Le graphique compte les vidéos parentes: 50 entrées, 13 presque-accidents et 9 clips sans danger. Mais au niveau des fenêtres temporelles, il y a beaucoup plus de temps sans danger. Il faut donc raconter le dataset correctement: il est petit, mais centré sur l'événement rare que l'on veut anticiper."

Montrer: `dataset_event_distribution.png`.

Transition: "Pour rendre ces labels utilisables, les noms de dossiers safe/unsafe ne suffisaient pas."

## Diapo 4 - Annotation comme méthode (1:30)
Dire: "Nous avons créé notre propre outil d'annotation parce que la cible est temporelle. L'outil enregistre le polygone 2D de danger, le début du risque visible, l'entrée physique, et les segments attention/blouse. L'entrée physique est l'événement objectif. Le début du risque est le repère humain: le moment où un expert peut déjà voir que la situation devient risquée."

Montrer: `annotation_tool_interface.png`; pointer la zone, le marqueur ambre de risque, le marqueur rouge d'entrée, et la ligne de segments.

Transition: "Ces annotations deviennent ensuite des variables structurées."

## Diapo 5 - Ingénierie des variables (1:20)
Dire: "Le modèle de danger ne part pas directement des pixels. On passe d'abord par YOLO pose, puis on calcule les distances entre les parties du corps et la zone dangereuse, les indicateurs dedans/dehors, la vitesse et l'accélération. Cela pousse le modèle à apprendre le mouvement vers la zone plutôt que l'identité de l'acteur ou le fond."

Montrer: `pipeline_policy_diagram.png`.

Transition: "Une fois la séquence structurée, nous utilisons un score d'alerte et un signal d'imminence."

## Diapo 6 - Architectures TCN et GRU (1:20)
Dire: "Le TCN porte l'alerte opérateur. Il lit une fenêtre causale de 60 pas avec 54 variables, projette vers 96 canaux, puis passe dans quatre blocs TCN résiduels dilatés avant de produire une seule sortie, risk_present_now. Le GRU exact-entry lit une fenêtre plus courte de 30 pas et sert à lire l'imminence d'arrêt avec le score_by_02, centré sur les horizons 0,2 et 0,3 seconde."

Montrer: la comparaison d'architecture.

Transition: "Comme le dataset est petit, l'évaluation doit être prudente."

## Diapo 7 - Robustesse de l'évaluation (1:00)
Dire: "Les splits sont faits par vidéo parente, donc les fenêtres voisines d'une même vidéo ne passent pas à la fois en train et test. Nous répétons aussi les splits avec différentes graines. Cela ne remplace pas un dataset plus grand, mais réduit la dépendance à une séparation chanceuse."

Montrer: le schéma des splits répétés.

Transition: "Avec cette évaluation, les résultats se lisent comme deux compromis distincts."

## Diapo 8 - Résultat principal (1:30)
Dire: "Pour l'alerte opérateur, le TCN retenu atteint 0.850 à 0,2 seconde et 0.642 à 0,3 seconde avec une précision de 0.859 et 1.574 fausse alerte par minute. Si l'on pousse le TCN plus agressivement, on gagne un peu à 0,3 seconde, mais le bruit monte fortement. Pour le stop court horizon, le GRU exact-entry atteint 0.708 de fiabilité à 0,2 seconde et 0.903 à 0,3 seconde au seuil strict 0.95."

Montrer: la diapo de résultats avec les deux compromis séparés.

Transition: "Ensuite, attention et blouse interviennent comme couche de politique, pas comme preuve du danger physique."

## Diapo 9 - Couche de politique (1:15)
Dire: "Attention et blouse/PPE ne remplacent pas le modèle de danger physique. Ils modifient la sensibilité de l'alerte. La formule augmente le score final quand le danger physique est déjà non nul et que le contexte humain devient moins favorable, par exemple attention distraite ou blouse non conforme."

Montrer: `attention_blouse_examples.png`.

Transition: "Le prototype fonctionne dans cette géométrie contrôlée, mais le déploiement demande davantage."

## Diapo 10 - Prudence déploiement (1:20)
Dire: "Le signal court horizon est prometteur, mais la zone actuelle reste une projection 2D. C'est acceptable pour ce prototype parce que la caméra et la machine sont fixes. Ce n'est pas suffisant pour un déploiement, car profondeur, occlusions et angle caméra changent la relation réelle entre le corps et le volume dangereux. Il faudra du multi-angle ou de la profondeur, plus une mesure complète de la chaîne d'arrêt jusqu'à l'action mécanique."

Montrer: `timing_budget.png`.

Transition: "La conclusion doit donc commencer par les gains, puis ouvrir sur ce qui reste à valider."

## Diapo 11 - Conclusion (0:50)
Dire: "Le gain principal est une chaîne complète: annotation, variables pose-zone, TCN d'alerte continue, GRU de stop imminent, couche de politique et raisonnement sur la latence. La suite est claire: plus d'acteurs, plus de vrais négatifs, plus de machines, multi-angle ou profondeur, test complet de latence et validation de sûreté."

Montrer: la diapo de synthèse.

Phrase finale: "C'est un prototype contrôlé avec un signal de sécurité utile; la suite est de prouver la robustesse hors scénario."

## Checklist des artefacts

- Ouvrir le deck PowerPoint: `machine-safety-defense-presentation.pptx`.
- Diapo 4: montrer l'interface d'annotation et expliquer pourquoi l'outil maison était nécessaire.
- Diapo 5: montrer le diagramme de pipeline pour relier annotation, variables et modèles.
- Diapo 8: montrer le compromis du TCN pour l'alerte et celui du GRU pour le stop; insister sur 0,2 s et 0,3 s.
- Diapo 9: montrer les crops attention/blouse et la formule de politique.
- Diapo 10: montrer le timing et rappeler la limite 2D ainsi que la suite multi-angle/profondeur.
