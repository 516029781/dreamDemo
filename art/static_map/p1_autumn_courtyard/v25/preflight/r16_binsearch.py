# R14: binary-search the orange board object by hide-render + pixel count
import bpy, os, json, time
sc = bpy.context.scene

ORANGE_BOX = (0.16, 0.28, 0.30, 0.36)   # u0-u1, v_top0-v1 core of the orange board

def count_orange():
    # read back the just-rendered result via a temp save of RenderResult is not possible;
    # instead render writes file, then PIL reads it outside. Here we store filepath.
    return None

meshes = [ob for ob in sc.objects if ob.type == 'MESH']
sc.cycles.samples = 16
sc.render.resolution_percentage = 40

def render_count(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    # count via blender's image load (no PIL in blender python)
    img = bpy.data.images.load(path)
    px = list(img.pixels)
    w, h = img.size
    x0, x1 = int(ORANGE_BOX[0]*w), int(ORANGE_BOX[1]*w)
    y0, y1 = int((1-ORANGE_BOX[3])*h), int((1-ORANGE_BOX[2])*h)
    n = 0
    tot = 0
    for yy in range(y0, y1, 2):
        for xx in range(x0, x1, 2):
            i = (yy*w + xx)*4
            r, g, b = px[i], px[i+1], px[i+2]
            # blender image buffers are linear; orange board linear approx (0.64,0.30,0.10)
            tot += 1
            if r > 0.70 and 0.50 < g < 0.65 and 0.25 < b < 0.40 and (r - b) > 0.30:
                n += 1
    bpy.data.images.remove(img)
    return n, tot

base_path = bpy.path.abspath('//renders/r16_base.png')
base, tot = render_count(base_path)
print('BASE orange=%d / %d' % (base, tot))

lo, hi = 0, len(meshes)
rounds = 0
t0 = time.time()
while hi - lo > 1 and rounds < 14:
    mid = (lo + hi) // 2
    grp = meshes[lo:mid]
    for ob in grp:
        ob.hide_render = True
    p = bpy.path.abspath('//renders/r16_b.png')
    n, _ = render_count(p)
    for ob in grp:
        ob.hide_render = False
    rounds += 1
    print('ROUND %d hide[%d:%d] orange=%d (base %d)' % (rounds, lo, mid, n, base))
    if n < base * 0.5:      # board disappeared -> culprit in [lo, mid)
        hi = mid
    else:                    # still there -> in [mid, hi)
        lo = mid
print('CULPRIT_RANGE [%d:%d]' % (lo, hi))
for ob in meshes[lo:hi]:
    print('CANDIDATE:', ob.name)
print('R14_DONE elapsed=%.0fs' % (time.time()-t0))
