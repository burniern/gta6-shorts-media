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
BLOCKED = {15936, 190482, 24603, 253425, 253426, 2860, 7315, 80724, 8675}  # clips refusés après vérification visuelle (hors sujet ou personnes)
BAD = re.compile(r"\b(blood|weapon|gun|accident|crash|funeral|war|protest|injur|dead|death|kid|child)\b", re.I)


def key():
    k = os.environ.get("PIXABAY_KEY")
    if not k and os.path.exists(os.path.join(HERE, "pixabay_key.txt")):
        k = open(os.path.join(HERE, "pixabay_key.txt")).read().strip()
    return k


def main(n=3):
    os.makedirs(OUT, exist_ok=True)
    k = key()
    have = set(os.listdir(OUT))
    for q in QUERIES:
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
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
