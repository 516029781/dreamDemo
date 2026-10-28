import pathlib

p = pathlib.Path('demo_n5/assets/scripts/CourtyardBootstrap.ts')
s = p.read_text(encoding='utf-8')
s = s.replace("key.illuminance = 178000;", "key.illuminance = 188000;")
s = s.replace("key.color = hexToColor('#FFE3C4');", "key.color = hexToColor('#FFECD8');")
s = s.replace('globals.ambient.skyIllum = 10000;', 'globals.ambient.skyIllum = 11500;')
s = s.replace('globals.ambient.skyColor = new Vec4(0.55, 0.47, 0.40, 1);',
              'globals.ambient.skyColor = new Vec4(0.56, 0.50, 0.45, 1);')
s = s.replace('globals.ambient.groundLightingColor = new Color(140, 96, 64, 255);',
              'globals.ambient.groundLightingColor = new Color(150, 106, 74, 255);')
s = s.replace("ENG_MAT_grass_dry: { tex: 'textures/tex_leaf_detail/texture', color: '#CDB784', rough: 0.72, metal: 0.0 }",
              "ENG_MAT_grass_dry: { tex: 'textures/tex_leaf_detail/texture', color: '#C9B993', rough: 0.72, metal: 0.0 }")
s = s.replace("ENG_MAT_grass_pale: { tex: 'textures/tex_leaf_detail/texture', color: '#E3CFA0', rough: 0.70, metal: 0.0 }",
              "ENG_MAT_grass_pale: { tex: 'textures/tex_leaf_detail/texture', color: '#DED0B0', rough: 0.70, metal: 0.0 }")
p.write_text(s, encoding='utf-8')
print('tone pass 4 applied')
