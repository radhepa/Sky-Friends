"""Offline previews of buildings: four corner views plus a cutaway, rendered with headless Edge.

  python tools/buildings/preview.py nest_house               -> tools/buildings/out/nest_house.png
  python tools/buildings/preview.py nest_house --cut 4       cutaway at layer 4 (default: ground + 3)
  python tools/buildings/preview.py --role home              contact sheet of one role's buildings
  python tools/buildings/preview.py --all --check            build every building (runs finish() checks)

Views: the front (north) is toward the camera in the first view. Final checks belong in Minecraft.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kit  # noqa: E402
import look  # noqa: E402

OUT = HERE / 'out'
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
THREE = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"

PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;height:100%;overflow:hidden;background:#8fb8de}
.lab{position:absolute;color:#efe6f5;font:15px monospace;text-shadow:1px 1px 0 #000}
</style></head><body>
<script src="__THREE__"></script>
<script>__VIEWER__</script>
<script>
const ITEMS = __ITEMS__;
const W = innerWidth, H = innerHeight;
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(1); renderer.setSize(W, H); renderer.setScissorTest(true);
renderer.setClearColor(0x8fb8de);
document.body.appendChild(renderer.domElement);
// views: [azimuth degrees (0 = looking at the north face), elevation degrees, use cutaway]
const VIEWS = [[-35, 28, 0], [35, 28, 0], [145, 28, 0], [215, 28, 0], [-35, 62, 1]];
const cols = ITEMS.length > 1 ? Math.ceil(Math.sqrt(ITEMS.length * 1.6)) : VIEWS.length;
const rows = ITEMS.length > 1 ? Math.ceil(ITEMS.length / cols) : 1;
const cw = Math.floor(W / cols), ch = Math.floor(H / rows);
function draw(group, size, az, el, x, y, w, h) {
  const scene = new THREE.Scene(); scene.add(group);
  const [sx, sy, sz] = size;
  group.position.set(-sx / 2, 0, -sz / 2);
  const r = Math.max(sx, sz, sy * 0.9) * 0.9 + 4;
  const cam = new THREE.PerspectiveCamera(30, w / h, 0.1, 2000);
  const a = az * Math.PI / 180, e = el * Math.PI / 180;
  const dist = r / Math.tan(15 * Math.PI / 180) * 0.62;
  const ty = sy * 0.38;
  cam.position.set(Math.sin(a) * Math.cos(e) * dist, ty + Math.sin(e) * dist, -Math.cos(a) * Math.cos(e) * dist);
  cam.lookAt(0, ty, 0);
  renderer.setViewport(x, H - y - h, w, h); renderer.setScissor(x, H - y - h, w, h);
  renderer.render(scene, cam);
}
ITEMS.forEach((it, i) => {
  if (ITEMS.length === 1) {
    VIEWS.forEach((v, k) => {
      const g = voxelGroup(v[2] ? it.cut : it.full);
      const vw = Math.floor(W / 3), vh = Math.floor(H / 2);
      const x = (k % 3) * vw, y = Math.floor(k / 3) * vh;
      draw(g, it.full.size, v[0], v[1], x, y, vw, vh);
      const lab = document.createElement('div'); lab.className = 'lab';
      lab.style.left = (x + 8) + 'px'; lab.style.top = (y + 6) + 'px';
      lab.textContent = k === 0 ? it.name + '  ' + it.full.size.join('x') + (k === 4 ? '' : '') : (v[2] ? 'cutaway' : '');
      document.body.appendChild(lab);
    });
    const lab = document.createElement('div'); lab.className = 'lab';
    lab.style.left = (2 * Math.floor(W / 3) + 12) + 'px'; lab.style.top = (Math.floor(H / 2) + 12) + 'px';
    lab.style.whiteSpace = 'pre'; lab.textContent = it.info; document.body.appendChild(lab);
  } else {
    const x = (i % cols) * cw, y = Math.floor(i / cols) * ch;
    draw(voxelGroup(it.full), it.full.size, -35, 28, x, y, cw, ch);
    const lab = document.createElement('div'); lab.className = 'lab';
    lab.style.left = (x + 6) + 'px'; lab.style.top = (y + 4) + 'px'; lab.textContent = it.name;
    document.body.appendChild(lab);
  }
});
document.title = 'done';
</script></body></html>"""


def shoot(html, out_png, size):
    OUT.mkdir(exist_ok=True)
    page = OUT / (Path(out_png).stem + '.html')
    page.write_text(html, encoding='utf-8')
    if os.path.exists(out_png):
        os.remove(out_png)
    prof = str(OUT / ('_prof_' + Path(out_png).stem))
    subprocess.run([EDGE, '--headless=new', '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--hide-scrollbars',
                    f'--window-size={size[0]},{size[1]}', '--virtual-time-budget=15000', f'--user-data-dir={prof}',
                    f'--screenshot={out_png}', page.as_uri()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    for _ in range(120):
        if os.path.exists(out_png) and os.path.getsize(out_png) > 0:
            time.sleep(0.4)
            break
        time.sleep(0.5)
    return out_png


def info(b):
    m = b.meta
    counts = {}
    for s in b.grid.values():
        if not kit.is_air(s):
            counts[kit.bid(s)] = counts.get(kit.bid(s), 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:10]
    lines = [f"{m.get('people', '')} {m.get('role', '')}  residents {m.get('residents', 0)}  door x={m.get('door')}",
             f"{sum(counts.values())} blocks"] + [f"  {n} {c}" for n, c in top]
    return '\n'.join(lines)


def render(names, out_png, cut=None, size=None):
    items = []
    for name in names:
        b = kit.make(name)
        c = b.ground + 3 if cut is None else cut
        items.append({'name': name, 'full': look.export(b), 'cut': look.export(b, cut=c), 'info': info(b)})
    html = (PAGE.replace('__THREE__', THREE).replace('__VIEWER__', (HERE / 'viewer.js').read_text(encoding='utf-8'))
            .replace('__ITEMS__', json.dumps(items)))
    size = size or ((1500, 900) if len(items) == 1 else (1800, 1100))
    return shoot(html, str(out_png), size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='*')
    ap.add_argument('--role')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--check', action='store_true', help='only build (runs the finish() checks), no pictures')
    ap.add_argument('--cut', type=int)
    ap.add_argument('--out')
    args = ap.parse_args()
    catalog = kit.load_all()
    names = list(args.names)
    if args.role:
        names += [n for n, s in catalog.items() if s['role'] == args.role]
    if args.all:
        names = list(catalog)
    if args.check:
        for n in names:
            b = kit.make(n)
            print(f'ok {n:28s} {b.w}x{b.h}x{b.d}  {sum(1 for s in b.grid.values() if not kit.is_air(s))} blocks')
        return
    if not names:
        ap.error('name a building, --people or --all')
    if len(names) == 1:
        out = args.out or OUT / f'{names[0]}.png'
    else:
        out = args.out or OUT / f'sheet_{args.role or "all"}.png'
    print(render(names, out, cut=args.cut))


if __name__ == '__main__':
    main()
