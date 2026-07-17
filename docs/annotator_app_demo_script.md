# Script de demo de l'application d'annotation

Ce script correspond a l'annotateur web actuel dans :

`dashboard/web_annotator/`

Il est prevu pour une **demo en direct** ou pour une **video de presentation**.  
Chaque section indique :
- ce qu'il faut faire a l'ecran
- ce qu'il faut dire

---

## 1. Introduction

### A l'ecran
- Lancer le serveur :

```powershell
python backend/web_annotator_server.py
```

- Ouvrir :

```text
http://127.0.0.1:8765
```

- Garder la vue generale de l'application.

### A dire

"Ici, nous montrons notre outil d'annotation pour le projet de securite machine."

"Nous l'avons developpe nous-memes parce que notre probleme ne se limite pas a poser des labels generiques sur des images. Nous avons besoin d'annotations temporelles precises, de segments, d'evenements exacts, et d'une zone de danger definie directement sur la scene."

"L'interface web est notre interface principale. Elle permet la lecture video native, l'edition sur timeline, la superposition de la zone dangereuse, et l'enregistrement direct des annotations dans les fichiers utilises ensuite par le pipeline."

---

## 2. La file d'annotation

### A l'ecran
- Pointer la colonne **Annotation Queue**.
- Montrer le texte de progression.
- Utiliser la barre de recherche.
- Tester le filtre :
  - `All`
  - `Safe`
  - `Unsafe`
  - `Needs review`
  - `Reviewed`
- Montrer la legende :
  - `reviewed`
  - `E`
  - `S`
  - `untouched`
- Cliquer sur quelques clips.
- Utiliser `P Prev` et `N Next`.

### A dire

"A gauche, nous avons la file d'annotation. C'est ici que nous organisons le travail sur l'ensemble du dataset."

"Nous pouvons rechercher par acteur, nom de fichier ou mot-cle, puis filtrer rapidement les clips safe, unsafe, a revoir ou deja finalises."

"L'etat de chaque clip est visible directement dans la liste. Cela permet de voir si un clip est complet, partiel, ou encore vierge. C'est tres utile pour reprendre une session sans perdre le contexte."

"La navigation est aussi pensee pour aller vite : soit on clique directement dans la liste, soit on avance clip par clip avec les boutons precedent et suivant."

---

## 3. L'espace video et les controles

### A l'ecran
- Ouvrir un clip.
- Montrer :
  - la video
  - l'overlay de zone
  - le scrubber
  - la timeline
  - les controles de transport
  - le temps courant
- Utiliser :
  - `Space Play`
  - `< Frame`
  - `Frame >`
  - `-1 sec`
  - `+1 sec`
- Changer la vitesse.
- Cocher et decocher `Auto-next`.

### A dire

"Au centre, nous avons l'espace principal d'annotation. La video est affichee avec un calque par-dessus, ce qui nous permet de dessiner et de corriger la zone de danger directement sur l'image."

"Sous la video, nous avons deux niveaux de navigation temporelle. Le premier permet de se deplacer globalement dans le clip. Le second, la timeline, fonctionne davantage comme un petit editeur video pour les annotations."

"Les controles permettent la lecture normale, l'avance image par image, les sauts d'une seconde, le changement de vitesse, et le passage automatique au clip suivant. Cela permet d'alterner entre revue rapide et annotation tres precise."

---

## 4. Preparation du cache et revue rapide

### A l'ecran
- Pointer la ligne de statut du cache.
- Cliquer sur `Prepare All Clips`.
- Filtrer sur `Unsafe`.
- Cliquer sur `F Zone Review`.
- Laisser tourner un instant a `8x`, puis arreter.

### A dire

"Comme certaines videos d'origine ne sont pas ideales pour une lecture navigateur, l'outil peut preparer une version cachee lisible rapidement par le navigateur. Cela ameliore fortement l'ouverture des clips et surtout le seeking."

"Nous avons aussi un mode de revue rapide. Avec `Zone Review`, on peut parcourir les clips filtres a haute vitesse, en general a huit fois la vitesse normale, avec passage automatique au clip suivant."

"C'est pratique pour comprendre rapidement la scene, repeter la geometrie de danger, et reperer les clips interessants avant d'entrer dans une annotation fine."

---

## 5. Definition de la zone dangereuse

### A l'ecran
- Mettre la video en pause sur une frame claire.
- Cliquer sur `Z Edit Zone`.
- Poser plusieurs points autour de la zone machine.
- Deplacer un point.
- Ajouter un point.
- Supprimer un point avec clic droit.
- Cliquer sur `Ctrl+S Save Zone`.

### A dire

"Une fonctionnalite centrale de l'outil est la definition manuelle de la zone de danger. Nous dessinons un polygone projete en 2D autour de la zone machine dangereuse visible dans la camera."

"Ce n'est pas une reconstruction 3D complete, et nous ne le presentons pas comme tel. Pour ce prototype, c'est une reference pratique et coherente qui relie l'annotation humaine aux features pose-zone utilises ensuite par les modeles."

"L'edition est interactive : on peut ajouter des sommets, les deplacer, corriger la forme, retirer un point, puis sauvegarder la zone finale."

---

## 6. Labels de clip : attention et blouse

### A l'ecran
- Pointer le bloc **Clip Labels**.
- Basculer entre :
  - `A attentive`
  - `D distracted`
- Basculer entre :
  - `R proper`
  - `B bad`
- Montrer un clip simple.
- Cliquer sur `W Whole Clip`.

### A dire

"Le premier niveau d'annotation concerne l'etat du clip : l'attention et la blouse, ou plus largement le contexte PPE."

"Ces labels ne remplacent pas la cible principale de danger physique. Ils servent de contexte complementaire pour la couche de politique."

"Quand un etat reste constant sur tout le clip, le workflow est tres simple : on choisit l'etat d'attention, on choisit l'etat de blouse, puis on enregistre un segment sur tout le clip en une seule action."

---

## 7. Annotation par segment

### A l'ecran
- Se placer a un instant.
- Cliquer sur `S Start Segment`.
- Avancer un peu.
- Cliquer sur `E End + Save`.
- Montrer le segment sur la timeline.

### A dire

"Quand le label change au cours du clip, nous n'utilisons plus un segment global. Nous passons a une annotation temporelle partielle."

"Le principe est simple : on fixe le debut, on avance jusqu'a la fin de l'etat, puis on sauvegarde."

"Une fois le segment enregistre, il apparait directement sur la timeline. Cela donne un retour visuel immediat et rend la correction beaucoup plus simple."

---

## 8. Evenements de danger

### A l'ecran
- Pointer le bloc **Danger Event**.
- Montrer :
  - `M physical entry`
  - `O risk onset`
  - les sources
  - le spatial
  - le type d'evenement
  - le champ de note
- Choisir :
  - `risk_onset`
  - `hand_or_arm`
  - un `Spatial`
- Marquer `O Risk Onset`.
- Avancer jusqu'a l'entree reelle.
- Marquer `M Physical Entry`.
- Montrer les pins sur la timeline.

### A dire

"Le panneau d'evenement sert a poser des timestamps exacts. C'est ici que nous enregistrons les deux instants les plus importants du clip."

"Le premier est le `risk onset`, c'est-a-dire le premier moment ou le risque devient visiblement credible. Le second est la `physical entry`, c'est-a-dire la frame exacte ou une partie du corps entre effectivement dans la zone dangereuse."

"Nous enregistrons aussi la source du danger, comme main ou bras, la relation spatiale, le type d'evenement, et une note en cas d'ambiguite."

"Ces deux instants sont centraux pour toute la suite du projet. L'entree physique est la verite terrain dure. Le risk onset represente le moment visible plus tot, utile pour raisonner sur l'anticipation."

---

## 9. Edition directe sur la timeline

### A l'ecran
- Cliquer sur la timeline pour changer de temps.
- Faire glisser le pin rouge.
- Faire glisser le pin ambre si disponible.
- Montrer la ligne bleue du curseur courant.

### A dire

"La timeline ne sert pas seulement a afficher. Elle sert aussi a corriger."

"La ligne bleue indique la position courante. Les barres montrent les segments, et les pins colores montrent les evenements exacts."

"Si un timestamp est legerement decale, il n'est pas necessaire de refaire l'annotation. On peut simplement faire glisser le pin pour corriger directement l'instant exact."

"C'est un gain de temps important, surtout quand on travaille a l'image pres."

---

## 10. Workflow d'un clip safe

### A l'ecran
- Ouvrir un clip safe.
- Choisir attention et blouse.
- Cliquer sur `W Whole Clip`.
- Cliquer sur `G No Danger`.
- Montrer le resume sauvegarde.

### A dire

"Pour un clip safe, le workflow est volontairement court. Nous annotons les labels de contexte, nous enregistrons le segment, puis nous marquons `No Danger`."

"Cela permet d'avoir de vrais exemples negatifs explicites, et pas seulement l'absence d'annotation. C'est important pour la qualite du dataset et pour l'evaluation des modeles."

---

## 11. Notes, resume, et etats partiels

### A l'ecran
- Entrer une note courte :
  - `occlusion`
  - `above projection`
  - `unclear source`
- Pointer le bloc **Saved annotations for this video**.
- Montrer si possible un clip partiellement annote.

### A dire

"Le champ de note sert uniquement aux cas ambigus, par exemple une occlusion, une projection peu claire, ou une source de danger incertaine."

"En bas, l'outil affiche un resume de ce qui est deja enregistre pour la video courante. Cela permet de verifier rapidement l'etat de la video avant de passer a la suite."

"La meme logique apparait dans la file d'annotation, avec les etats partiels qui montrent ce qui manque encore."

---

## 12. Annuler et reinitialiser

### A l'ecran
- Cliquer sur `Undo Event`.
- Cliquer sur `Undo Segment`.
- Si pertinent, montrer `X Reset Clip`.

### A dire

"Comme l'annotation est manuelle, les outils de correction sont indispensables. On peut annuler le dernier evenement, annuler le dernier segment, ou reinitialiser completement le clip courant."

"Cela evite toute edition manuelle des fichiers CSV juste pour corriger une petite erreur."

---

## 13. Raccourcis clavier

### A l'ecran
- Pointer le panneau **Shortcuts**.
- Demontrer quelques touches :
  - `Space`
  - fleches
  - `A`, `D`, `R`, `B`
  - `S`, `E`, `W`
  - `M`, `O`, `G`
  - `Z`

### A dire

"L'outil est aussi pense pour un usage clavier. Les actions les plus frequentes ont des raccourcis : lecture, deplacement frame par frame, navigation entre clips, choix des labels, sauvegarde des segments, marquage des evenements, no danger, et edition de la zone."

"C'est important parce qu'une session d'annotation longue est repetitive. Le clavier reduit les manipulations inutiles et accelere fortement le travail."

---

## 14. Fichiers de sortie et validation

### A l'ecran
- Mentionner :
  - `data/annotations/videos.csv`
  - `data/annotations/segments.csv`
  - `data/annotations/events.csv`
  - `data/annotations/zones.json`
- Montrer ou citer :

```powershell
python backend/validate_annotations.py
```

### A dire

"Toutes les annotations sont enregistrees dans des fichiers simples et auditables : les videos, les segments, les evenements, et les zones."

"Apres une session, nous pouvons lancer la validation automatique. Elle verifie la coherence temporelle, la validite des labels, les bornes des segments, les frames d'evenement, et la forme de la zone."

"Cela garantit que la suite du pipeline travaille sur des annotations propres."

---

## 15. Conclusion

### A l'ecran
- Revenir a la vue generale de l'interface.
- Laisser un clip annote visible si possible.

### A dire

"La valeur principale de cet outil est qu'il transforme des videos brutes en annotations structurees qui correspondent directement a notre probleme de securite."

"Il gere la file de revue, la lecture rapide, l'edition de zone, les segments, les evenements exacts, la correction sur timeline, les labels de contexte, l'annulation, et l'export vers les fichiers utilises ensuite par le pipeline."

"Autrement dit, nous n'avons pas construit une interface de labeling generique. Nous avons construit un environnement d'annotation adapte a une analyse causale du risque machine."

---

## Version courte 90 secondes

"Voici notre application d'annotation pour le projet de securite machine. A gauche, nous gerons la file des videos avec recherche, filtres, progression et etats de revue. Au centre, nous avons l'espace video avec lecture, avance image par image, revue rapide, timeline et superposition de la zone de danger. Nous pouvons dessiner manuellement la zone machine, annoter l'attention et la blouse sur tout le clip ou sur des segments partiels, puis marquer deux instants exacts : le debut du risque visible et l'entree physique reelle. Ces evenements apparaissent ensuite comme des pins sur la timeline et peuvent etre corriges par glisser-deposer. L'outil gere aussi les clips safe, les notes d'ambiguite, les raccourcis clavier, l'annulation, la reinitialisation, et l'export vers des fichiers CSV et JSON valides. En bref, c'est un outil d'annotation concu specifiquement pour notre probleme de securite et pas une interface generique."
