import pathlib

p = pathlib.Path('demo_n5/assets/scripts/CourtyardBootstrap.ts')
s = p.read_text(encoding='utf-8')
pairs = {
    "'#A79B88'": "'#A2907A'",
    "'#BDB09B'": "'#B7A488'",
    "'#6F6455'": "'#6B5B4A'",
    "'#7E7364'": "'#75685A'",
    "'#D3BF88'": "'#CDB784'",
    "'#E7D5A4'": "'#E3CFA0'",
}
for a, b in pairs.items():
    assert a in s, a
    s = s.replace(a, b)
s = s.replace('globals.ambient.skyIllum = 11000;', 'globals.ambient.skyIllum = 10000;')
s = s.replace('key.illuminance = 168000;', 'key.illuminance = 178000;')
p.write_text(s, encoding='utf-8')
print('tone pass 2 applied')

# Blender palette in sync
q = pathlib.Path('tools/blender_n5/courtyard_lib.py')
t = q.read_text(encoding='utf-8')
bpairs = {
    '"stone_base": "#A79B88"': '"stone_base": "#A2907A"',
    '"stone_light": "#BDB09B"': '"stone_light": "#B7A488"',
    '"stone_dark": "#6F6455"': '"stone_dark": "#6B5B4A"',
    '"mortar": "#7E7364"': '"mortar": "#75685A"',
    '"grass_dry": "#D3BF88"': '"grass_dry": "#CDB784"',
    '"grass_pale": "#E7D5A4"': '"grass_pale": "#E3CFA0"',
}
for a, b in bpairs.items():
    assert a in t, a
    t = t.replace(a, b)
q.write_text(t, encoding='utf-8')
print('blender palette synced')
