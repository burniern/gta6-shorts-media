#!/usr/bin/env python3
"""Bibliothèque de vidéos d'ambiance libres (Pixabay, usage commercial autorisé, sans crédit obligatoire).
Ambiance Miami / Floride / nuit / néons / police / voitures. Convertit en 720x1280 vertical, 12 s max.
Usage: python3 fetch_broll.py [nb_par_requete]   (clé dans pixabay_key.txt ou $PIXABAY_KEY)
"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "broll")
QUERIES = ["miami night", "miami beach", "miami skyline", "neon city night", "police car lights",
           "sports car night", "palm trees sunset", "florida swamp", "speedboat ocean", "highway night drive",
           "nightclub lights", "money cash", "city traffic night aerial", "sunset beach drone", "helicopter city"]
BLOCKED = {106379, 142997, 1651, 181376, 187690, 37253, 39183, 45283, 57179, 57181, 65390, 6970, 7686, 11722, 212404, 16931, 81185, 16160, 283428, 15936, 253387, 253388, 239125, 205875, 16045, 1295, 2946, 190482, 24603, 253425, 253426, 2860, 7315, 80724, 8675, 110933, 253391, 31956, 37283, 137765, 16046, 114445, 135480, 180386, 114900, 13441, 16939, 211724, 222308, 253390, 253392, 31342, 3565, 74, 694, 302098, 107635, 116937, 186533, 117749, 38084, 174003, 26619, 64597, 202749, 38388, 114945, 1630, 186535, 15629, 224421, 16934, 253389, 152397, 90048, 283426, 132, 151295, 202987, 26726, 272238, 363873, 37255, 37256, 41, 47813, 7602, 8437, 88686, 26767, 44702, 36944, 387099, 283737, 135320, 19600, 218795, 21827, 42047, 51199, 61755, 729, 202134, 199623, 215751, 37799, 275188, 16938, 8173, 129904, 10747, 130172, 139, 148597, 171116, 180776, 202743, 21223, 282995, 40352, 444, 46, 48019, 77626, 83875}  # clips refusés après vérification visuelle (hors sujet ou personnes)
BAD = re.compile(r"\b(blood|weapon|gun|accident|crash|funeral|war|protest|injur|dead|death|kid|child)\b", re.I)


def key():
    k = os.environ.get("PIXABAY_KEY")
    if not k and os.path.exists(os.path.join(HERE, "pixabay_key.txt")):
        k = open(os.path.join(HERE, "pixabay_key.txt")).read().strip()
    return k


FACES = ["shocked man", "surprised woman", "man laughing", "woman laughing", "excited man celebrating",
         "tired man office", "yawning man", "man screaming excited", "woman shocked phone", "man disappointed",
         "gamer playing video game", "man playing console", "friends cheering", "woman celebrating", "man waking up alarm"]
ACTION = ["car drifting", "night drive fast", "police lights night", "sports car speed", "neon lights", "fireworks night",
          "motorcycle night", "speedboat fast", "city timelapse night", "lightning storm"]


def main(n=3, queries=None, out=None):
    global OUT
    if out:
        OUT = out
    queries = queries or QUERIES
    os.makedirs(OUT, exist_ok=True)
    k = key()
    have = set(os.listdir(OUT))
    for q in queries:
        url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
            dict(key=k, q=q, per_page=20, safesearch="true", video_type="film"))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (gta6-shorts)"})
            hits = json.load(urllib.request.urlopen(req, timeout=30)).get("hits", [])
        except Exception as e:
            print("erreur", q, e)
            continue
        got = 0
        for h in hits:
            if got >= n:
                break
            if h["id"] in BLOCKED or BAD.search(h.get("tags", "")) or h.get("duration", 0) < 5:
                continue
            name = f"px{h['id']}.mp4"
            if name in have:
                got += 1
                continue
            v = h["videos"].get("medium") or h["videos"].get("small")
            if not v or not v.get("url"):
                continue
            dst = os.path.join(OUT, name)
            cmd = ["ffmpeg", "-v", "error", "-y", "-user_agent", "Mozilla/5.0 (gta6-shorts)", "-i", v["url"], "-t", "12", "-an",
                   "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", dst]
            if subprocess.run(cmd, timeout=240).returncode == 0 and os.path.getsize(dst) > 50000:
                have.add(name)
                got += 1
                with open(os.path.join(OUT, "INDEX.txt"), "a") as f:
                    f.write(f"{name} | {q} | {h['tags']} | pixabay {h['pageURL']}\n")
                print("ok", q, name, flush=True)
            elif os.path.exists(dst):
                os.remove(dst)
        time.sleep(1)


if __name__ == "__main__":
    # python3 fetch_broll.py 3            -> ambiance (broll/)
    # python3 fetch_broll.py 2 faces      -> vraies réactions humaines (broll/faces/), pour l'accroche
    # python3 fetch_broll.py 2 action     -> plans très dynamiques (broll/), pour la 1re seconde
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    kind = sys.argv[2] if len(sys.argv) > 2 else ""
    if kind == "faces":
        main(n, FACES, os.path.join(HERE, "broll", "faces"))
    elif kind == "action":
        main(n, ACTION)
    else:
        main(n)
    subprocess.run([sys.executable, os.path.join(HERE, "motion_score.py")])
