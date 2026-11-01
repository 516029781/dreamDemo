# Batch R1: light direction calibration (art repair plan, A)
import bpy, json, os, time, math
from mathutils import Vector

t0 = time.time()
sc = bpy.context.scene
LOG = {}

# 1) locate sun object
sun_light = next(l for l in bpy.data.lights if l.type == 'SUN')
sun_ob = next(ob for ob in bpy.data.objects if ob.data == sun_light)
LOG['sun_name'] = sun_ob.name
LOG['old_rot'] = [round(a, 3) for a in sun_ob.rotation_euler]
LOG['old_energy'] = sun_light.energy
LOG['old_color'] = [round(c, 3) for c in sun_light.color]

# 2) new direction: propagate toward (-0.40, -0.40, -0.82) => sun at +x/+y high (screen right-back), elevation ~55 deg
#    shadow direction = horizontal part = (-x, -y) = screen lower-left, matching reference
d = Vector((-0.40, -0.40, -0.82)).normalized()
q = d.to_track_quat('-Z', 'Y')
# NOTE: this object uses QUATERNION rotation mode - must set rotation_quaternion (euler is ignored!)
sun_ob.rotation_mode = 'QUATERNION'
sun_ob.rotation_quaternion = q
sun_ob.rotation_euler = q.to_euler()   # keep euler mirror in sync for future edits
LOG['new_dir'] = [round(v, 3) for v in d]

# 3) energy: elevation 35->55 deg raises ground irradiance ~43%; 8.2/1.26 ~ 6.5
sun_light.energy = 6.5
# warmer key
sun_light.color = (1.0, 0.88, 0.72)
LOG['new_energy'] = sun_light.energy
LOG['new_color'] = [round(c, 3) for c in sun_light.color]

# 4) save
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()

# 5) render check frame (50%, 48spp)
sc.cycles.samples = 48
sc.render.resolution_percentage = 50
out = bpy.path.abspath('//renders/repair_batch1_light.png')
sc.render.filepath = out
bpy.ops.render.render(write_still=True)

# 6) side-effect scan: overexposure ratio + top strip color
img = bpy.data.images.load(out)
px = list(img.pixels)
w, h = img.size
tot = over = 0
top_r = top_g = top_b = tn = 0
for yy in range(0, h, 2):
    for xx in range(0, w, 2):
        i = (yy * w + xx) * 4
        r, g, b = px[i], px[i+1], px[i+2]
        tot += 1
        if r > 0.97 and g > 0.97 and b > 0.97:
            over += 1
        if yy > h * 0.7:   # image rows: row 0 is bottom in blender images? top strip = high yy in buffer? use yy > 0.7h as top-half sample
            top_r += r; top_g += g; top_b += b; tn += 1
LOG['overexposed_ratio'] = round(over / max(tot, 1), 4)
LOG['topstrip_rgb'] = [round(top_r / max(tn, 1) * 255), round(top_g / max(tn, 1) * 255), round(top_b / max(tn, 1) * 255)]
LOG['elapsed_s'] = round(time.time() - t0, 1)

with open(bpy.path.abspath('//preflight/R1_LIGHT_LOG.json'), 'w', encoding='utf-8') as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print('R1_DONE', LOG)
