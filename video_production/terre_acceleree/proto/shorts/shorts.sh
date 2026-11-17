#!/bin/bash
# Shorts verticaux natifs (1080×1920) du film « Terre accélérée ».
#   ./shorts/shorts.sh rendre <nom>    → images dans rendus_v/<nom>/
#   ./shorts/shorts.sh monter <nom>    → shorts/<nom>.mp4 (son du film, carte de fin)
# nom : scène:séquence:début:fin
set -euo pipefail
cd "$(dirname "$0")/.."
# phrase d'accroche seule pendant les 2,5 premières secondes (compteur et sous-titre masqués au rendu : &accroche=)
declare -A ACC=(
  [s1_on_ne_pese_plus_rien]="TU PÈSES 0 KG|150"
  [s2_la_mer_quitte_nice]="LA MER QUITTE NICE|128"
  [s3_paris_penche]="PARIS SE MET À PENCHER|100"
  [s4_la_terre_devient_un_anneau]="LA TERRE SE DÉCHIRE|124"
)
declare -A S=(
  [s1_on_ne_pese_plus_rien]="navire:apesanteur:6:30:12"   # ouverture 12–14,5 s re-rendue avec &elan=12 (recul de caméra)
  [s2_la_mer_quitte_nice]="scene:nice:18:58"
  [s3_paris_penche]="paris:paris:45:90"
  [s4_la_terre_devient_un_anneau]="espace:anneau:0:50"
)
POLICE=../../lune/film/shorts/polices/Anton.ttf
act=$1; nom=$2; IFS=: read sc sq d f m <<< "${S[$nom]}"
if [ "$act" = rendre ]; then
  rm -rf "rendus_v/${nom:?}"; node render.cjs "$d" "$f" 0.0333333333 "rendus_v/$nom" "$sc:$sq:vertical=1" 2>&1 | grep -E "ERREUR" || true
  echo "$nom $(ls rendus_v/$nom | wc -l) images"
else
  IFS="|" read acc tacc <<< "${ACC[$nom]}"
  m=${m:-$d}; skip=$(python3 -c "print(round(($m-$d)*30))"); d=$m
  dur=$(python3 -c "print($f-$d)")
  ffmpeg -v error -y -framerate 30 -start_number "$skip" -i "rendus_v/$nom/%05d.jpg" -ss "$d" -t "$dur" -i "son_$sq.wav" \
    -filter_complex "[0:v]zoompan=z='if(lt(on,75),1.12-0.12*on/75,1)':d=1:x=0:y=0:s=1080x1920:fps=30,drawtext=fontfile=$POLICE:text='$acc':fontsize=$tacc:fontcolor=white:borderw=6:bordercolor=black@0.6:x=(w-tw)/2:y=330:enable='lt(t,2.5)':alpha='if(lt(t,2.2),1,(2.5-t)/0.3)',drawbox=x=0:y=820:w=1080:h=330:color=black@0.6:t=fill:enable='gte(t,$dur-3.5)',drawtext=fontfile=$POLICE:text='LE FILM COMPLET':fontsize=104:fontcolor=0xffb347:x=(w-tw)/2:y=860:enable='gte(t,$dur-3.5)',drawtext=fontfile=$POLICE:text='SUR LA CHAÎNE':fontsize=104:fontcolor=white:x=(w-tw)/2:y=990:enable='gte(t,$dur-3.5)',fade=t=out:st=$(python3 -c "print($dur-0.4)"):d=0.4[v];[1:a]afade=t=in:d=0.03,afade=t=out:st=$(python3 -c "print($dur-0.6)"):d=0.6,loudnorm=I=-14:TP=-1:LRA=11[a]" \
    -map "[v]" -map "[a]" -t "$dur" -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -movflags +faststart "shorts/$nom.mp4"
  echo "ok shorts/$nom.mp4 $dur s"
fi
