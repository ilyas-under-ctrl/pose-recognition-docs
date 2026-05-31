# Script oral - Soutenance sécurité machine

Durée cible: 10 à 12 minutes.

## 1. Introduction générale

Bonjour Monsieur, bonjour chers membres du jury.

Aujourd'hui, nous avons l'honneur de vous présenter notre projet de sécurité machine par vision fixe.

Ce projet porte sur une question simple en apparence, mais importante en pratique: peut-on utiliser une caméra fixe et un modèle vidéo causal pour anticiper l'entrée d'une partie du corps dans une zone dangereuse autour d'une machine?

L'idée centrale n'est pas seulement de reconnaître qu'une situation est déjà dangereuse. L'objectif est d'anticiper assez tôt pour donner soit une alerte utile à l'opérateur, soit une courte marge à la machine pour initier une chaîne d'arrêt.

Notre travail relie plusieurs dimensions: annotation experte, feature engineering pose-zone, modélisation séquentielle, politique d'alerte, et analyse de latence.

## 2. Contexte et problématique

Dans un environnement industriel, beaucoup de systèmes détectent un état déjà critique. Or, en sécurité, l'enjeu réel est de gagner du temps avant l'événement physique.

Dans notre cas, l'événement objectif est très clair: l'entrée physique d'une main, d'un bras ou d'une autre partie du corps dans le volume dangereux projeté autour de la machine.

Notre problématique de recherche est donc la suivante:

dans quelle mesure une caméra fixe, couplée à une modélisation causale de la vidéo, peut-elle détecter assez tôt un risque visible pour avertir un technicien, ou produire un signal suffisamment strict pour accompagner une logique d'arrêt court horizon?

Nous traitons cette question sous une contrainte forte: à chaque instant, le modèle ne reçoit que le passé vidéo disponible jusqu'à cet instant. Il n'y a donc aucune information future dans la prédiction.

## 3. Objectif opérationnel du système

Le système est organisé autour de deux niveaux de décision.

Le premier niveau est l'alerte opérateur. Ici, on cherche un signal suffisamment précoce pour prévenir l'humain, même si cela suppose de tolérer un peu plus de bruit.

Le deuxième niveau est le stop court horizon. Ici, la logique est différente: le signal doit être plus strict, plus tardif, et interprété comme un indicateur d'imminence de l'entrée physique.

Cette séparation est importante, car une alerte humaine et une logique d'arrêt automatique ne supportent pas le même compromis entre avance temporelle et faux déclenchements.

## 4. Données et annotations

Le dataset contient 72 vidéos parentes filmées dans une configuration contrôlée: même machine, même caméra fixe, et deux acteurs.

Les annotations finales distinguent des clips d'entrée physique, des presque-accidents et des clips sans danger.

Mais la valeur du dataset ne vient pas seulement du comptage des vidéos. Elle vient surtout de la structure temporelle que nous avons ajoutée.

En effet, nous avons développé notre propre outil d'annotation afin de stocker trois types d'information dans une même interface:

- le polygone de zone dangereuse,
- les segments attention et blouse ou PPE,
- et deux événements temporels distincts: le début du risque visible et l'entrée physique réelle.

L'entrée physique reste la vérité terrain principale, car c'est l'événement de sécurité objectif.

Le début du risque visible joue un autre rôle: il représente le moment où un technicien expérimenté ou un responsable sécurité peut raisonnablement dire que la situation devient crédiblement dangereuse avant l'entrée.

C'est ce repère qui nous permet de raisonner sur l'anticipation attendue d'un système d'alerte.

## 5. Pipeline et feature engineering

Le pipeline principal ne donne pas directement les pixels au modèle de danger.

Nous passons d'abord par YOLO pose afin d'extraire les points du corps. Ensuite, nous comparons ces points à la zone dangereuse annotée.

À partir de là, nous construisons des variables causales structurées:

- coordonnées normalisées,
- visibilité de la pose,
- distance signée à la zone,
- indicateur dedans ou dehors,
- vitesse,
- accélération.

Ce choix est une vraie étape de feature engineering.

Il pousse le modèle à apprendre une dynamique de rapprochement vers la zone dangereuse, plutôt qu'à mémoriser l'arrière-plan, l'acteur, ou des détails visuels peu robustes.

Cette représentation est aussi plus interprétable, ce qui est important dans un contexte sécurité.

## 6. Modélisation séquentielle

Le cœur du système repose sur deux modèles séquentiels, mais ils ne répondent pas au même niveau de décision.

Le premier est le TCN, qui porte l'alerte opérateur.

Il reçoit une fenêtre causale d'environ deux secondes, avec 60 pas temporels et 54 variables d'entrée. Il applique une projection convolutionnelle, puis plusieurs blocs TCN résiduels dilatés, avant de produire une seule sortie: `risk_present_now`.

Cette sortie ne veut pas dire "entrée dans 0,5 seconde" ou "entrée dans 1 seconde". Elle signifie simplement:

à cet instant, la dynamique pose-zone ressemble déjà à un risque visible.

Le deuxième modèle est le GRU exact-entry.

Celui-ci travaille sur une fenêtre plus courte et sur une question plus stricte. Il sert à lire l'imminence du danger à très court horizon, avec une attention particulière sur les horizons 0,2 et 0,3 seconde avant entrée.

Autrement dit, le TCN sert l'alerte continue, tandis que le GRU sert la lecture d'un stop imminent.

## 7. Protocole d'évaluation

Comme le dataset est petit, nous avons évité de fonder le projet sur une seule séparation train, validation, test.

Nous avons donc utilisé des splits répétés avec différentes graines, en gardant toujours l'étanchéité par vidéo parente.

Cette précaution est importante, car elle réduit la dépendance à un split chanceux et donne une lecture plus robuste des performances.

Les métriques ne sont pas uniquement des métriques de classification standard. Elles sont aussi temporelles.

Pour l'alerte opérateur, nous mesurons notamment:

- si l'alerte arrive au moins 0,2 seconde avant l'entrée,
- si elle arrive au moins 0,3 seconde avant l'entrée,
- la précision des alarmes,
- et le nombre de fausses alertes par minute.

Pour le stop court horizon, la logique est différente. Nous mesurons plutôt:

- la probabilité qu'une entrée survienne réellement dans 0,2 seconde après déclenchement,
- puis dans 0,3 seconde,
- ainsi que le temps moyen restant avant entrée lorsque le signal se déclenche.

## 8. Résultat principal sur l'alerte opérateur

Le résultat principal du projet est le TCN à sortie unique pour l'alerte opérateur.

Avec le seuil d'exploitation présenté dans le rapport, il atteint 0,850 de détection au moins 0,2 seconde avant l'entrée, et 0,642 à 0,3 seconde, avec une précision de 0,859 et 1,574 fausse alerte par minute.

Ce point est important, car il montre qu'un système purement causal, à partir d'une caméra fixe, peut fournir un signal utile avant l'événement physique.

Nous avons aussi étudié un seuil plus agressif. Il gagne légèrement en avance à 0,3 seconde, mais au prix d'une hausse nette du bruit.

Le message n'est donc pas que le modèle déclenche toujours très tôt, mais qu'il existe un compromis opérationnel crédible entre avance et stabilité.

À ce moment de la présentation, nous pouvons montrer une vidéo de démonstration où le score TCN franchit le seuil avant l'entrée physique, avec la zone dangereuse superposée.

## 9. Résultat principal sur le stop court horizon

Pour le stop court horizon, nous utilisons le GRU exact-entry.

Ici, la question n'est plus: "l'alerte est-elle utile pour un humain?"

La question devient:

quand le signal se déclenche, l'entrée physique est-elle réellement imminente?

Au seuil strict présenté dans le rapport, le GRU donne environ 0,708 de fiabilité à 0,2 seconde et 0,903 à 0,3 seconde.

Ce signal est trop tardif pour reposer sur une réaction humaine confortable, mais il devient intéressant comme base d'analyse pour une logique d'arrêt automatique.

Donc, dans notre lecture finale:

- le TCN est le modèle d'alerte opérateur,
- le GRU est le modèle d'imminence court horizon.

## 10. Couche de politique: attention et blouse / PPE

Nous avons également ajouté une couche de politique au-dessus du danger physique.

Cette couche utilise deux informations de contexte:

- l'attention,
- et l'état de la blouse ou du PPE.

Ces signaux ne remplacent pas le modèle de danger. Ils ne prétendent pas non plus prouver physiquement qu'une entrée va se produire.

Leur rôle est plus simple: augmenter la sensibilité de l'alerte quand le contexte humain devient moins favorable.

Par exemple, si l'opérateur regarde ailleurs ou porte mal sa blouse, le système peut devenir plus conservateur dans son déclenchement.

Cette partie donne une lecture plus réaliste de l'usage terrain, sans confondre danger physique et contexte humain.

À ce moment, nous pouvons montrer la vidéo annotée où l'opérateur est explicitement labellisé comme non attentif et blouse mal portée.

## 11. Limites et déploiement

Le projet reste un prototype académique.

La caméra est fixe, la machine est unique, le nombre d'acteurs est faible, et la zone dangereuse est représentée par une projection 2D.

Cette projection 2D est acceptable pour un prototype contrôlé, mais elle ne suffit pas pour un déploiement réel. En pratique, la profondeur, les occlusions et les changements d'angle caméra peuvent modifier la relation réelle entre le corps et le volume dangereux.

Un déploiement plus robuste demanderait donc:

- plus d'acteurs,
- plus de vrais négatifs,
- plusieurs machines,
- et idéalement du multi-angle ou de la profondeur.

Il faudrait aussi mesurer toute la chaîne de latence, depuis la capture vidéo jusqu'à l'action mécanique réelle.

## 12. Conclusion

Pour conclure, notre projet montre qu'il est possible de construire une chaîne complète de sécurité machine par vision fixe.

Cette chaîne comprend:

- un outil d'annotation dédié,
- une représentation causale pose-zone,
- un TCN pour l'alerte opérateur,
- un GRU pour le stop court horizon,
- une couche de politique avec attention et blouse,
- et une lecture temporelle des compromis entre anticipation, précision et bruit.

La valeur ajoutée du projet n'est donc pas seulement un modèle.

Elle réside dans l'intégration de l'annotation, de la modélisation, de la politique d'usage et du raisonnement opérationnel dans un même système cohérent.

Les prochaines étapes sont claires: enrichir le dataset, améliorer la robustesse géométrique, tester des configurations multi-angle, et valider la chaîne d'arrêt complète dans des conditions plus proches du réel.

Je vous remercie pour votre attention.

## Supports à montrer pendant l'oral

- [machine-safety-defense-presentation.pptx](C:/Users/ilyas/Desktop/pose%20recognision/presentations/machine-safety-defense-presentation.pptx)
- [attention_bad_blouse_demo.mp4](C:/Users/ilyas/Desktop/pose%20recognision/output/demo_videos/attention_bad_blouse_demo.mp4)
- [tcn_entry_prediction_demo.mp4](C:/Users/ilyas/Desktop/pose%20recognision/output/demo_videos/tcn_entry_prediction_demo.mp4)
- [rapport_securite_machine.pdf](C:/Users/ilyas/Desktop/pose%20recognision/academic_report/rapport_securite_machine.pdf)
