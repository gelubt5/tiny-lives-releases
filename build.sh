# bash build.sh <episode_dir> <output.mp4>   (concat scenes + narration + music + engine SFX, -14 LUFS)
set -e
D=$(cd "$1" && pwd); OUTF=$2; TK=$(cd "$(dirname "$0")" && pwd)
cd "$D"; rm -f list.txt; off=0; delays=""
for f in out/sc_*.mp4; do echo "file '$D/$f'" >> list.txt; d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $f); delays="$delays $off"; off=$(python3 -c "print($off+$d)"); done
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c:v copy -c:a aac video_sfx.mp4
python3 "$TK/music.py" $off music.wav
args=""; filt=""; k=0
for d in $delays; do args="$args -i nar/n$(printf %02d $k).wav"; ms=$(python3 -c "print(int(($d+0.4)*1000))"); filt="$filt[$((k+1)):a]aresample=44100,adelay=${ms}|${ms}[n$k];"; k=$((k+1)); done
mix=""; for j in $(seq 0 $((k-1))); do mix="$mix[n$j]"; done
ffmpeg -v error -y -i video_sfx.mp4 $args -i music.wav -filter_complex "${filt}${mix}amix=inputs=$k:normalize=0,volume=1.6[nar];[$((k+1)):a]volume=0.16[mus];[0:a]volume=0.5[sfx];[nar][mus][sfx]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5[a]" -map 0:v -map "[a]" -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest "$OUTF"
