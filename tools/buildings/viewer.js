// Voxel preview renderer for End Expansion buildings and villages (three.js r128).
// voxelGroup(data) turns look.export() output into a THREE.Group: one merged mesh of vertex-coloured
// boxes (hidden faces between full cubes culled), shaded like Minecraft (top bright, sides dimmer),
// glass in its own translucent mesh, glowing blocks unshaded.
(function () {
  const SHADE = { top: 1.0, bottom: 0.5, north: 0.8, south: 0.8, east: 0.62, west: 0.62 };
  const FACES = [
    // name, normal, 4 corners as (x,y,z) picks from [x0,x1]x[y0,y1]x[z0,z1]
    ['top', [0, 1, 0], [[0, 1, 0], [1, 1, 0], [1, 1, 1], [0, 1, 1]]],
    ['bottom', [0, -1, 0], [[0, 0, 1], [1, 0, 1], [1, 0, 0], [0, 0, 0]]],
    ['north', [0, 0, -1], [[1, 0, 0], [0, 0, 0], [0, 1, 0], [1, 1, 0]]],
    ['south', [0, 0, 1], [[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]]],
    ['west', [-1, 0, 0], [[0, 0, 0], [0, 0, 1], [0, 1, 1], [0, 1, 0]]],
    ['east', [1, 0, 0], [[1, 0, 1], [1, 0, 0], [1, 1, 0], [1, 1, 1]]],
  ];

  function edgeTexture() {
    const c = document.createElement('canvas'); c.width = c.height = 16;
    const g = c.getContext('2d');
    const img = g.createImageData(16, 16);
    let seed = 7;
    const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) {
      const edge = x === 0 || y === 0 || x === 15 || y === 15;
      const v = Math.round(255 * (edge ? 0.80 : 0.94 + rnd() * 0.06));
      const i = (y * 16 + x) * 4;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
    const t = new THREE.CanvasTexture(c);
    t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter;
    return t;
  }

  function hash(x, y, z) {
    let h = (x * 374761393 + y * 668265263 + z * 2147483647) | 0;
    h = (h ^ (h >>> 13)) * 1274126177;
    return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
  }

  window.voxelGroup = function (data, opts) {
    opts = opts || {};
    const P = data.palette, B = data.blocks;
    const solid = new Set();
    for (let i = 0; i < B.length; i += 4) if (P[B[i + 3]].f) solid.add(B[i] + ',' + B[i + 1] + ',' + B[i + 2]);
    const buckets = { opaque: [[], [], []], glass: [[], [], []] };
    for (let i = 0; i < B.length; i += 4) {
      const x = B[i], y = B[i + 1], z = B[i + 2], e = P[B[i + 3]];
      const bucket = e.a < 1 ? buckets.glass : buckets.opaque;
      const jitter = 0.94 + hash(x, y, z) * 0.08;
      for (const b of e.b) {
        const x0 = x + b[0] / 16, y0 = y + b[1] / 16, z0 = z + b[2] / 16;
        const x1 = x + b[3] / 16, y1 = y + b[4] / 16, z1 = z + b[5] / 16;
        const full = e.f && b[0] === 0 && b[4] === 16 && b[3] === 16 && b[1] === 0;
        for (const [name, n, corners] of FACES) {
          if (full) {
            const k = (x + n[0]) + ',' + (y + n[1]) + ',' + (z + n[2]);
            if (solid.has(k)) continue;
          }
          const base = name === 'top' || name === 'bottom' ? e.t : e.s;
          const s = (e.g ? 1.1 : SHADE[name]) * jitter;
          const r = Math.min(1, base[0] / 255 * s), g = Math.min(1, base[1] / 255 * s), bl = Math.min(1, base[2] / 255 * s);
          const xs = [x0, x1], ys = [y0, y1], zs = [z0, z1];
          const idx = [0, 1, 2, 0, 2, 3];
          const uv = [[0, 0], [1, 0], [1, 1], [0, 1]];
          for (const k of idx) {
            const c = corners[k];
            bucket[0].push(xs[c[0]], ys[c[1]], zs[c[2]]);
            bucket[1].push(r, g, bl);
            bucket[2].push(uv[k][0], uv[k][1]);
          }
        }
      }
    }
    const group = new THREE.Group();
    const tex = edgeTexture();
    for (const [key, arr] of Object.entries(buckets)) {
      if (!arr[0].length) continue;
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(arr[0], 3));
      geo.setAttribute('color', new THREE.Float32BufferAttribute(arr[1], 3));
      geo.setAttribute('uv', new THREE.Float32BufferAttribute(arr[2], 2));
      const mat = new THREE.MeshBasicMaterial({ vertexColors: true, map: tex, side: THREE.DoubleSide });
      if (key === 'glass') { mat.transparent = true; mat.opacity = 0.6; mat.depthWrite = false; }
      const mesh = new THREE.Mesh(geo, mat);
      mesh.renderOrder = key === 'glass' ? 1 : 0;
      group.add(mesh);
    }
    group.userData.size = data.size;
    return group;
  };
})();
