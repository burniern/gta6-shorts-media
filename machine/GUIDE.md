# Machine à shorts GTA 6 — guide de production

## 1. Veille virale (chaque jour, AVANT d'écrire)
Budget vidIQ : 150 crédits/mois, donc ~5 crédits par jour maximum.
- Appeler `vidiq_instagram_tiktok_outlier_search` (5 crédits) avec query « GTA 6 » (ou le sujet chaud du jour),
  audienceQuery `Culture/Region: French-speaking (France, Switzerland, Belgium, Quebec); Global: true; Demographics: gamers 14-30;`,
  resultsPerPlatform 6, datePostedAfter = il y a 3 jours.
- Lire pour chaque résultat : hook_0_3s, format.template, execution, audio. Retenir les 2 schémas qui reviennent le plus.
- Écrire 3 lignes dans `veille/AAAA-MM-JJ.md` (repo) : schémas repérés + lien des 2 meilleurs exemples.
- Au moins 2 des 3 vidéos du jour REPRENNENT un schéma repéré (structure, accroche, rythme), avec nos propres visuels et nos propres faits vérifiés. On copie la recette, jamais le contenu.
- `vidiq_watch_shortform_content` (10 crédits) seulement si un format totalement nouveau explose (max 1 par semaine).

## 2. Recettes virales déjà identifiées (analyse vidIQ du 17.11.2026)
Points communs des Reels GTA 6 qui ont fait 30 à 100x la moyenne de leur compte :
- **Un nouvel élément à l'écran toutes les 0,8 à 1,5 s** (sous-titre, chiffre, étiquette). make_short.py le fait : sous-titres mot à mot, gros chiffre « big », étiquette « tag ». => phrases COURTES (6-12 mots), 5 à 7 segments (voir §3).
- **Un effet sonore sur chaque apparition** (fait automatiquement : whoosh/impact/pop).
- **Accroche paradoxale ou choc dans la 1re seconde**, puis relance, puis chute qui contredit le début, puis question binaire.
- **La musique se coupe avant la question finale** (fait automatiquement).
Concepts qui marchent (à adapter, pas à copier mot pour mot) :
- « Coup de vieux » : un bébé né à la sortie de GTA 5 (17.09.2013) a 13 ans et n'a pas l'âge légal (18 ans) pour GTA 6 ; liste de repères depuis 2013 (vrais faits uniquement) ; CTA « T'avais quel âge en 2013 ? ».
- Effet domino : « Dans GTA 6, une mission pourrait te prendre 2 heures... et voilà pourquoi » (enchaînement d'événements possibles, présenté comme un scénario).
- Décompte / décomposition chiffrée avec « big » qui change à chaque segment.
- Mème hyperbolique court (8-12 s) : texte solennel + chute en un mot (« Littéralement. »). Ex. : le 19 novembre est aussi la Journée internationale des hommes.
- Comparatifs GTA 5 / GTA 6 ; « 5 choses à faire le jour 1 » ; « 5 changements » ; « ce que GTA 6 corrige ».
- Pousser le PARTAGE : « Envoie ça à ton pote qui... » (les partages en message privé sont le signal n°1 d'Instagram).

## 3. Règles de viralité
### Leçons des statistiques réelles du compte (17.11.2026, 4 Reels, ~560 vues)
- Durée de vue moyenne ~8 s sur des vidéos de 20-30 s => vidéos de **12 à 18 s**, **5 à 7 segments**.
- 0 partage / 0 commentaire / 0 enregistrement : l'appel au partage dans la description ne suffit pas.
  => **Segment 2 ou 3 (avant la 6e seconde) = appel au partage DANS la vidéo** : say « Envoie ça à ton pote qui ... », tag « ENVOIE À UN POTE ». Le pote visé doit être drôle et précis (« ton pote qui dit qu'il finit GTA 6 en un week-end »).
  => La question finale doit tenir dans les 12 premières secondes.
- Meilleur Reel (189 vues, 45,9 % d'abandon, 2,9 % de J'aime) : « 1 h par soir = fini en février » => accroche qui parle au spectateur + calcul concret qui le concerne. **Accroches en « tu / ta / ton »** : « Si tu… », « Ta PS5… », « Ton pote… ».
- Segment 1 = accroche COMPLÈTE dans "caption" (affichée en grand sur la 1re image, qui sert de couverture ; pas de sous-titres mot à mot sur ce segment). Courte (≤ 7 mots), choc, compréhensible sans le son.
- Privilégier les sujets qu'on envoie à un pote : mèmes de joueur, défis, « toi vs ton pote », calculs persos.
- (18.11) Mise en page : textes dans la zone sûre (largeur 840 px, décalés à gauche des boutons Instagram) ; "big" ≤ 8 caractères de préférence (réduit automatiquement sinon) ; sous-titres coupés par groupes de sens.
### Règles générales
- Segment 1 = accroche (jamais d'intro). Dernier segment = question binaire.
- "big" = un chiffre ou un mot fort (pas d'emoji). "tag" = étiquette de contexte. "caption" = idée clé, *mots dorés*.
- Texte du post : 1 phrase de curiosité + appel au partage + 4 à 6 hashtags (#GTA6 #GTAVI #gaming #jeuxvideo ...).

## 4. Règles éditoriales (non négociables)
- Français, énergique, tutoiement. Faits vrais et sourcés uniquement ; rumeur = « selon une rumeur ».
- AUCUNE image, vidéo, logo ou musique de Rockstar / GTA ni d'autres créateurs. Visuels = make_short.py + clips Pixabay (broll/) ; musique = music/ (générée, libre de droits).
- Éviter les noms anglais difficiles (dire « l'éditeur » plutôt que Take-Two). Ne pas écrire « GTA 5 » ET « GTA 6 » dans la même phrase lue (la voix confond parfois) : dire « l'ancien épisode ».
- Chiffres en lettres dans "say", en chiffres dans "caption"/"big".

## 5. Format d'un script (machine/scripts/AAAA-MM-JJ_N_sujet.json)
{"voice": "chatterbox:none", "broll": true, "segments": [
  {"say": "texte lu", "caption": "idée clé, *mots dorés*", "big": "gros chiffre (option)", "tag": "étiquette (option)"}
]}

## 6. Production
    bash setup.sh                                  # ~5-10 min
    PIXABAY_KEY=... python3 fetch_broll.py 2       # fonds Pixabay ; vérifier la planche contact, supprimer les clips hors sujet ou avec une personne reconnaissable
    python3 make_short.py scripts/X.json out/X.mp4 # 10-20 min par vidéo (contrôle qualité voix inclus, cache par phrase)
« ATTENTION phrase N reste douteuse » => simplifier la phrase et relancer.
Puis transcrire la vidéo finale (faster-whisper) et vérifier qu'aucun fait n'est déformé.

## 7. Voix
Voix C = voix par défaut de Chatterbox (chatterbox:none), choisie par l'utilisateur.
