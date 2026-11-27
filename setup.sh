# One-time setup in a fresh cloud session (~1 min)
set -e
pip install --break-system-packages -q pycairo numpy fonttools 2>/dev/null || pip install -q pycairo numpy fonttools
mkdir -p ~/.fonts
for f in "bangers/Bangers-Regular.ttf:Bangers.ttf" "cinzel/Cinzel%5Bwght%5D.ttf:Cinzel.ttf" "baloo2/Baloo2%5Bwght%5D.ttf:Baloo2.ttf"; do
  src=${f%%:*}; dst=${f##*:}; [ -s ~/.fonts/$dst ] || curl -sSL -o ~/.fonts/$dst "https://raw.githubusercontent.com/google/fonts/main/ofl/$src"
done
fc-cache -f >/dev/null; fc-list : family | grep -E "Bangers|Cinzel" | head -2
which ffmpeg >/dev/null && echo setup-ok
