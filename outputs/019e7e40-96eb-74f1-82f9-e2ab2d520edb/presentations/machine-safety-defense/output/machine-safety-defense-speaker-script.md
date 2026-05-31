# SÃ©curitÃ© machine - Script de prÃ©sentation

DurÃ©e cible: 12 Ã  14 minutes.

## Diapo 1 - Narratif de soutenance (0:45)
Dire: "Le projet ne consiste pas seulement Ã  reconnaÃ®tre qu'une frame est dÃ©jÃ  dangereuse. L'objectif est de prÃ©dire le danger avant l'entrÃ©e physique. Avec une camÃ©ra fixe, on transforme la vidÃ©o en signaux causaux pose-zone pour deux usages: prÃ©venir le technicien et donner Ã  la machine une courte marge pour initier l'arrÃªt."

Montrer: la mosaÃ¯que du dataset sur la diapo.

Transition: "Avant de parler des modÃ¨les, il faut clarifier le temps que l'on veut gagner."

## Diapo 2 - Cible opÃ©rationnelle (1:00)
Dire: "Nous travaillons autour du mÃªme Ã©vÃ©nement objectif, l'entrÃ©e physique, avec deux niveaux de dÃ©cision. Le TCN sert l'alerte opÃ©rateur et peut accepter davantage de faux positifs pour gagner du temps. Le GRU exact-entry sert le stop court horizon, donc avec une logique plus stricte et plus tardive."

Montrer: `timing_budget.png`.

Transition: "Cette distinction est importante parce que le dataset ne se lit pas seulement avec le nombre d'Ã©vÃ©nements."

## Diapo 3 - RÃ©alitÃ© du dataset (1:00)
Dire: "Le graphique compte les vidÃ©os parentes: 50 entrÃ©es, 13 presque-accidents et 9 clips sans danger. Mais au niveau des fenÃªtres temporelles, il y a beaucoup plus de temps sans danger. Il faut donc raconter le dataset correctement: il est petit, mais centrÃ© sur l'Ã©vÃ©nement rare que l'on veut anticiper."

Montrer: `dataset_event_distribution.png`.

Transition: "Pour rendre ces labels utilisables, les noms de dossiers safe/unsafe ne suffisaient pas."

## Diapo 4 - Annotation comme mÃ©thode (1:30)
Dire: "Nous avons crÃ©Ã© notre propre outil d'annotation parce que la cible est temporelle. L'outil enregistre le polygone 2D de danger, le dÃ©but du risque visible, l'entrÃ©e physique, et les segments attention/blouse. L'entrÃ©e physique est l'Ã©vÃ©nement objectif. Le dÃ©but du risque est le repÃ¨re humain: le moment oÃ¹ un expert peut dÃ©jÃ  voir que la situation devient risquÃ©e."

Montrer: `annotation_tool_interface.png`; pointer la zone, le marqueur ambre de risque, le marqueur rouge d'entrÃ©e, et la ligne de segments.

Transition: "Ces annotations deviennent ensuite des variables structurÃ©es."

## Diapo 5 - IngÃ©nierie des variables (1:20)
Dire: "Le modÃ¨le de danger ne part pas directement des pixels. On passe d'abord par YOLO pose, puis on calcule les distances entre les parties du corps et la zone dangereuse, les indicateurs dedans/dehors, la vitesse et l'accÃ©lÃ©ration. Cela pousse le modÃ¨le Ã  apprendre le mouvement vers la zone plutÃ´t que l'identitÃ© de l'acteur ou le fond."

Montrer: `pipeline_policy_diagram.png`.

Transition: "Une fois la sÃ©quence structurÃ©e, nous utilisons un score d'alerte et un signal d'imminence."

## Diapo 6 - Architectures TCN et GRU (1:20)
Dire: "Le TCN porte l'alerte opÃ©rateur. Il lit une fenÃªtre causale de 60 pas avec 54 variables, projette vers 96 canaux, puis passe dans quatre blocs TCN rÃ©siduels dilatÃ©s avant de produire une seule sortie, risk_present_now. Le GRU exact-entry lit une fenÃªtre plus courte de 30 pas et sert Ã  lire l'imminence d'arrÃªt avec le score_by_02, centrÃ© sur les horizons 0,2 et 0,3 seconde."

Montrer: la comparaison d'architecture.

Transition: "Comme le dataset est petit, l'Ã©valuation doit Ãªtre prudente."

## Diapo 7 - Robustesse de l'Ã©valuation (1:00)
Dire: "Les splits sont faits par vidÃ©o parente, donc les fenÃªtres voisines d'une mÃªme vidÃ©o ne passent pas Ã  la fois en train et test. Nous rÃ©pÃ©tons aussi les splits avec diffÃ©rentes graines. Cela ne remplace pas un dataset plus grand, mais rÃ©duit la dÃ©pendance Ã  une sÃ©paration chanceuse."

Montrer: le schÃ©ma des splits rÃ©pÃ©tÃ©s.

Transition: "Avec cette Ã©valuation, les rÃ©sultats se lisent comme deux compromis distincts."

## Diapo 8 - RÃ©sultat principal (1:30)
Dire: "Pour l'alerte opÃ©rateur, le TCN au seuil 0.55 atteint 0.850 Ã  0,2 seconde et 0.642 Ã  0,3 seconde avec une prÃ©cision de 0.859 et 1.574 fausse alerte par minute. Au seuil 0.35, on gagne un peu Ã  0,3 seconde, mais le bruit monte fortement. Pour le stop court horizon, le GRU exact-entry atteint 0.708 de fiabilitÃ© Ã  0,2 seconde et 0.903 Ã  0,3 seconde au seuil strict 0.95."

Montrer: la diapo de rÃ©sultats avec les deux compromis sÃ©parÃ©s.

Transition: "Ensuite, attention et blouse interviennent comme couche de politique, pas comme preuve du danger physique."

## Diapo 9 - Couche de politique (1:15)
Dire: "Attention et blouse/PPE ne remplacent pas le modÃ¨le de danger physique. Ils modifient la sensibilitÃ© de l'alerte. La formule augmente le score final quand le danger physique est dÃ©jÃ  non nul et que le contexte humain devient moins favorable, par exemple attention distraite ou blouse non conforme."

Montrer: `attention_blouse_examples.png`.

Transition: "Le prototype fonctionne dans cette gÃ©omÃ©trie contrÃ´lÃ©e, mais le dÃ©ploiement demande davantage."

## Diapo 10 - Prudence dÃ©ploiement (1:20)
Dire: "Le signal court horizon est prometteur, mais la zone actuelle reste une projection 2D. C'est acceptable pour ce prototype parce que la camÃ©ra et la machine sont fixes. Ce n'est pas suffisant pour un dÃ©ploiement, car profondeur, occlusions et angle camÃ©ra changent la relation rÃ©elle entre le corps et le volume dangereux. Il faudra du multi-angle ou de la profondeur, plus une mesure complÃ¨te de la chaÃ®ne d'arrÃªt jusqu'Ã  l'action mÃ©canique."

Montrer: `timing_budget.png`.

Transition: "La conclusion doit donc commencer par les gains, puis ouvrir sur ce qui reste Ã  valider."

## Diapo 11 - Conclusion (0:50)
Dire: "Le gain principal est une chaÃ®ne complÃ¨te: annotation, variables pose-zone, TCN d'alerte continue, GRU de stop imminent, couche de politique et raisonnement sur la latence. La suite est claire: plus d'acteurs, plus de vrais nÃ©gatifs, plus de machines, multi-angle ou profondeur, test complet de latence et validation de sÃ»retÃ©."

Montrer: la diapo de synthÃ¨se.

Phrase finale: "C'est un prototype contrÃ´lÃ© avec un signal de sÃ©curitÃ© utile; la suite est de prouver la robustesse hors scÃ©nario."

## Checklist des artefacts

- Ouvrir le deck PowerPoint: `machine-safety-defense-presentation.pptx`.
- Diapo 4: montrer l'interface d'annotation et expliquer pourquoi l'outil maison Ã©tait nÃ©cessaire.
- Diapo 5: montrer le diagramme de pipeline pour relier annotation, variables et modÃ¨les.
- Diapo 8: montrer le compromis du TCN pour l'alerte et celui du GRU pour le stop; insister sur 0,2 s et 0,3 s.
- Diapo 9: montrer les crops attention/blouse et la formule de politique.
- Diapo 10: montrer le timing et rappeler la limite 2D ainsi que la suite multi-angle/profondeur.

