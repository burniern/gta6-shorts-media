#!/usr/bin/env bash
# Installe tout ce qu'il faut pour la machine à shorts GTA 6 dans une session cloud vierge.
# Usage : bash setup.sh   (depuis le dossier qui contient make_short.py)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
pip install --break-system-packages -q faster-whisper num2words pillow 2>&1 | grep -v WARNING || true
if [ ! -x "$ROOT/cb/bin/python" ]; then
  python3 -m venv "$ROOT/cb"
  "$ROOT/cb/bin/pip" install -q --upgrade pip
  "$ROOT/cb/bin/pip" install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu
  "$ROOT/cb/bin/pip" install -q chatterbox-tts
fi
which ffmpeg >/dev/null || (apt-get update -qq && apt-get install -y -qq ffmpeg)

# musiques de fond libres de droits générées avec vidIQ (liens permanents)
mkdir -p "$HERE/music"
[ -f "$HERE/music/synthwave_miami.mp3" ] || (curl -sL -m 120 -o /tmp/m1.wav "https://ai-music-tracks.s3.us-east-1.amazonaws.com/ec5a1adb-90e1-43c6-b2a1-3b43f0f05ead/f7cf9715-0755-4bfd-a6ca-f7071c004402.wav" && ffmpeg -v error -y -i /tmp/m1.wav -ac 2 -b:a 160k "$HERE/music/synthwave_miami.mp3")
[ -f "$HERE/music/trap_tropical.mp3" ] || (curl -sL -m 120 -o /tmp/m2.wav "https://ai-music-tracks.s3.us-east-1.amazonaws.com/ec5a1adb-90e1-43c6-b2a1-3b43f0f05ead/6f945e0e-41fe-4b3c-99b7-dab3d8987771.wav" && ffmpeg -v error -y -i /tmp/m2.wav -ac 2 -b:a 160k "$HERE/music/trap_tropical.mp3")
echo "MUSIQUE OK"
echo "SETUP OK"
