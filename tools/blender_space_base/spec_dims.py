"""Frozen dimensions for space_base_minigame v01.

All values in metres. Source: SPACE_BASE_MASTER_SPEC_20261102.md v1.3.
Do not edit scene coordinates in build_scene.py; import from here.
"""
from __future__ import annotations

WORLD = {"x0": 0.0, "x1": 240.0, "y0": -190.0, "y1": 190.0, "z0": 0.0}

CORE = {"x0": 0.0, "x1": 240.0, "y0": 0.0, "y1": 190.0}
GARDEN = {"x0": 0.0, "x1": 240.0, "y0": -30.0, "y1": 0.0}
ROAD = {"x0": 108.0, "x1": 132.0, "y0": -60.0, "y1": -30.0}
WORKSHOP = {"x0": 35.0, "x1": 205.0, "y0": -190.0, "y1": -60.0}

ROOMS = {
    "H1": {"x0": 0.0, "x1": 70.0, "y0": 0.0, "y1": 70.0, "wall_h": 9.0},
    "H2": {"x0": 0.0, "x1": 70.0, "y0": 120.0, "y1": 190.0, "wall_h": 10.0},
    "H3": {"x0": 170.0, "x1": 240.0, "y0": 120.0, "y1": 190.0, "wall_h": 11.0},
    "H4": {"x0": 170.0, "x1": 240.0, "y0": 0.0, "y1": 70.0, "wall_h": 13.0},
}

# Horizontal wall: y fixed, x from -> to, openings are (a,b) along x.
# Vertical wall: x fixed, y from -> to, openings are (a,b) along y.
WALL_T = 0.6
DOORS = {
    "H1_north": {"axis": "h", "fixed": 70.0, "a": 0.0, "b": 70.0, "open": [(32.0, 38.0)], "h": 9.0},
    "H1_east":  {"axis": "v", "fixed": 70.0, "a": 0.0, "b": 70.0, "open": [(32.0, 38.0)], "h": 9.0},
    "H1_south": {"axis": "h", "fixed": 0.0,  "a": 0.0, "b": 70.0, "open": [(32.0, 38.0)], "h": 9.0},
    "H1_west":  {"axis": "v", "fixed": 0.0,  "a": 0.0, "b": 70.0, "open": [], "h": 9.0},
    "H2_south": {"axis": "h", "fixed": 120.0,"a": 0.0, "b": 70.0, "open": [(32.0, 38.0)], "h": 10.0},
    "H2_east":  {"axis": "v", "fixed": 70.0, "a": 120.0,"b": 190.0,"open": [(152.0,158.0)], "h": 10.0},
    "H2_north": {"axis": "h", "fixed": 190.0,"a": 0.0, "b": 70.0, "open": [], "h": 10.0},
    "H2_west":  {"axis": "v", "fixed": 0.0,  "a": 120.0,"b": 190.0,"open": [], "h": 10.0},
    "H3_west":  {"axis": "v", "fixed": 170.0,"a": 120.0,"b": 190.0,"open": [(152.0,158.0)], "h": 11.0},
    "H3_south": {"axis": "h", "fixed": 120.0,"a": 170.0,"b": 240.0,"open": [(202.0,208.0)], "h": 11.0},
    "H3_north": {"axis": "h", "fixed": 190.0,"a": 170.0,"b": 240.0,"open": [], "h": 11.0},
    "H3_east":  {"axis": "v", "fixed": 240.0,"a": 120.0,"b": 190.0,"open": [], "h": 11.0},
    "H4_north": {"axis": "h", "fixed": 70.0, "a": 170.0,"b": 240.0,"open": [(202.0,208.0)], "h": 13.0},
    "H4_west":  {"axis": "v", "fixed": 170.0,"a": 0.0, "b": 70.0, "open": [(32.0, 38.0)], "h": 13.0},
    "H4_south": {"axis": "h", "fixed": 0.0,  "a": 170.0,"b": 240.0,"open": [(202.0,208.0)], "h": 13.0},
    "H4_east":  {"axis": "v", "fixed": 240.0,"a": 0.0, "b": 70.0, "open": [], "h": 13.0},
    "W_outer":  {"axis": "v", "fixed": 0.0,  "a": 70.0, "b": 120.0,"open": [], "h": 6.0},
    "E_outer":  {"axis": "v", "fixed": 240.0,"a": 70.0, "b": 120.0,"open": [], "h": 6.0},
    "N_outer":  {"axis": "h", "fixed": 190.0,"a": 70.0, "b": 170.0,"open": [], "h": 6.0},
    "S_outer":  {"axis": "h", "fixed": 0.0,  "a": 70.0, "b": 170.0,"open": [], "h": 6.0},
}

CENTRAL = {"x0": 70.0, "x1": 170.0, "y0": 70.0, "y1": 120.0, "h": 9.0}
CEO = {"x0": 100.0, "x1": 140.0, "y0": 90.0, "y1": 120.0, "z0": 9.0, "z1": 13.5}
STAIRS = {
    "H2": {"x": 68.0, "y": 122.0, "size": 3.0, "h": 9.0},
    "H4": {"x": 172.0, "y": 68.0, "size": 3.0, "h": 9.0},
}
BRIDGES = [
    {"x": 69.0, "y": 121.0, "w": 1.2, "l": 4.0, "z": 9.0, "rot_z": 45.0},
    {"x": 171.0, "y": 69.0, "w": 1.2, "l": 4.0, "z": 9.0, "rot_z": 45.0},
]
ROOF_RAIL = {"x0": 100.0, "x1": 140.0, "y": 88.5, "h": 1.1}

GARDEN_POOL = {"x0": 100.0, "x1": 140.0, "y0": -16.0, "y1": -8.0, "depth": 0.4}
FOUNTAINS = [{"x": 110.0, "y": -12.0, "r": 3.0, "h": 0.6}, {"x": 130.0, "y": -12.0, "r": 3.0, "h": 0.6}]
TREE_PITS = [(40.0, -10.0), (200.0, -10.0), (80.0, -22.0), (160.0, -22.0)]
BENCHES = [(95.0, -27.0), (145.0, -27.0), (120.0, -5.0)]
GARDEN_LAMPS = [(60.0, -15.0), (180.0, -15.0), (105.0, -28.0), (135.0, -28.0)]

ROAD_GATE = {"y": -36.0, "x0": 114.0, "x1": 126.0, "beam_z": 5.0, "beam_t": 0.5}
ROAD_BOOTH = {"x": 112.0, "y": -42.0, "w": 3.0, "d": 3.0, "h": 3.2}
ROAD_BARRIER = {"x": 116.0, "y": -43.0, "arm": 8.0}
ROAD_PIPE = {"y": -49.0, "x0": 108.0, "x1": 132.0, "z": 5.2, "dia": 0.5}
ROAD_BOLLARDS = [(109.0, -34.0), (109.0, -44.0), (109.0, -54.0), (131.0, -39.0), (131.0, -49.0), (131.0, -57.0)]
ROAD_PALLETS = [(127.0, -35.0), (129.0, -39.0)]
ROAD_LAMPS = [(109.0, -38.0), (131.0, -52.0)]
ROAD_SIGN = (111.0, -37.0)
ROAD_T16 = {"x0": 114.0, "x1": 122.0, "y": -62.0, "h": 1.1}
ROAD_T18 = (128.0, -64.0)

WS_PIT = {"x": 145.0, "y": -150.0, "w": 30.0, "d": 18.0, "depth": 2.0}
WS_CONTAINERS = [(43.0, -170.0), (43.0, -160.0), (43.0, -150.0), (43.0, -140.0), (65.0, -70.0), (75.0, -70.0)]
WS_COVER = [(170.0, -140.0), (182.0, -128.0)]
WS_PIPE = {"x0": 35.0, "x1": 95.0, "y": -165.0, "dia": 0.6, "n": 4}
WS_EVAC = (195.0, -180.0)
WS_TERMINAL = (203.0, -180.0)
WS_T18 = (128.0, -64.0)

PALETTE = {
    "structure_white": "#CFD5D6",
    "concrete": "#979C9C",
    "mid_grey": "#676D6E",
    "steel": "#3B4344",
    "near_black": "#222B2D",
    "haavk_green": "#3E9B63",
    "teal": "#17707C",
    "blue_light": "#2F5C9C",
    "orange": "#C87A30",
    "warning_yellow": "#D6A62B",
    "brass": "#AA8355",
    "dark_stone": "#3A322A",
    "garden_green": "#172A22",
    "sky": "#D8DEE0",
}

CAMERA = {
    "location": (120.0, 568.23, 819.2),
    "rotation_deg": (35.0, 0.0, 180.0),
    "ortho_scale": 240.0,
    "sensor_fit": "HORIZONTAL",
    "resolution": (1920, 2560),
    "master_resolution": (3840, 5120),
    "clip_start": 0.1,
    "clip_end": 5000.0,
}
