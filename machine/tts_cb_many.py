#!/usr/bin/env python3
"""Voix Chatterbox (expressive) : génère plusieurs phrases en chargeant le modèle une seule fois.
Usage (dans le venv cb): python tts_cb_many.py REF.wav jobs.json
jobs.json = [{"text": "...", "out": "/chemin/a000.wav"}, ...]
"""
import json, os, re, sys
os.environ.setdefault("TQDM_DISABLE", "1")
import torch, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

NUM = {"1": "un", "2": "deux", "3": "trois", "4": "quatre", "5": "cinq",
       "6": "six", "7": "sept", "8": "huit", "9": "neuf"}


def prononciation(t):
    # GTA 6 -> "Gé Té A six" (choix validé par l'utilisateur)
    t = re.sub(r"\bGTA\s*([1-9])\b", lambda m: "Gé Té A " + NUM[m.group(1)], t)
    t = re.sub(r"\bGTA\b", "Gé Té A", t)
    # phonétique seulement pour les mots difficiles (approche mixte validée)
    for a, b in {"Take-Two": "Tèk Tou", "Rockstar": "Rokstar", "Newzoo": "Niou Zou",
                 "PS5": "Pé Èsse cinq", "Xbox": "Ixe Boxe", "trailer": "trèleur",
                 "Vice City": "Vaïsse Siti", "Lucia": "Loussia", "Jason": "Djèïssone",
                 "Leonida": "Léonida", "cinquante et un": "sinkante é un"}.items():
        t = t.replace(a, b)
    return t


ref, jobs = sys.argv[1], json.load(open(sys.argv[2]))
torch.set_num_threads(os.cpu_count() or 2)
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
for j in jobs:
    kw = dict(language_id="fr", exaggeration=0.8, cfg_weight=0.35, temperature=0.8)
    if ref and ref != "none":
        kw["audio_prompt_path"] = ref
    w = m.generate(prononciation(j["text"]), **kw)
    torchaudio.save(j["out"], w, m.sr)
    print("ok", j["out"], flush=True)
