"""Contrôle qualité de la voix : transcrit chaque phrase, coupe le charabia en fin
de phrase, et signale les phrases à régénérer."""
import difflib, re, unicodedata, wave
import numpy as np

_model = None


def _m():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def _norm(t):
    # chiffres -> lettres pour comparer "51" et "cinquante et un"
    from num2words import num2words
    t = re.sub(r"\d+", lambda m: " " + num2words(int(m.group()), lang="fr") + " ", t)
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9 ]", " ", t.replace("'", " ").replace("-", " "))
    return t.split()


def _load16k(path):
    import subprocess, tempfile, os
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ar", "16000", "-ac", "1", tmp], check=True)
    w = wave.open(tmp)
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    os.remove(tmp)
    return a


def verifier(path, attendu):
    """Retourne (score 0-1, fin_utile_en_s ou None)."""
    segs, _ = _m().transcribe(_load16k(path), language="fr", word_timestamps=True)
    words = [w for s in segs for w in (s.words or [])]
    exp = _norm(attendu)
    if not words or not exp:
        return 0.0, None
    best, best_end = 0.0, None
    toks = []
    for w in words:
        toks += _norm(w.word)
        r = difflib.SequenceMatcher(None, exp, toks).ratio()
        if r >= best:
            best, best_end = r, w.end
    return best, best_end


def liberer():
    """Libère le modèle Whisper (RAM) avant de relancer Chatterbox : évite le SIGKILL (OOM) au 2e essai."""
    global _model
    _model = None
    import gc
    gc.collect()
