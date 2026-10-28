import pathlib

p = pathlib.Path('demo_n5/assets/scripts/CourtyardBootstrap.ts')
s = p.read_text(encoding='utf-8')

# Stone gets a tighter specular so the key light produces real highlights.
s = s.replace("ENG_MAT_stone_base: { tex: 'textures/tex_stone_tiles/texture', color: '#A2907A', rough: 0.90, metal: 0.0 }",
              "ENG_MAT_stone_base: { tex: 'textures/tex_stone_tiles/texture', color: '#A2907A', rough: 0.62, metal: 0.0 }")
s = s.replace("ENG_MAT_stone_light: { tex: 'textures/tex_stone_tiles/texture', color: '#B7A488', rough: 0.86, metal: 0.0 }",
              "ENG_MAT_stone_light: { tex: 'textures/tex_stone_tiles/texture', color: '#D6C6AC', rough: 0.58, metal: 0.0 }")
s = s.replace("ENG_MAT_stone_dark: { tex: 'textures/tex_stone_tiles/texture', color: '#6B5B4A', rough: 0.94, metal: 0.0 }",
              "ENG_MAT_stone_dark: { tex: 'textures/tex_stone_tiles/texture', color: '#6B5B4A', rough: 0.72, metal: 0.0 }")
s = s.replace("ENG_MAT_mortar: { tex: 'textures/tex_stone_tiles/texture', color: '#75685A', rough: 0.96, metal: 0.0 }",
              "ENG_MAT_mortar: { tex: 'textures/tex_stone_tiles/texture', color: '#75685A', rough: 0.86, metal: 0.0 }")

# Key light less yellow: the frame's 30-60 deg share and saturation both come
# from an over-warm key multiplying every albedo.
s = s.replace("key.color = hexToColor('#FFD9AE');", "key.color = hexToColor('#FFE3C4');")
p.write_text(s, encoding='utf-8')
print('specular + neutral key', "'#FFE3C4'" in s)
