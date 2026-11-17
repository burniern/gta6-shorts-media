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
    words, lines, cur = text.split(), [], ""
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
    x = (W - total) / 2
    for p, g in parts:
        draw.text((x, cy), p, font=fnt, fill=GOLD if g else WHITE,
                  stroke_width=6, stroke_fill=(15, 8, 20), anchor="lm")
        x += draw.textlength(p, font=fnt)


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
        lines = wrap(d, seg["big"], f, W - 120)
        y = 620 - (len(lines) - 1) * size * 0.55
        for ln in lines:
            d.text((W / 2, y), ln, font=f, fill=GOLD, anchor="mm",
                   stroke_width=4, stroke_fill=(15, 8, 20))
            y += size * 1.1

    if seg.get("caption"):
        f = font(F_BLACK, 72)
        toks = []
        for i, chunk in enumerate(seg["caption"].split("*")):
            for w in chunk.split():
                toks.append(f"*{w}*" if i % 2 else w)
        lines = wrap(d, " ".join(toks), f, W - 140)
        lines = [ln.replace("* *", " ") for ln in lines]
        y0 = 880 - (len(lines) - 1) * 44 + int((1 - ease) * 30)
        for i, ln in enumerate(lines):
            draw_rich_line(d, ln, f, y0 + i * 90)

    # sous-titres mot à mot (2-3 mots, mot prononcé en surbrillance, effet « pop »)
    if words:
        cur = max([i for i, (_, a, _) in enumerate(words) if a <= t] or [0])
        c0 = (cur // 3) * 3
        chunk = words[c0:c0 + 3]
        since = t - chunk[0][1]
        sc = 1.12 - 0.12 * min(1.0, max(0.0, since) / 0.09)
        f = font(F_BLACK, int(104 * sc))
        widths = [d.textlength(w.upper() + " ", font=f) for w, _, _ in chunk]
        tot_w = sum(widths) - d.textlength(" ", font=f)
        if tot_w > W - 90:  # mots longs (ex. QUATRE-VINGTS) : on réduit pour ne pas déborder
            f = font(F_BLACK, max(40, int(104 * sc * (W - 90) / tot_w)))
            widths = [d.textlength(w.upper() + " ", font=f) for w, _, _ in chunk]
        x = (W - sum(widths) + d.textlength(" ", font=f)) / 2
        for j, (w, a, b) in enumerate(chunk):
            on = (c0 + j) == cur
            d.text((x, 1360), w.upper(), font=f, anchor="lm", fill=(255, 225, 40) if on else WHITE,
                   stroke_width=9, stroke_fill=(10, 4, 16))
            x += widths[j]

    # barre de progression en bas
    return im


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
                        "-af", "silenceremove=start_periods=1:start_threshold=-45dB,"
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
    clips = sorted(_glob.glob(os.path.join(HERE, "broll", "*.mp4"))) if cfg.get("broll") else []
    _rnd.seed(script_path)
    _rnd.shuffle(clips)
    shade = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(shade)
    for y in range(H):  # voile sombre, plus dense au centre (zone texte)
        a = int(55 + 110 * math.exp(-((y - 1100) / 520) ** 2))
        sd.line([(0, y), (W, y)], fill=(18, 8, 26, a))
    seg_starts = []
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
        bdir = None
        if clips:
            bdir = os.path.join(tmp, f"b{si:03d}")
            os.makedirs(bdir)
            src = clips[si % len(clips)]
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", src, "-t", f"{dur:.2f}",
                            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                            "-q:v", "4", os.path.join(bdir, "%05d.jpg")], check=True)
        for k in range(nf):
            b = synthwave(n) if cfg.get("style", "synthwave") == "synthwave" else base
            if bdir:
                bf = os.path.join(bdir, f"{min(k + 1, len(os.listdir(bdir))):05d}.jpg")
                b = Image.alpha_composite(Image.open(bf).convert("RGBA"), shade).convert("RGB")
            z = 1.0 + 0.07 * (k / max(1, nf))  # zoom lent continu
            if z > 1.0:
                bw, bh = int(W * z), int(H * z)
                b = b.resize((bw, bh), Image.BILINEAR).crop(((bw - W) // 2, (bh - H) // 2, (bw - W) // 2 + W, (bh - H) // 2 + H))
            im = frame(b, seg, k / FPS, words)
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
