#!/bin/sh
# Assemble le film complet « Et si la Terre tournait de plus en plus vite… » : chaque séquence (images + son) puis le tout.
set -e
cd "$(dirname "$0")"
mkdir -p segments
ORDRE="ouverture nice kourou espace paris equateur nicepente apesanteur anneau fin"
: > segments/liste.txt
for s in $ORDRE; do
  if [ "$s" = nice ]; then IMG=frames_nice; else IMG=rendus/$s; fi
  ffmpeg -v error -y -framerate 30 -i "$IMG/%05d.jpg" -i "son_$s.wav" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 30 \
    -c:a aac -b:a 192k -ar 48000 -ac 2 -shortest "segments/$s.mp4"
  echo "file '$s.mp4'" >> segments/liste.txt
  echo "séquence $s : $(ffprobe -v error -show_entries format=duration -of csv=p=0 segments/$s.mp4) s"
done
ffmpeg -v error -y -f concat -safe 0 -i segments/liste.txt -c copy terre_acceleree.mp4
ffmpeg -nostats -i terre_acceleree.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:" | tail -2
echo "ok terre_acceleree.mp4 : $(ffprobe -v error -show_entries format=duration -of csv=p=0 terre_acceleree.mp4) s"
