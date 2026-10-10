"""Read a gzipped structure template back (for checks): python tools/buildings/nbtread.py <file.nbt> [x y z]"""
import gzip
import struct
import sys


def _read(buf, i, kind):
    if kind == 1:
        return struct.unpack_from('>b', buf, i)[0], i + 1
    if kind == 2:
        return struct.unpack_from('>h', buf, i)[0], i + 2
    if kind == 3:
        return struct.unpack_from('>i', buf, i)[0], i + 4
    if kind == 4:
        return struct.unpack_from('>q', buf, i)[0], i + 8
    if kind == 5:
        return struct.unpack_from('>f', buf, i)[0], i + 4
    if kind == 6:
        return struct.unpack_from('>d', buf, i)[0], i + 8
    if kind == 7:
        n = struct.unpack_from('>i', buf, i)[0]
        return buf[i + 4:i + 4 + n], i + 4 + n
    if kind == 8:
        n = struct.unpack_from('>H', buf, i)[0]
        return buf[i + 2:i + 2 + n].decode('utf-8'), i + 2 + n
    if kind == 9:
        et, n = buf[i], struct.unpack_from('>i', buf, i + 1)[0]
        i += 5
        out = []
        for _ in range(n):
            v, i = _read(buf, i, et)
            out.append(v)
        return out, i
    if kind == 10:
        out = {}
        while True:
            t = buf[i]
            i += 1
            if t == 0:
                return out, i
            n = struct.unpack_from('>H', buf, i)[0]
            name = buf[i + 2:i + 2 + n].decode('utf-8')
            i += 2 + n
            out[name], i = _read(buf, i, t)
    if kind == 11:
        n = struct.unpack_from('>i', buf, i)[0]
        return list(struct.unpack_from(f'>{n}i', buf, i + 4)), i + 4 + 4 * n
    if kind == 12:
        n = struct.unpack_from('>i', buf, i)[0]
        return list(struct.unpack_from(f'>{n}q', buf, i + 4)), i + 4 + 8 * n
    raise ValueError(kind)


def load(path):
    buf = gzip.open(path).read()
    assert buf[0] == 10
    n = struct.unpack_from('>H', buf, 1)[0]
    data, _ = _read(buf, 3 + n, 10)
    return data


if __name__ == '__main__':
    d = load(sys.argv[1])
    print('size', d['size'], 'palette', len(d['palette']), 'blocks', len(d['blocks']), 'entities', len(d['entities']))
    if len(sys.argv) > 4:
        x, y, z = map(int, sys.argv[2:5])
        for b in d['blocks']:
            if b['pos'] == [x, y, z]:
                print('at', [x, y, z], d['palette'][b['state']])
        print('palette 0..5', d['palette'][:6])
