# bash build_short.sh shorts/<slug>   -> shorts/<slug>/short.mp4 (1080x1920, title + word-chunk captions, -14 LUFS)
set -e
TK=$(cd "$(dirname "$0")" && pwd); D=$(cd "$1" && pwd)
bash "$TK/build.sh" "$D" "$D/horiz.mp4"
python3 "$TK/short_subs.py" "$D"
cd "$D"
ffmpeg -v error -y -i horiz.mp4 -filter_complex "[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=24:3,eq=brightness=-0.18:saturation=0.8[bg];[b]scale=1080:-2[fg];[bg][fg]overlay=0:656,ass=subs.ass:fontsdir=/root/.fonts[v]" -map "[v]" -map 0:a -af loudnorm=I=-14:TP=-1.5 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart short.mp4
