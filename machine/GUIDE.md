# Machine à shorts GTA 6 — guide de production

## 0. RÈGLES EN VIGUEUR DEPUIS LE 18.11.2026 (prioritaires sur tout le reste du guide)
Stats du 18.11 : mème « Toi demain matin au boulot » (11 s) = 52,8 % d'abandon (mieux que la moyenne), 0,9 % de J'aime ;
news « Pas sorti, déjà jeu de l'année » (15 s) = 60 % d'abandon, 3 s de vue moyenne. 0 partage partout :
« Envoie ça à ton pote » ne marche pas. On perd ~50 % des gens dans les 3 premières secondes => problème VISUEL (fond calme).
- **Durée : 8 à 12 s.** 4 à 6 segments. Supprimer le segment « ENVOIE À UN POTE ».
- **Format principal (4 vidéos sur 6) : mèmes « Toi quand… » / situations de joueur.** Les news sont racontées sous cet angle
  (« Toi quand tu apprends que… »), avec le fait exact.
- **Appel à l'action = commentaire ou tag**, jamais « envoie à un pote » : question binaire à la fin (« Congé ou malade ? »)
  ou « Tague ton pote qui… » (tag « TAGUE-LE »). Le texte du post finit par la question + « 👇 ».
- **Première seconde** : make_short.py fait déjà flash, zoom « punch », tremblement, accroche qui « claque » et un nouveau plan
  toutes les 1,7 s (clips classés par mouvement, broll/MOTION.json). Garder l'accroche ≤ 7 mots.
- **Visage humain sur l'accroche** : `"face": "<mot-clé>"` (shocked, laughing, celebrating, tired, alarm, phone, gamer, disappointed…)
  prend une vraie réaction humaine libre de droits dans broll/faces/ (télécharger : `python3 fetch_broll.py 2 faces`,
  puis planche contact et suppression des clips hors sujet, d'animaux, d'enfants ou montrant l'écran d'un autre jeu).
  `"opener": "<mot-clé>"` (fireworks, drift, police, neon…) choisit le 1er plan dans broll/INDEX.txt.
- **Format « conversation »** (très partageable) : `"voice": "none"`, segments avec `"chat": [["lui"|"moi", "texte"]]` et `"dur"`
  (≈1,4-1,9 s par message), `"chat_name": "Kevin"` ; 1er segment = accroche en caption, dernier = caption « *Tague* ton Kevin ».
  Exemple : machine/scripts/2026-11-18_2_nuit-blanche_v3.json. Pas d'emoji dans les textes (police).
- **Mode sans voix** : `"voice": "none"` + `"dur"` par segment ; texte + musique uniquement.
- **Tests A/B automatiques chaque jour** : sur 6 vidéos, au moins 2 sans voix (dont 1 conversation), au moins 3 avec visage.
  Noter dans veille/AAAA-MM-JJ.md la variante de chaque vidéo (voix/sans voix, visage/pas, format). Le lendemain, comparer
  abandon 3 s, durée de vue et J'aime par variante et écrire le gagnant dans §3.
- **Story automatique** : chaque Reel est aussi publié en story Instagram 3 min après (même vidéo, sans texte).
- **Couverture** : `videoCoverMilliseconds: 700` (évite l'image du flash).

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
### Algorithme des Reels (recherche du 18.11.2026, sources : déclarations d'Adam Mosseri, Buffer, Metricool, SocialPilot)
- Les 3 signaux n°1 confirmés : **durée de visionnage** (y compris revisionnages), **partages en message privé par personne touchée**, **J'aime par personne touchée**. Les partages comptent le plus pour toucher des non-abonnés (notre cas : 100 % non-abonnés au début) et plus que les commentaires.
- **Le 1er test se joue sur 1,5-3 s** : jusqu'à la moitié des gens partent avant 3 s. Accroche à la fois écrite ET dite dès la 1re seconde, image qui bouge dès la 1re seconde (jamais d'écran fixe ou noir), pas de silence.
- **Boucle** : la dernière phrase doit renvoyer à l'accroche (ex. accroche « Ton sommeil est annulé » → fin « …alors, tu dors ou pas ? ») pour que la vidéo se relance naturellement et compte des revisionnages.
- **S'arrêter dès que l'idée est livrée** : pas de phrase de remplissage. 12-18 s reste notre cible (le créneau 15-30 s est donné comme le meilleur en général ; nos stats montrent ~8 s de visionnage moyen).
- **Originalité** : Instagram pénalise les reposts et filigranes (jusqu'à exclure des recommandations les comptes qui republient) et favorise le contenu original. Nos vidéos sont originales (voix, texte, montage), garder 100 % de création propre ; ne jamais reposter une vidéo d'ailleurs.
- **Description** : 1re ligne = la même accroche que la vidéo, avec les mots-clés que les gens tapent (« GTA 6 », « date de sortie », « astuces GTA 6 ») ; 3 à 7 hashtags ciblés ; remplir mediaAltText (Metricool) avec une phrase descriptive contenant les mots-clés (aide la recherche Instagram).
- **Rester dans la niche GTA 6** : la cohérence du compte aide l'algorithme à savoir à qui montrer nos Reels.
- Programmer via Metricool ne nuit pas à la portée (Mosseri programme lui-même ses posts).
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
