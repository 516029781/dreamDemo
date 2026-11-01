# -*- coding: utf-8 -*-
"""探测灯光 rig、world、关键材质与渲染设置。只读。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
out = {"lights": [], "world": {}, "render": {}, "materials": []}

for ob in sc.objects:
    if ob.type != "LIGHT":
        continue
    L = ob.data
    out["lights"].append({
        "name": ob.name,
        "type": L.type,
        "energy": round(L.energy, 3),
        "color": [round(c, 4) for c in L.color],
        "loc": [round(v, 3) for v in ob.matrix_world.translation],
        "rot": [round(v, 4) for v in ob.rotation_euler],
        "angle_deg": round(__import__("math").degrees(L.angle), 2) if hasattr(L, "angle") else None,
        "use_shadow": L.use_shadow,
        "size": round(L.size, 3) if hasattr(L, "size") else None,
    })

w = sc.world
if w and w.use_nodes:
    for n in w.node_tree.nodes:
        if n.type == "BACKGROUND":
            out["world"] = {
                "strength": round(n.inputs["Strength"].default_value, 4),
                "color": [round(c, 4) for c in n.inputs["Color"].default_value],
            }
out["world"]["use_nodes"] = bool(w and w.use_nodes)

r = sc.render
out["render"] = {
    "engine": r.engine,
    "res": [r.resolution_x, r.resolution_y, r.resolution_percentage],
    "view_transform": sc.view_settings.view_transform,
    "look": sc.view_settings.look,
    "exposure": sc.view_settings.exposure,
    "gamma": sc.view_settings.gamma,
}
if r.engine == "CYCLES":
    out["render"]["samples"] = sc.cycles.samples
    out["render"]["denoise"] = sc.cycles.use_denoising
    out["render"]["max_bounces"] = sc.cycles.max_bounces
    out["render"]["diffuse_bounces"] = sc.cycles.diffuse_bounces
    out["render"]["glossy_bounces"] = sc.cycles.glossy_bounces

for m in bpy.data.materials:
    if m.use_nodes and not m.name.startswith("__"):
        nodes = [n.type for n in m.node_tree.nodes]
        out["materials"].append({"name": m.name, "nodes": nodes,
                                 "users": m.users})
out["materials"].sort(key=lambda d: -d["users"])

with open(os.path.join(PRE, "C3_LIGHT_PROBE.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("LIGHTS:")
for L in out["lights"]:
    print(" ", json.dumps(L, ensure_ascii=False))
print("WORLD:", json.dumps(out["world"], ensure_ascii=False))
print("RENDER:", json.dumps(out["render"], ensure_ascii=False))
print("MATERIALS top20:")
for m in out["materials"][:20]:
    print(f'  {m["users"]:3d}  {m["name"]}')
