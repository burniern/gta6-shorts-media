#!/usr/bin/env python3
"""Génère un short vertical 1080x1920 à partir d'un script JSON.

Usage: python3 make_short.py script.json sortie.mp4

Format du JSON :
{
  "voice": "voices/fr_FR-tom-medium.onnx",
  "segments": [
    {"say": "texte lu par la voix",
     "caption": "sous-titre affiché (mot clé entre *étoiles* = doré)",
     "big": "gros chiffre ou titre (optionnel)",
     "tag": "petite étiquette au-dessus (optionnel)"}
  ]
}
"""
import json, os, re, subprocess, sys, tempfile, wave, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BG1, BG2 = (28, 17, 38), (45, 24, 58)
GOLD, WHITE, PINK = (236, 186, 64), (255, 255, 255), (232, 72, 140)
import glob as _g
F_BLACK = next(iter(_g.glob("/usr/share/fonts/**/InterDisplay-Black.otf", recursive=True)
                    + _g.glob("/usr/share/fonts/**/DejaVuSans-Bold.ttf", recursive=True)), None)
F_SERIF = next(iter(_g.glob("/usr/share/fonts/**/DejaVuSerif-Bold.ttf", recursive=True)), F_BLACK)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def font(path, size):
    return ImageFont.truetype(path, size)


def background():
    im = Image.new("RGB", (W, H), BG1)
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        c = tuple(int(BG1[i] + (BG2[i] - BG1[i]) * math.sin(t * math.pi)) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    # grille de points discrète
    for x in range(0, W, 54):
        for y in range(0, H, 54):
            d.point((x, y), fill=(70, 50, 85))
    return im


_SW_CACHE = {}


def synthwave(k):
    """Fond animé original « coucher de soleil néon » (boucle de 60 images)."""
    k = k % 60
    if k in _SW_CACHE:
        return _SW_CACHE[k]
    if "sky" not in _SW_CACHE:
        sky = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(sky)
        hz = 1250
        top, mid = (20, 6, 40), (190, 40, 120)
        for y in range(hz):
            t = (y / hz) ** 1.6
            d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (mid[i] - top[i]) * t) for i in range(3)))
        for y in range(hz, H):
            d.line([(0, y), (W, y)], fill=(16, 4, 30))
        # soleil à bandes
        sun = Image.new("RGBA", (W, H))
        sdr = ImageDraw.Draw(sun)
        cx, cy, r = W // 2, 1050, 330
        for y in range(cy - r, hz):
            t = (y - (cy - r)) / (2 * r)
            c = (255, int(220 - 150 * t), int(90 + 40 * t), 255)
            half = int(math.sqrt(max(0, r * r - (y - cy) ** 2)))
            band = y > cy - 40 and ((y - cy) // 14) % 3 == 0
            if not band:
                sdr.line([(cx - half, y), (cx + half, y)], fill=c)
        glow = sun.filter(ImageFilter.GaussianBlur(40))
        sky = Image.alpha_composite(Image.alpha_composite(sky.convert("RGBA"), glow), sun)
        # silhouettes de palmiers (formes simples, dessin original)
        d = ImageDraw.Draw(sky)
        for px, ph, lean in [(110, 620, 40), (960, 700, -50), (860, 480, -25)]:
            base_y = hz
            d.line([(px, base_y), (px + lean, base_y - ph)], fill=(12, 2, 22), width=26)
            tx, ty = px + lean, base_y - ph
            for ang in (-160, -130, -100, -70, -40, -10, 20, 200):
                a = math.radians(ang)
                L = 230
                pts = []
                for j in range(9):  # feuille qui retombe (courbe), épaisse au milieu
                    u = j / 8
                    x = tx + L * u * math.cos(a)
                    y = ty + L * u * math.sin(a) * 0.5 + 120 * u * u
                    pts.append((x, y))
                for j in range(len(pts) - 1):
                    w = int(26 * math.sin(math.pi * (j + 0.5) / 8)) + 4
                    d.line([pts[j], pts[j + 1]], fill=(12, 2, 22), width=w)
            d.ellipse([tx - 22, ty - 18, tx + 22, ty + 18], fill=(12, 2, 22))
        _SW_CACHE["sky"] = sky.convert("RGB")
    im = _SW_CACHE["sky"].copy()
    d = ImageDraw.Draw(im)
    hz, cx = 1250, W // 2
    off = k / 60
    for i in range(14):  # lignes horizontales qui avancent
        z = (i + off) / 14
        y = hz + int((H - hz) * z ** 2.2)
        d.line([(0, y), (W, y)], fill=(255, 60, 200), width=3)
    for i in range(-12, 13):  # lignes de fuite
        d.line([(cx + i * 30, hz), (cx + i * 260, H)], fill=(255, 60, 200), width=3)
    # voile sombre au centre pour la lisibilité
    shade = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(shade)
    for y in range(500, 1500, 4):
        a = int(140 * math.exp(-((y - 1050) / 330) ** 2))
        sd.rectangle([0, y, W, y + 4], fill=(10, 2, 20, a))
    im = Image.alpha_composite(im.convert("RGBA"), shade).convert("RGB")
    _SW_CACHE[k] = im
    return im


def wrap(draw, text, fnt, maxw):
    text = re.sub(r"\*GTA\* \*(\d)\*", "*GTA\u00a0\\1*", text)
    text = re.sub(r"\bGTA (\d)", "GTA\u00a0\\1", text)  # ne jamais couper « GTA 6 »
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test.replace("*", ""), font=fnt) <= maxw:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_rich_line(draw, line, fnt, cy):
    """Dessine une ligne centrée ; les mots entre *...* sont en doré."""
    parts, gold = [], False
    for chunk in line.split("*"):
        if chunk:
            parts.append((chunk, gold))
        gold = not gold
    total = sum(draw.textlength(p, font=fnt) for p, _ in parts)
    x = SAFE_CX - total / 2
    for p, g in parts:
        draw.text((x, cy), p, font=fnt, fill=GOLD if g else WHITE,
                  stroke_width=6, stroke_fill=(15, 8, 20), anchor="lm")
        x += draw.textlength(p, font=fnt)


# Zone sûre Instagram/TikTok : boutons à droite (x > ~930, y ~1050-1650) et texte du post en bas (y > ~1550)
SAFE_W = 840          # largeur max du texte
SAFE_CX = 490         # centre horizontal décalé à gauche, loin des boutons
SUB_Y = 1065          # hauteur des sous-titres mot à mot (au-dessus des boutons, sous le titre)
LIAISON = {"à", "a", "au", "aux", "de", "du", "des", "le", "la", "les", "l'", "un", "une", "ton", "ta", "tes",
           "ton", "son", "sa", "ses", "mon", "ma", "mes", "ce", "cet", "cette", "ces", "et", "ou", "en", "sur",
           "pour", "par", "dans", "qui", "que", "qu'", "ça", "ne", "pas", "plus", "si", "tu", "il", "on", "je",
           "est", "c'est", "d'", "j'", "t'", "s'", "n'", "avec", "sans", "chez", "très", "trop", "déjà",
           "se", "me", "te", "y", "lui", "leur", "nous", "vous", "va", "vont", "sont", "ont"}


def sub_chunks(words, maxw=3, maxc=16):
    """Découpe les sous-titres en groupes de sens : jamais finir un groupe sur un petit mot de liaison."""
    out, i, n = [], 0, len(words)
    while i < n:
        j, chars = i, 0
        while j < n and j - i < maxw and chars + len(words[j][0]) <= maxc + (0 if j > i else 99):
            chars += len(words[j][0]) + 1
            j += 1
        lia = lambda k: words[k][0].lower().strip(".,!?") in LIAISON
        while j - i > 2 and lia(j - 1) and j < n:
            j -= 1
        if j - i == 2 and lia(j - 1) and j < n and not lia(i):
            j -= 1
        while j < n and all(lia(k) for k in range(i, j)):  # « la » seul : on colle le mot suivant
            j += 1
        if j < n and words[j - 1][0].upper().strip(".,!?") == "GTA":  # ne jamais couper « GTA 6 »
            j += 1
        out.append((i, j))
        i = j
    return out


def frame(base, seg, t, words=None):
    """t = secondes depuis le début du segment (pour l'animation d'entrée)."""
    im = base.copy()
    d = ImageDraw.Draw(im)
    pop = min(1.0, t / 0.18)
    ease = 1 - (1 - pop) ** 3

    if seg.get("tag"):
        f = font(F_BLACK, 54)
        tw = d.textlength(seg["tag"], font=f)
        x0 = (W - tw) / 2 - 36
        d.rounded_rectangle([x0, 300, x0 + tw + 72, 390], radius=45, fill=PINK)
        d.text((W / 2, 345), seg["tag"], font=f, fill=WHITE, anchor="mm")

    if seg.get("big"):
        size = int((260 if len(seg["big"]) <= 6 else 150) * (0.7 + 0.3 * ease))
        f = font(F_SERIF, size)
        tw = d.textlength(seg["big"], font=f)
        if tw > SAFE_W:  # trop large : on réduit (toujours sur une seule ligne)
            size = int(size * SAFE_W / tw)
            f = font(F_SERIF, size)
        lines = [seg["big"]]
        y = 560 - (len(lines) - 1) * size * 0.55
        for ln in lines:
            d.text((W / 2, y), ln, font=f, fill=GOLD, anchor="mm",
                   stroke_width=4, stroke_fill=(15, 8, 20))
            y += size * 1.1

    first = seg.get("_first")
    if seg.get("chat") is not None:
        draw_chat(im, d, seg, t)
    if seg.get("caption") and not (seg.get("chat") and not first):
        slam = 1.0
        if first:  # l'accroche arrive en « claque » (1,35 -> 1) : mouvement dès la 1re image
            slam = 1.0 + 0.35 * (1 - min(1.0, t / 0.16)) ** 2
        f = font(F_BLACK, int((100 if first else 72) * slam))  # 1er plan = accroche complète (sert aussi de couverture)
        toks = []
        for i, chunk in enumerate(seg["caption"].split("*")):
            for w in chunk.split():
                toks.append(f"*{w}*" if i % 2 else w)
        lines = wrap(d, " ".join(toks), f, SAFE_W)
        lines = [ln.replace("* *", " ") for ln in lines]
        lh = int((120 if first else 90) * slam)
        y0 = (1150 if first else 810) - (len(lines) - 1) * lh // 2 + (0 if first else int((1 - ease) * 30))
        for i, ln in enumerate(lines):
            draw_rich_line(d, ln, f, y0 + i * lh)

    # sous-titres mot à mot (2-3 mots, mot prononcé en surbrillance, effet « pop »)
    if words and not first and not seg.get("chat") and not seg.get("_mute"):
        chunks = sub_chunks(words)
        cur = max([i for i, (_, a, _) in enumerate(words) if a <= t] or [0])
        c0, c1 = next((a, b) for a, b in chunks if a <= cur < b)
        chunk = words[c0:c1]
        since = t - chunk[0][1]
        sc = 1.12 - 0.12 * min(1.0, max(0.0, since) / 0.09)
        f = font(F_BLACK, int(96 * sc))
        sp = d.textlength(" ", font=f)
        widths = [d.textlength(w.upper(), font=f) for w, _, _ in chunk]
        tot_w = sum(widths) + sp * (len(chunk) - 1)
        if tot_w > SAFE_W:
            f = font(F_BLACK, max(44, int(96 * sc * SAFE_W / tot_w)))
            sp = d.textlength(" ", font=f)
            widths = [d.textlength(w.upper(), font=f) for w, _, _ in chunk]
            tot_w = sum(widths) + sp * (len(chunk) - 1)
        x = SAFE_CX - tot_w / 2
        for j, (w, a, b) in enumerate(chunk):
            on = (c0 + j) == cur
            d.text((x, SUB_Y), w.upper(), font=f, anchor="lm", fill=(255, 225, 40) if on else WHITE,
                   stroke_width=9, stroke_fill=(10, 4, 16))
            x += widths[j] + sp

    # barre de progression en bas
    return im


CHAT_ME, CHAT_HIM = (40, 120, 255), (58, 58, 66)


def draw_chat(im, d, seg, t):
    """Fausse conversation entre deux potes inventés. seg['chat'] = messages déjà affichés + nouveaux
    (liste de ["moi"|"lui", "texte"]) ; seg['_new'] = nb de nouveaux messages qui apparaissent dans ce plan."""
    msgs = seg["chat"]
    new = seg.get("_new", len(msgs))
    f = font(F_BLACK, 64)
    x0, x1 = 50, 930
    # fond sombre derrière toute la conversation (lisible sur n'importe quelle vidéo)
    ov = Image.new("RGBA", (W, H))
    ImageDraw.Draw(ov).rounded_rectangle([x0 - 20, 230, x1 + 20, 1520], radius=50, fill=(8, 6, 14, 190))
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))
    d = ImageDraw.Draw(im)
    # en-tête façon messagerie
    d.rounded_rectangle([x0, 250, x1, 360], radius=30, fill=(24, 24, 30))
    d.ellipse([x0 + 25, 270, x0 + 95, 340], fill=PINK)
    d.text((x0 + 60, 305), seg.get("_who", "K")[0].upper(), font=font(F_BLACK, 40), fill=WHITE, anchor="mm")
    d.text((x0 + 120, 305), seg.get("_who", "Kevin"), font=font(F_BLACK, 46), fill=WHITE, anchor="lm")
    bubbles, y = [], 0
    for i, (who, txt) in enumerate(msgs):
        txt = re.sub(r"[^\w\s.,!?'’:;()«»…%€$+\-/]", "", txt).strip()
        lines = wrap(d, txt, f, 640)
        h = 44 + 78 * len(lines)
        bubbles.append((who, lines, h, i >= len(msgs) - new))
    # n'afficher que ce qui tient entre y=400 et y=1500 (les plus récents en bas)
    total, keep = 0, []
    for b in reversed(bubbles):
        if total + b[2] + 24 > 1100:
            break
        keep.insert(0, b)
        total += b[2] + 24
    y = 400
    nshown = 0
    for who, lines, h, is_new in keep:
        if is_new:
            idx = sum(1 for k in keep if k[3] and keep.index(k) < keep.index((who, lines, h, is_new)))
            appear = t - idx * 0.9  # les nouveaux messages arrivent l'un après l'autre
            if appear < 0:
                continue
            sc = min(1.0, appear / 0.15)
        else:
            sc = 1.0
        wmax = max(d.textlength(ln.replace("*", ""), font=f) for ln in lines)
        bw = wmax + 64
        me = who == "moi"
        bx = x1 - bw if me else x0
        oy = int((1 - sc) * 40)
        d.rounded_rectangle([bx, y + oy, bx + bw, y + h + oy], radius=34, fill=CHAT_ME if me else CHAT_HIM)
        for j, ln in enumerate(lines):
            d.text((bx + 32, y + oy + 22 + 39 + 78 * j), ln.replace("*", ""), font=f, fill=WHITE, anchor="lm")
        y += h + 24
        nshown += 1


def tts(text, voice, out):
    if voice.endswith(".onnx"):  # Piper (hors ligne)
        subprocess.run([sys.executable, "-m", "piper", "-m", voice, "-f", out,
                        "--length-scale", "0.88", "--sentence-silence", "0.05"],
                       input=text.encode(), check=True, capture_output=True)
    else:  # voix neuronale Edge, ex. fr-FR-VivienneMultilingualNeural
        mp3 = out + ".mp3"
        subprocess.run([sys.executable, os.path.join(HERE, "tts_edge.py"), voice, text, mp3],
                       check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", "24000", "-ac", "1", out],
                       check=True)
    with wave.open(out) as w:
        return w.getnframes() / w.getframerate()


def main(script_path, out_path):
    cfg = json.load(open(script_path))
    voice = cfg.get("voice", os.path.join(HERE, "..", "voices", "fr_FR-tom-medium.onnx"))
    tmp = tempfile.mkdtemp()
    base = background()
    raw = [os.path.join(tmp, f"r{i:03d}.wav") for i in range(len(cfg["segments"]))]
    # cache de voix PAR PHRASE : même voix + même phrase => on réutilise l'audio déjà validé
    import hashlib, shutil
    cdir = os.path.join(HERE, "voice_cache")
    os.makedirs(cdir, exist_ok=True)
    seg_cache = [os.path.join(cdir, hashlib.sha1(json.dumps([voice, s.get("phon", s["say"])]).encode()).hexdigest()[:16] + ".wav")
                 for s in cfg["segments"]]
    for i, p in enumerate(raw):
        if os.path.exists(seg_cache[i]):
            shutil.copy(seg_cache[i], p)
    missing = [i for i in range(len(raw)) if not os.path.exists(seg_cache[i])]
    print(f"voix en cache : {len(raw) - len(missing)}/{len(raw)} phrases", flush=True)
    if voice == "none":  # vidéo sans voix : texte + musique, durée fixée par plan
        for i in range(len(raw)):
            seg = cfg["segments"][i]
            dur = seg.get("dur", max(1.4, 0.065 * len(seg.get("caption", seg["say"]))))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                            "-t", f"{dur:.2f}", raw[i]], check=True)
        missing = []
        seg_cache = [os.path.join(tmp, f"nc{i}.wav") for i in range(len(raw))]
    if not missing:
        pass
    elif voice.startswith("chatterbox:"):  # voix expressive, modèle chargé une fois
        from verif_voix import verifier
        todo = list(missing)
        best = {}  # i -> (score, fichier, fin)
        from verif_voix import liberer
        for essai in range(3):
            liberer()  # Whisper hors RAM pendant Chatterbox (sinon OOM au 2e essai)
            jobs = os.path.join(tmp, "jobs.json")
            outs = {i: os.path.join(tmp, f"t{i:03d}_{essai}.wav") for i in todo}
            json.dump([{"text": cfg["segments"][i].get("phon", cfg["segments"][i]["say"]), "out": outs[i]} for i in todo], open(jobs, "w"))
            subprocess.run([os.path.join(HERE, "..", "cb", "bin", "python"),
                            os.path.join(HERE, "tts_cb_many.py"), voice.split(":", 1)[1], jobs], check=True)
            for i in todo:
                sc, fin = verifier(outs[i], cfg["segments"][i]["say"])
                print(f"phrase {i} essai {essai}: score {sc:.2f}", flush=True)
                if i not in best or sc > best[i][0]:
                    best[i] = (sc, outs[i], fin)
            todo = [i for i in todo if best[i][0] < 0.78]
            if not todo:
                break
        for i, (sc, f, fin) in best.items():
            cut = ["-t", f"{fin + 0.2:.2f}"] if fin else []
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, *cut, raw[i]], check=True)
            if sc < 0.78:
                print(f"ATTENTION phrase {i} reste douteuse (score {sc:.2f})")
    else:
        for i in missing:
            tts(cfg["segments"][i]["say"], voice, raw[i])

    # chaque phrase normalisée (24 kHz mono) + 0,12 s de silence -> durées exactes
    wavs, durs = [], []
    for i, p in enumerate(raw):
        q = os.path.join(tmp, f"a{i:03d}.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-ar", "24000", "-ac", "1",
                        "-af", "anull" if voice == "none" else "silenceremove=start_periods=1:start_threshold=-45dB,"
                               "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                               "apad=pad_dur=0.12", q], check=True)
        with wave.open(q) as w:
            durs.append(w.getnframes() / w.getframerate())
        wavs.append(q)
    for i, p in enumerate(wavs):
        shutil.copy(p, seg_cache[i])
    lst = os.path.join(tmp, "a.txt")
    with open(lst, "w") as f:
        for p in wavs:
            f.write(f"file '{p}'\n")
    audio = os.path.join(tmp, "voice.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", audio], check=True)
    total = sum(durs)

    fdir = os.path.join(tmp, "f")
    os.makedirs(fdir)
    n, t_start = 0, 0.0
    progress_h = 12
    # vidéos d'ambiance libres de droits (broll/), une par segment, assombries sous le texte
    import glob as _glob, random as _rnd
    # b-roll : les clips qui bougent le plus d'abord (broll/MOTION.json), un nouveau plan toutes les ~1,7 s
    _rnd.seed(script_path)
    motion = {}
    mpath = os.path.join(HERE, "broll", "MOTION.json")
    if os.path.exists(mpath):
        motion = json.load(open(mpath))
    clips = sorted(_glob.glob(os.path.join(HERE, "broll", "*.mp4"))) if cfg.get("broll") else []
    clips.sort(key=lambda p: -motion.get(os.path.basename(p), 0) + _rnd.random() * 3)
    dynamic = clips[: max(4, len(clips) * 2 // 3)]  # on écarte le tiers le plus statique
    _rnd.shuffle(dynamic)
    faces = sorted(_glob.glob(os.path.join(HERE, "broll", "faces", "*.mp4")))
    face_idx = {}
    if os.path.exists(os.path.join(HERE, "broll", "faces", "INDEX.txt")):
        for ln in open(os.path.join(HERE, "broll", "faces", "INDEX.txt")):
            parts = ln.split(" | ")
            face_idx[parts[0]] = (parts[1] + " " + parts[2]).lower()
    want = cfg.get("face")  # ex. "shocked" / "laughing" / "tired" : vraie réaction humaine sur l'accroche
    face_clip = None
    if want and faces:
        good = [p for p in faces if want.lower() in face_idx.get(os.path.basename(p), "")]
        face_clip = _rnd.choice(good or faces)
    opener = clips[0] if clips else None  # le plus dynamique ouvre la vidéo
    if cfg.get("opener"):  # ex. "fireworks", "drift", "police" : mot-clé cherché dans broll/INDEX.txt
        idx = open(os.path.join(HERE, "broll", "INDEX.txt")).read().lower().splitlines()
        hits = [os.path.join(HERE, "broll", ln.split(" | ")[0]) for ln in idx if cfg["opener"].lower() in ln]
        hits = [h for h in hits if os.path.exists(h)]
        if hits:
            opener = _rnd.choice(hits)
    shade = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(shade)
    for y in range(H):  # voile sombre, plus dense au centre (zone texte)
        a = int(55 + 110 * math.exp(-((y - 1100) / 520) ** 2))
        sd.line([(0, y), (W, y)], fill=(18, 8, 26, a))
    if voice == "none":
        for seg in cfg["segments"]:
            seg["_mute"] = True
    cfg["segments"][0]["_first"] = True  # pas de sous-titres mot à mot sur l'accroche
    # conversation : chaque plan affiche les messages précédents + les siens
    hist = []
    for seg in cfg["segments"]:
        if seg.get("chat") is not None:
            seg["_new"] = len(seg["chat"])
            hist = hist + [list(m) for m in seg["chat"]]
            seg["chat"] = list(hist)
            seg["_who"] = cfg.get("chat_name", "Kevin")
    SHOT = cfg.get("shot", 1.7)
    shots = []  # (début, fin, clip)
    t_acc, pool_i = 0.0, 0
    cut_times = set()
    for si, dur in enumerate(durs):
        a = t_acc
        while a < t_acc + dur - 0.05:
            b = min(t_acc + dur, a + SHOT)
            if t_acc + dur - b < 0.6:
                b = t_acc + dur
            if si == 0 and a == 0 and (face_clip or opener):
                c = face_clip or opener
            else:
                c = dynamic[pool_i % len(dynamic)] if dynamic else None
                pool_i += 1
            shots.append((a, b, c))
            cut_times.add(round(a * FPS))
            a = b
        t_acc += dur
    shot_frames = {}
    for j, (a, b, c) in enumerate(shots):
        if not c:
            continue
        bdir = os.path.join(tmp, f"b{j:03d}")
        os.makedirs(bdir)
        off = 1.0 + _rnd.random() * 3
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{off:.2f}", "-stream_loop", "-1", "-i", c, "-t", f"{b - a + 0.1:.2f}",
                        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                        "-q:v", "4", os.path.join(bdir, "%05d.jpg")], check=True)
        shot_frames[j] = (round(a * FPS), bdir, len(os.listdir(bdir)))
    def bg_at(n):
        for j, (a, b, c) in enumerate(shots):
            if round(a * FPS) <= n < round(b * FPS) and j in shot_frames:
                f0, bdir, cnt = shot_frames[j]
                return os.path.join(bdir, f"{min(n - f0 + 1, cnt):05d}.jpg"), n - f0
        return None, n
    seg_starts = []
    rng_shake = _rnd.Random(7)
    for si, (seg, dur) in enumerate(zip(cfg["segments"], durs)):
        nf = max(1, round(dur * FPS))
        seg_starts.append(t_start)
        # mots prononcés répartis sur la durée parlée (proportionnel à la longueur)
        spoken = re.sub(r"[.…!?;:,]+", " ", seg["say"]).split()
        speak = max(0.3, dur - 0.12)
        tot = sum(len(w) + 2 for w in spoken) or 1
        words, acc = [], 0.0
        for w in spoken:
            a = acc / tot * speak
            acc += len(w) + 2
            words.append((w, a, acc / tot * speak))
        for k in range(nf):
            b = synthwave(n) if cfg.get("style", "synthwave") == "synthwave" else base
            bf, ks = bg_at(n)
            if bf:
                b = Image.alpha_composite(Image.open(bf).convert("RGBA"), shade).convert("RGB")
            # zoom : « punch » 1,12 -> 1,0 à chaque nouveau plan, puis zoom lent
            z = 1.0 + 0.05 * (ks / (SHOT * FPS)) + 0.14 * max(0.0, 1 - ks / 6) ** 2
            if n < 3:
                z += 0.12 * (1 - n / 3)
            bw, bh = int(W * z), int(H * z)
            dx = dy = 0
            if n < 10:  # léger tremblement à l'ouverture
                amp = 14 * (1 - n / 10)
                dx, dy = int(rng_shake.uniform(-amp, amp)), int(rng_shake.uniform(-amp, amp))
            b = b.resize((bw, bh), Image.BILINEAR)
            cx0 = max(0, min(bw - W, (bw - W) // 2 + dx))
            cy0 = max(0, min(bh - H, (bh - H) // 2 + dy))
            b = b.crop((cx0, cy0, cx0 + W, cy0 + H))
            im = frame(b, seg, k / FPS, words)
            if n < 5:  # flash blanc d'ouverture
                im = Image.blend(im, Image.new("RGB", (W, H), WHITE), 0.55 * (1 - n / 5))
            d = ImageDraw.Draw(im)
            prog = (t_start + k / FPS) / total
            d.rectangle([0, H - progress_h, int(W * prog), H], fill=GOLD)
            im.save(os.path.join(fdir, f"{n:05d}.jpg"), quality=90)
            n += 1
        t_start += dur

    # effets sonores synthétisés (originaux) : whoosh à chaque nouveau plan, impact sur les gros chiffres, pop sur les étiquettes
    try:
        import numpy as np
        sr = 44100
        sfx = np.zeros(int((total + 1) * sr), dtype=np.float32)
        rng = np.random.default_rng(1)

        def put(sig, t):
            i = int(max(0, t) * sr)
            sfx[i:i + len(sig)] += sig[:max(0, len(sfx) - i)]

        tt = np.arange(int(0.35 * sr)) / sr
        noise = rng.standard_normal(len(tt)).astype(np.float32)
        env = np.sin(np.pi * tt / tt[-1]) ** 2
        whoosh = np.convolve(noise, np.ones(30) / 30, mode="same") * env * 0.35
        ti = np.arange(int(0.4 * sr)) / sr
        impact = (np.sin(2 * np.pi * (90 - 50 * ti) * ti) * np.exp(-ti * 9)).astype(np.float32) * 0.7
        tp = np.arange(int(0.08 * sr)) / sr
        pop = (np.sin(2 * np.pi * (900 - 2500 * tp) * tp) * np.exp(-tp * 45)).astype(np.float32) * 0.35
        for ct in sorted(cut_times):
            if ct:
                put(whoosh * 0.6, ct / FPS - 0.12)
        put(impact * 0.8, 0.0)  # impact dès la 1re image
        for si, seg in enumerate(cfg["segments"]):
            t0 = seg_starts[si]
            if si:
                put(whoosh, t0 - 0.12)
            if seg.get("big"):
                put(impact, t0 + 0.02)
            if seg.get("tag"):
                put(pop, t0 + 0.08)
        import wave as _wv
        sfx_path = os.path.join(tmp, "sfx.wav")
        with _wv.open(sfx_path, "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes((np.clip(sfx, -1, 1) * 32767).astype(np.int16).tobytes())
        withsfx = os.path.join(tmp, "voice_sfx.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", audio, "-i", sfx_path, "-filter_complex",
                        "[0:a]aresample=44100[v];[1:a]volume=0.8[s];[v][s]amix=inputs=2:duration=first:normalize=0",
                        withsfx], check=True)
        audio = withsfx
    except Exception as e:
        print("sfx ignorés:", e)

    # musique de fond libre de droits (music/*.wav|mp3), en sourdine sous la voix
    import glob as _g2
    tracks = sorted(_g2.glob(os.path.join(HERE, "music", "*.wav")) + _g2.glob(os.path.join(HERE, "music", "*.mp3")))
    if cfg.get("music", True) and tracks:
        trk = cfg["music"] if isinstance(cfg.get("music"), str) else tracks[hash(script_path) % len(tracks)]
        mixed = os.path.join(tmp, "mix.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", audio, "-stream_loop", "-1", "-i", trk,
                        "-filter_complex",
                        f"[1:a]volume=0.5,aresample=44100,volume='if(between(t,{seg_starts[-1]:.2f},{seg_starts[-1] + 1.1:.2f}),0.08,1)':eval=frame[m];"
                        "[0:a]aresample=44100,asplit[v][sc];"
                        "[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[md];"
                        "[v][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95",
                        "-t", f"{total:.2f}", mixed], check=True)
        audio = mixed
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS),
                    "-i", os.path.join(fdir, "%05d.jpg"), "-i", audio,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                    out_path], check=True)
    print(f"OK {out_path} {total:.1f}s {n} frames")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
