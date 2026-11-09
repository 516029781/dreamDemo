# -*- coding: utf-8 -*-
"""v3.8 走位距离复核：房间互达 / 撤离路线 / 总裁捷径。北朝上，y 向北为正。"""
import math, heapq

def L(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def poly(pts):
    return sum(L(pts[i], pts[i + 1]) for i in range(len(pts) - 1))

# ---------- 1. 房间互达 ----------
H1, H2, H3, H4 = (90, 30), (90, 90), (150, 90), (150, 30)
G1, G2, E1, E2, E3, E4 = (90, 60), (150, 60), (90, 0), (150, 0), (90, 120), (150, 120)
CW, CE, CS, CN = 53, 187, -7, 127

pt = {
    'H1': H1, 'H2': H2, 'H3': H3, 'H4': H4,
    'G1': G1, 'G2': G2, 'E1': E1, 'E2': E2, 'E3': E3, 'E4': E4,
    'P_E1': (90, CS), 'P_E2': (150, CS), 'P_E3': (90, CN), 'P_E4': (150, CN),
    'C_SW': (CW, CS), 'C_SE': (CE, CS), 'C_NE': (CE, CN), 'C_NW': (CW, CN),
}
G = {k: {} for k in pt}
def link(a, b):
    d = L(pt[a], pt[b]); G[a][b] = d; G[b][a] = d

for a, b in [('H1', 'G1'), ('H2', 'G1'), ('H3', 'G2'), ('H4', 'G2'),
             ('H1', 'E1'), ('H2', 'E3'), ('H4', 'E2'), ('H3', 'E4'),
             ('E1', 'P_E1'), ('E2', 'P_E2'), ('E3', 'P_E3'), ('E4', 'P_E4'),
             ('P_E1', 'C_SW'), ('P_E1', 'C_SE'), ('P_E2', 'C_SE'),
             ('C_SW', 'C_NW'), ('C_SE', 'C_NE'), ('C_NE', 'C_NW'),
             ('P_E3', 'C_NW'), ('P_E3', 'C_NE'), ('P_E4', 'C_NE'),
             ('P_E1', 'P_E2'), ('P_E3', 'P_E4'),
             ('P_E1', 'C_NW'), ('P_E2', 'C_NE'),
             ('C_SW', 'P_E3'), ('C_SE', 'P_E4')]:
    link(a, b)

def dist(src, dst, allow_rooms=True):
    blocked = set() if allow_rooms else {'H1', 'H2', 'H3', 'H4'} - {src, dst}
    pq = [(0.0, src)]; best = {src: 0.0}
    while pq:
        d, u = heapq.heappop(pq)
        if u == dst: return d
        if d > best.get(u, 1e9): continue
        for v, w in G[u].items():
            if v in blocked: continue
            nd = d + w
            if nd < best.get(v, 1e9):
                best[v] = nd; heapq.heappush(pq, (nd, v))
    return None

print('== 房间互达（中心→中心，可穿组内门）==')
for a, b in [('H1','H2'), ('H3','H4'), ('H1','H4'), ('H2','H3'), ('H1','H3'), ('H2','H4')]:
    print(f'  {a}→{b}: {dist(a,b):.1f} m')
print('== 纯绕外圈（不穿房间）==')
for a, b in [('H1','H3'), ('H2','H4')]:
    print(f'  {a}→{b}: {dist(a,b,False):.1f} m')

# ---------- 2. 撤离路线 ----------
F = (120, -39); R = 13
def arc(p_in, p_out, steps=16):
    start = math.pi / 2
    end = math.atan2(p_out[1] - F[1], p_out[0] - F[0])
    sweep = start - end
    pts = [p_in]
    for i in range(steps + 1):
        a = start - sweep * i / steps
        pts.append((F[0] + R * math.cos(a), F[1] + R * math.sin(a)))
    pts.append(p_out)
    return pts

garden_in, garden_out, gate = (120, -14), (160, -58), (172, -136)
arc_pts = arc(garden_in, garden_out)
lg = poly(arc_pts)
causeway = L(garden_out, gate)
print(f'\n== 花园段 ==  北口→绕喷泉东侧→东南出口: {lg:.1f} m（直线 {L(garden_in,garden_out):.1f}），堤道 {causeway:.1f} m')

O = (172, -136); a20 = math.radians(20)
uu = (math.sin(a20), -math.cos(a20)); vv = (math.cos(a20), math.sin(a20))
def W(u, v): return (O[0] + u*uu[0] + v*vv[0], O[1] + u*uu[1] + v*vv[1])

EXIT = W(90, 19)
print(f'  撤离点局部 (90,+19) → 世界 ({EXIT[0]:.1f},{EXIT[1]:.1f})；距东墙 6 m、距南端 6 m')
print(f'  坞四角: {tuple(round(x,1) for x in W(0,-25))} {tuple(round(x,1) for x in W(0,25))} {tuple(round(x,1) for x in W(96,25))} {tuple(round(x,1) for x in W(96,-25))}')

dock_uv = [(0,0), (6,-18), (66,-18), (74,-16), (74,19), (90,19)]
dock_pts = [W(*p) for p in dock_uv]
print('  坞内分段: ' + ' + '.join(f'{L(dock_pts[i],dock_pts[i+1]):.1f}' for i in range(len(dock_pts)-1)) + f' = {poly(dock_pts):.1f} m')

segs = [
    ('离心中心→南门', [(90,30),(90,0)]),
    ('南门→南环东行30→南下14', [(90,0),(120,0),(120,-14)]),
    ('花园北口→绕喷泉→东南出口', arc_pts),
    ('跨水堤道', [garden_out, gate]),
    ('坞内（门→坡道→横穿→沿东墙）', dock_pts),
]
acc = 0
print('\n== 撤离分段 ==')
for n, p in segs:
    d = poly(p); acc += d
    print(f'  {n}: {d:.1f} m  (累计 {acc:.1f})')
print(f'  合计 {acc:.1f} m，按 6 m/s ≈ {acc/6:.0f} s')

for label, head in [('离心中心', [(90,30)]), ('黑室中心', [(150,30)]),
                    ('南墙中点', [(120,0)]), ('离心南门', [(90,0)])]:
    pts = head + [(120,0), (120,-14)] + arc_pts + [gate] + dock_pts[1:]
    # 去重连续重复点
    clean = [pts[0]]
    for p in pts[1:]:
        if L(clean[-1], p) > 1e-6: clean.append(p)
    print(f'  {label} → 撤离: {poly(clean):.1f} m')

# ---------- 3. 总裁 ----------
v1, v2 = (112, 68), (130, 52)
print('\n== 浮力→黑室 ==')
print(f'  地面: {dist("H2","H4"):.1f} m')
vault = L((90,90), v1) + 12 + L(v1, v2) + 12 + L(v2, (150,30))
print(f'  穿总裁: {vault:.1f} m = {L((90,90),v1):.1f} + 12 + {L(v1,v2):.1f} + 12 + {L(v2,(150,30)):.1f}')
print(f'  省: {dist("H2","H4")-vault:.1f} m')
