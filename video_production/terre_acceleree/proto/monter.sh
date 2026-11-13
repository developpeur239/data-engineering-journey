#!/bin/sh
# Assemble les images (frames/) et le son (son.wav) en prototype.mp4
set -e
cd "$(dirname "$0")"
ffmpeg -v error -y -framerate 30 -i frames/%05d.jpg -i son.wav -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -movflags +faststart prototype.mp4
echo ok prototype.mp4
