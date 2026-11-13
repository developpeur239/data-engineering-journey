#!/bin/sh
# Séquence 1 « Nice » : images (frames_nice/) + son (son_nice.wav) → nice.mp4
set -e
cd "$(dirname "$0")"
ffmpeg -v error -y -framerate 30 -i frames_nice/%05d.jpg -i son_nice.wav -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -movflags +faststart nice.mp4
echo ok nice.mp4
