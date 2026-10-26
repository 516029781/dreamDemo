"""Audit the delivered GLB for the two geometry defects the rework spec names.

`REWORK_EXECUTION_SPEC` N01 asks to clear "floating leaf cards and duplicate
coplanar faces" but never says how many there are, so the fix has no before and
after. This counts them straight from the GLB:

  duplicate  same three vertex positions, same winding, in the same mesh
  degenerate zero-area triangle (reads as a hard sliver when shaded)
  coplanar   duplicate triangles that also share a normal -> z-fighting pair

Usage:  python tools/audit_glb_geometry.py [glb] [--json out.json]
"""
import json
import struct
import sys
import os
from collections import defaultdict

COMP = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2),
        5125: ('I', 4), 5126: ('f', 4)}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load_glb(path):
    with open(path, 'rb') as f:
        magic, ver, length = struct.unpack('<III', f.read(12))
        assert magic == 0x46546C67, 'not a glb: %s' % path
        clen, ctype = struct.unpack('<II', f.read(8))
        js = json.loads(f.read(clen).decode('utf-8'))
        blen, btype = struct.unpack('<II', f.read(8))
        bin_chunk = f.read(blen)
    return js, bin_chunk


def read_accessor(js, bin_chunk, idx):
    acc = js['accessors'][idx]
    n = acc['count']
    ncomp = NCOMP[acc['type']]
    fmt, size = COMP[acc['componentType']]
    bv = js['bufferViews'][acc['bufferView']]
    base = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = bv.get('byteStride') or ncomp * size
    out = []
    for i in range(n):
        off = base + i * stride
        vals = struct.unpack_from('<' + fmt * ncomp, bin_chunk, off)
        out.append(vals if ncomp > 1 else vals[0])
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') \
        else 'demo_n5/assets/resources/models/MAP001_courtyard.glb'
    js, bin_chunk = load_glb(path)
    report = {'file': path, 'meshes': []}
    tot_dup = tot_deg = tot_tri = 0
    for mesh in js['meshes']:
        name = mesh.get('name', '?')
        dup = deg = tri = 0
        for prim in mesh.get('primitives', []):
            idx = prim.get('indices')
            pos_i = prim['attributes']['POSITION']
            if idx is None:
                continue
            pos = read_accessor(js, bin_chunk, pos_i)
            ind = read_accessor(js, bin_chunk, idx)
            tri += len(ind) // 3
            seen = defaultdict(int)
            for t in range(0, len(ind) - 2, 3):
                a, b, c = ind[t], ind[t + 1], ind[t + 2]
                pa, pb, pc = pos[a], pos[b], pos[c]
                # zero-area: any two corners coincide, or the cross product
                # has no length
                u = (pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2])
                v = (pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2])
                cx = u[1] * v[2] - u[2] * v[1]
                cy = u[2] * v[0] - u[0] * v[2]
                cz = u[0] * v[1] - u[1] * v[0]
                if cx * cx + cy * cy + cz * cz < 1e-12:
                    deg += 1
                # duplicate: sort the three corners so winding is preserved
                # as a cyclic order, then key on rounded positions
                corners = [tuple(round(x, 4) for x in p) for p in (pa, pb, pc)]
                k = min(range(3), key=lambda i: corners[i])
                corners = tuple(corners[k:] + corners[:k])
                seen[corners] += 1
            dup += sum(n - 1 for n in seen.values() if n > 1)
        tot_dup += dup
        tot_deg += deg
        tot_tri += tri
        report['meshes'].append({'name': name, 'triangles': tri,
                                 'exact_duplicates': dup,
                                 'degenerate': deg})
    report['totals'] = {'triangles': tot_tri, 'exact_duplicates': tot_dup,
                        'degenerate': tot_deg}
    bad = [m for m in report['meshes'] if m['exact_duplicates'] or m['degenerate']]
    bad.sort(key=lambda m: -(m['exact_duplicates'] + m['degenerate']))
    print('%-42s %9s %9s %9s' % ('mesh', 'tris', 'dup', 'degenerate'))
    for m in bad[:20]:
        print('%-42s %9d %9d %9d' % (m['name'][:42], m['triangles'],
                                     m['exact_duplicates'], m['degenerate']))
    if not bad:
        print('(no duplicates or degenerate triangles)')
    print('TOTAL tris=%d dup=%d degenerate=%d  meshes=%d  offenders=%d'
          % (tot_tri, tot_dup, tot_deg, len(report['meshes']), len(bad)))
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(report, open(out, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('wrote', out)


if __name__ == '__main__':
    main()
