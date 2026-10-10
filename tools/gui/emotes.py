"""Draws the Cirri's emote bubbles: src/main/resources/assets/skyfriends/textures/gui/emotes.png (128x128).

    python tools/gui/emotes.py

Layout (client/EmoteBubbles.java): the top row holds three 32x32 bubbles (0 a round cloud for speech, 1 a thought
cloud trailing little puffs, 2 a spiky storm cloud for a shout); below, from y=32, 16x16 symbol cells, eight to a
row: ! ? heart note anger sweat dot dot-dot dot-dot-dot Zz sparkle idea gloom blush. Symbols are 12x12 pixel art
centred in their cells. Preview: tools/gui/out/emotes_preview.png (4x, on a sky background).
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/main/resources/assets/skyfriends/textures/gui/emotes.png'
PREVIEW = Path(__file__).resolve().parent / 'out' / 'emotes_preview.png'

EDGE = (58, 95, 134, 255)
WHITE = (255, 255, 255, 255)
SHADE = (222, 234, 246, 255)


def blob(circles, size=32):
    """A mask (set of pixels) made of filled circles: (cx, cy, r)."""
    px = set()
    for cx, cy, r in circles:
        for y in range(size):
            for x in range(size):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    px.add((x, y))
    return px


def paint(img, ox, oy, mask, fill=WHITE, edge=EDGE, shade=SHADE):
    """Fills a mask with an outline one pixel thick and a soft shade along its underside."""
    for (x, y) in mask:
        outside = any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        below = (x, y + 2) not in mask
        img.putpixel((ox + x, oy + y), edge if outside else shade if below else fill)


def bubbles(img):
    body = blob([(10, 13, 6.5), (16, 9.5, 7.5), (22, 13, 6.5), (16, 15.5, 7), (12, 17, 5), (20, 17, 5)])
    tail = {(x, y) for y in range(20, 27) for x in range(13, 19) if x - 13 <= 26 - y and x >= 13 + (y - 20) // 2}
    paint(img, 0, 0, body | tail)
    puffs = blob([(9.5, 24.5, 2.4), (6, 28.5, 1.6)])
    paint(img, 32, 0, body)
    paint(img, 32, 0, puffs)
    # a storm cloud: the body with jags all round
    import math
    jag = set()
    poly = []
    for i in range(28):
        a = i / 28 * math.tau
        r = 13.5 if i % 2 == 0 else 9.5
        poly.append((16 + math.cos(a) * r, 13 + math.sin(a) * r * 0.82))
    m = Image.new('L', (32, 32), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    for y in range(32):
        for x in range(32):
            if m.getpixel((x, y)):
                jag.add((x, y))
    paint(img, 64, 0, jag, fill=(255, 250, 232, 255), edge=(176, 120, 30, 255), shade=(250, 234, 196, 255))


# 12x12 symbols; '.' clear, 'o' outline, 'a' main colour, 'b' highlight, 'c' third colour
SYMBOLS = [
    ('exclaim', {'a': '#F06A3C', 'o': '#8A2E14'}, [
        '....oooo....', '...oaaaao...', '...oaaaao...', '...oaaaao...', '...oaaaao...', '....oaao....',
        '....oaao....', '.....oo.....', '............', '....oooo....', '...oaaaao...', '....oooo....']),
    ('question', {'a': '#4F8FD6', 'o': '#1E3F6B'}, [
        '...oooooo...', '..oaaaaaao..', '.oaaooooaao.', '..oo....oao.', '.......oaao.', '......oaao..',
        '.....oaao...', '.....oaao...', '......oo....', '.....oooo...', '....oaaaao..', '.....oooo...']),
    ('heart', {'a': '#F2607E', 'b': '#FFC2CF', 'o': '#8C2238'}, [
        '............', '..oo....oo..', '.obbo..oaao.', 'oabbaooaaaao', 'oaaaaaaaaaao', 'oaaaaaaaaaao',
        '.oaaaaaaaao.', '..oaaaaaao..', '...oaaaao...', '....oaao....', '.....oo.....', '............']),
    ('note', {'a': '#5468C8', 'b': '#AFC0FF', 'o': '#22306B'}, [
        '.......oo...', '......oabo..', '......oaabo.', '......oa.oao', '......oa..oo', '......oa....',
        '......oa....', '...oooaa....', '..oaaaaa....', '..oabaaa....', '...oaaao....', '....ooo.....']),
    ('anger', {'a': '#E23B3B', 'o': '#7A1414'}, [
        '............', '...oo..oo...', '..oao..oao..', '.oaao..oaao.', 'oaao....oaao', 'oo........oo',
        'oo........oo', 'oaao....oaao', '.oaao..oaao.', '..oao..oao..', '...oo..oo...', '............']),
    ('sweat', {'a': '#6EC1F0', 'b': '#E6F7FF', 'o': '#1F5E86'}, [
        '.....oo.....', '....oaao....', '....oaao....', '...oabaao...', '...obaaao...', '..oabaaaao..',
        '..obaaaaao..', '..oaaaaaao..', '..oaaaaaao..', '...oaaaao...', '....oooo....', '............']),
    ('dots1', {'a': '#7D93AA', 'o': '#3D5166'}, [
        '............', '............', '............', '............', '.oo.........', 'oaao........',
        'oaao........', '.oo.........', '............', '............', '............', '............']),
    ('dots2', {'a': '#7D93AA', 'o': '#3D5166'}, [
        '............', '............', '............', '............', '.oo..oo.....', 'oaaooaao....',
        'oaaooaao....', '.oo..oo.....', '............', '............', '............', '............']),
    ('dots3', {'a': '#7D93AA', 'o': '#3D5166'}, [
        '............', '............', '............', '............', '.oo..oo..oo.', 'oaaooaaooaao',
        'oaaooaaooaao', '.oo..oo..oo.', '............', '............', '............', '............']),
    ('sleep', {'a': '#8A7BE0', 'o': '#3B2F7A'}, [
        'oooooo......', 'oaaaao......', 'oooaao......', '..oao.......', '.oao..ooooo.', 'oaao..oaaao.',
        'oaaaaooaao..', 'ooooooaao...', '.....oaaaao.', '.....ooooo..', '............', '............']),
    ('sparkle', {'a': '#F4C542', 'b': '#FFF6C9', 'o': '#8A6410'}, [
        '.....o......', '....oao.....', '....oao.....', '...oaaao....', 'oooaabaaooo.', 'oaaabbbaaao.',
        'oooaabaaooo.', '...oaaao....', '....oao.....', '....oao.....', '.....o......', '............']),
    ('idea', {'a': '#FFE066', 'b': '#FFFBE0', 'c': '#9AA7B4', 'o': '#7A5F10'}, [
        '...oooooo...', '..oaabbaao..', '.oaabbaaaao.', '.oabaaaaaao.', '.oaaaaaaaao.', '..oaaaaaao..',
        '...oaaaao...', '....oaao....', '...oooooo...', '...occcco...', '...oooooo...', '....oooo....']),
    ('gloom', {'a': '#A9B4C2', 'b': '#6E9FD6', 'o': '#4A5563'}, [
        '............', '....oooo....', '..oooaaaoo..', '.oaaaaaaaao.', 'oaaaaaaaaaao', 'oaaaaaaaaaao',
        '.oooooooooo.', '..b...b..b..', '.b...b..b...', '............', '..b...b...b.', '............']),
    ('blush', {'a': '#F39AB0', 'b': '#FFE0E8', 'o': '#B04A68'}, [
        '............', '............', '............', '.oooo..oooo.', 'oaaaaooaaaao', 'oabaaooabaao',
        'oaaaaooaaaao', '.oooo..oooo.', '............', '............', '............', '............']),
]


def rgba(hexcolour):
    h = hexcolour.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def symbols(img):
    for n, (_, colours, rows) in enumerate(SYMBOLS):
        cx, cy = n % 8 * 16 + 2, 32 + n // 8 * 16 + 2
        assert len(rows) == 12 and all(len(r) == 12 for r in rows), _
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != '.':
                    img.putpixel((cx + x, cy + y), rgba(colours[ch]))


def main():
    img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    bubbles(img)
    symbols(img)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sky = Image.new('RGBA', (128, 128), (143, 193, 234, 255))
    sky.alpha_composite(img)
    sky.resize((512, 512), Image.NEAREST).save(PREVIEW)
    print(f'{OUT} ({len(SYMBOLS)} symbols); preview {PREVIEW}')


if __name__ == '__main__':
    main()
