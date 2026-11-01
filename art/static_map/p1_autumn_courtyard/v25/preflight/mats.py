"""材质反照率设置：按 sRGB 给值，内部转线性。

用法：
    python preflight/mats.py            # 打印当前值
    blender -b scene.blend -P preflight/mats.py

改值改 TARGETS 里的 sRGB。规则见方案 §六：
    目标 A = 当前A × (目标L / 当前L) ^ 2.2
"""
import bpy

TARGETS = {
    # 名称: (sRGB, roughness)
    "P1 tier | low ground": ((112, 102, 88), 0.96),
    "P1 tier | far bank": ((62, 57, 48), 0.95),
    "P1 tier | curb": ((164, 156, 142), 0.82),
}


def srgb2lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def apply(matname, rgb, rough=None):
    m = bpy.data.materials.get(matname)
    if not m:
        print("MISS", matname)
        return None
    if not m.use_nodes:
        m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if not b:
        print("NOBSDF", matname)
        return None
    lin = tuple(srgb2lin(x) for x in rgb)
    b.inputs["Base Color"].default_value = (*lin, 1.0)
    if rough is not None:
        b.inputs["Roughness"].default_value = rough
    return lin


if __name__ == "__main__":
    for name, (rgb, rough) in TARGETS.items():
        lin = apply(name, rgb, rough)
        if lin:
            print("MAT %-28s sRGB%-16s linear %s" % (name, str(rgb), [round(x, 3) for x in lin]))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    print("MATS_DONE")
