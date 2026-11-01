"""按六个锚点区域，统计场景中实际存在哪些对象（投影中心落在区域内）。

输出 CONTENT_CENSUS.json：每个区域的对象清单 + 投影面积占比。
只读，不改场景。
"""
import bpy
import json
import os
from bpy_extras.object_utils import world_to_camera_view as w2c
from mathutils import Vector

ROOT = r"C:/软件/鼠鼠/art/static_map/p1_autumn_courtyard/v22"

ANCHORS = {
    "左树":        (0.05, 0.03, 0.30, 0.46),
    "前景台阶栏杆": (0.13, 0.67, 0.40, 1.00),
    "主石板平台":   (0.00, 0.51, 0.76, 0.88),
    "中景设施":     (0.32, 0.28, 0.55, 0.55),
    "右侧圆筒草池": (0.50, 0.14, 1.00, 0.63),
    "冷色远景":     (0.30, 0.13, 0.54, 0.27),
}

sc = bpy.context.scene
cam = sc.camera
W, H = sc.render.resolution_x, sc.render.resolution_y
ASPECT = W / H


def project(ob):
    """返回 (u0,u1,v0,v1, area)，v 以左上为原点。完全在相机后则 None。"""
    us, vs = [], []
    for c in ob.bound_box:
        p = w2c(sc, cam, ob.matrix_world @ Vector(c))
        if p.z <= 0:
            continue
        us.append(p.x)
        vs.append(1.0 - p.y)
    if not us:
        return None
    u0, u1 = min(us), max(us)
    v0, v1 = min(vs), max(vs)
    return u0, u1, v0, v1, max(0.0, u1 - u0) * max(0.0, v1 - v0)


def inside(u, v, box):
    return box[0] <= u <= box[2] and box[1] <= v <= box[3]


out = {"anchors": {}, "camera": {}, "counts": {}}
out["camera"] = {
    "loc": [round(x, 3) for x in cam.matrix_world.translation],
    "lens": cam.data.lens,
    "pitch_deg": round(__import__("math").degrees(
        cam.rotation_euler.x - 1.5707963267948966) * -1, 3),
}

for name, box in ANCHORS.items():
    hits = []
    for ob in sc.objects:
        if ob.type not in {"MESH", "CURVE"}:
            continue
        if ob.hide_render:
            continue
        pr = project(ob)
        if not pr:
            continue
        u0, u1, v0, v1, area = pr
        cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
        if not inside(cu, cv, box):
            continue
        # 与区域的重叠面积比
        iu0, iu1 = max(u0, box[0]), min(u1, box[2])
        iv0, iv1 = max(v0, box[1]), min(v1, box[3])
        ov = max(0, iu1 - iu0) * max(0, iv1 - iv0)
        hits.append({
            "name": ob.name,
            "proj": [round(u0, 3), round(u1, 3), round(v0, 3), round(v1, 3)],
            "overlap": round(ov, 5),
            "area": round(area, 5),
            "verts": len(ob.data.vertices) if hasattr(ob.data, "vertices") else 0,
            "mats": [m.name for m in ob.data.materials if m] if hasattr(ob.data, "materials") else [],
        })
    hits.sort(key=lambda h: -h["overlap"])
    total = sum(h["overlap"] for h in hits)
    out["anchors"][name] = {
        "box": box,
        "n_objects": len(hits),
        "sum_overlap": round(total, 4),
        "objects": hits[:40],
    }
    out["counts"][name] = len(hits)
    print(f"=== {name}  box={box}  对象 {len(hits)}  合计投影 {total*100:.1f}%")
    for h in hits[:10]:
        print(f"    {h['name'][:46]:48s} uv[{h['proj'][0]:.2f},{h['proj'][1]:.2f}]"
              f" v[{h['proj'][2]:.2f},{h['proj'][3]:.2f}] ov={h['overlap']*100:.2f}%")

p = os.path.join(ROOT, "preflight", "CONTENT_CENSUS.json")
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", p)
