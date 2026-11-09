# -*- coding: utf-8 -*-
"""v3.9 最终效果预览图：按 §8.1 配色与明度分层，模拟游戏内俯视地图。
北朝上，y 向北为正。输出 planning/art/_final_preview.png
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

S = 6.0                      # px / m（预览图；正式纹理 7 px/m）
PAD_L, PAD_R, PAD_T, PAD_B = 110, 110, 300, 130
WW, WH = 240, 420            # 世界尺寸
W = int(PAD_L + WW * S + PAD_R)
H = int(PAD_T + WH * S + PAD_B)

# ---------- 颜色（§8.1）----------
WATER    = (34, 56, 60)      # 12-18% 深青
WATERLN  = (52, 82, 86)
LAND     = (150, 148, 137)   # 平台 / 路 45-55%
PLATFORM = (168, 166, 152)
GARDEN   = (201, 196, 184)   # 花园暖灰
DOCKC    = (169, 176, 178)   # 坞底冷灰
ROAD     = (110, 116, 118)   # 环路中性灰（比 §8.1 略亮，预览可读）
SEAWALL  = (96, 104, 100)
WAVELN   = (196, 206, 198)
INK      = (238, 236, 226)
MUTED    = (176, 186, 184)
DARKTX   = (44, 46, 42)
YELLOW   = (242, 194, 48)
BLUE     = (46, 111, 168)
HGREEN   = (62, 155, 99)
ACCENT   = (232, 146, 74)
STEEL    = (122, 138, 140)
CONT     = (78, 96, 92)
TAN      = (206, 192, 166)

FP = 'C:/Windows/Fonts/msyh.ttc'
FB = 'C:/Windows/Fonts/msyhbd.ttc'
def f(sz, bold=False):
    return ImageFont.truetype(FB if bold else FP, sz)

def X(x): return PAD_L + x * S
def Y(y): return PAD_T + (166 - y) * S
def P(x, y): return (X(x), Y(y))

img = Image.new('RGB', (W, H), WATER)
dr = ImageDraw.Draw(img)
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(ov)

def poly(d, pts, fill, outline=None, width=1):
    d.polygon([P(*p) for p in pts], fill=fill, outline=outline, width=width)

def rect(d, x0, y0, x1, y1, fill, outline=None, width=1):
    a, b = P(x0, y0), P(x1, y1)
    d.rectangle([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])],
                fill=fill, outline=outline, width=width)

def line(d, pts, fill, width=1):
    d.line([P(*p) for p in pts], fill=fill, width=width)

def circle(d, cx, cy, r_m, fill=None, outline=None, width=1):
    c = P(cx, cy); r = r_m * S
    d.ellipse([c[0]-r, c[1]-r, c[0]+r, c[1]+r], fill=fill, outline=outline, width=width)

def text(d, x, y, t, sz, col, bold=False, anchor='la'):
    d.text(P(x, y), t, font=f(sz, bold), fill=col, anchor=anchor)

def shadow(pts, dx=3, dy=5, alpha=80):
    od.polygon([(X(x)+dx, Y(y)+dy) for x, y in pts], fill=(0, 0, 0, alpha))

def shadow_rect(x0, y0, x1, y1, dx=3, dy=5, alpha=80):
    shadow([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dx, dy, alpha)

def dashes(d, pts, col, width=2, dash_m=4, gap_m=4):
    pp = [P(*p) for p in pts]
    total = 0
    segs = []
    for i in range(len(pp)-1):
        x0, y0 = pp[i]; x1, y1 = pp[i+1]
        L = math.hypot(x1-x0, y1-y0)
        segs.append((x0, y0, x1, y1, L))
        total += L
    step = (dash_m + gap_m) * S
    t = 0.0; on = True
    for x0, y0, x1, y1, L in segs:
        if L < 1e-6: continue
        ux, uy = (x1-x0)/L, (y1-y0)/L
        s = 0.0
        while s < L:
            e = min(s + step, L)
            if on:
                d.line([(x0+ux*s, y0+uy*s), (x0+ux*e, y0+uy*e)], fill=col, width=width)
            s = e; on = not on

# ================= 1. 水面 =================
for i in range(-4, 30):
    x0 = -60 + i * 26
    dr.line([(X(x0), Y(170)), (X(x0+120), Y(-262))], fill=(40, 62, 66), width=1)

# 远景山脊（画在留白里，先画，之后被陆地盖住）
ridge = [(0, 176), (40, 156), (80, 168), (130, 150), (180, 164), (240, 154), (240, 196), (0, 196)]
dr.polygon([(X(x), Y(y)) for x, y in ridge], fill=(56, 68, 72))
ridge2 = [(0, 164), (60, 150), (120, 160), (200, 144), (240, 154), (240, 180), (0, 180)]
dr.polygon([(X(x), Y(y)) for x, y in ridge2], fill=(70, 84, 86))
for gx in range(-40, 300, 44):
    gy = 210 + (gx % 3) * 26
    dr.line([(X(gx), Y(gy)), (X(gx+60), Y(gy-90))], fill=(46, 70, 74), width=1)

# ================= 2. 陆地平台 =================
OCT = [(72,-14),(168,-14),(194,8),(194,112),(168,134),(72,134),(46,112),(46,8)]
# 核心平台
poly(dr, OCT, PLATFORM, SEAWALL, 5)
poly(dr, [(p[0], p[1]) for p in OCT], None, WAVELN, 1)
# 观景平台（四个切角外挑）
for (ax, ay), (bx, by) in [((72,-14),(46,8)), ((168,-14),(194,8)),
                            ((194,112),(168,134)), ((72,134),(46,112))]:
    mx, my = (ax+bx)/2, (ay+by)/2
    nx, ny = mx*1.0, my*1.0
    vx, vy = bx-ax, by-ay
    L = math.hypot(vx, vy)
    ox, oy = -vy/L, vx/L
    if (mx-120)*ox + (my-60)*oy < 0: ox, oy = -ox, -oy
    cx, cy = mx + ox*3, my + oy*3
    hw, hl = 13, 3.5
    ux, uy = vx/L, vy/L
    quad = [(cx-ux*hw-ox*hl, cy-uy*hw-oy*hl), (cx+ux*hw-ox*hl, cy+uy*hw-oy*hl),
            (cx+ux*hw+ox*hl, cy+uy*hw+oy*hl), (cx-ux*hw+ox*hl, cy-uy*hw+oy*hl)]
    poly(dr, quad, PLATFORM, SEAWALL, 2)

# 南花园半岛
poly(dr, [(70,-64),(170,-64),(170,-14),(70,-14)], GARDEN, SEAWALL, 5)
# 跨水堤道
C0, C1 = (160,-58), (172,-136)
dx, dy = C1[0]-C0[0], C1[1]-C0[1]
L = math.hypot(dx, dy); ux, uy = dx/L, dy/L; px, py = -uy, ux
hw = 9
cw = [(C0[0]+px*hw, C0[1]+py*hw), (C1[0]+px*hw, C1[1]+py*hw),
      (C1[0]-px*hw, C1[1]-py*hw), (C0[0]-px*hw, C0[1]-py*hw)]
poly(dr, cw, (124,130,130), SEAWALL, 3)
# 管廊（堤道西侧一条）
poly(dr, [(C0[0]-px*(hw-3), C0[1]-py*(hw-3)), (C1[0]-px*(hw-3), C1[1]-py*(hw-3)),
          (C1[0]-px*(hw-0.6), C1[1]-py*(hw-0.6)), (C0[0]-px*(hw-0.6), C0[1]-py*(hw-0.6))],
     (92, 98, 96))

# 干船坞（东南 20°）
O = (172, -136); ang = math.radians(20)
uu = (math.sin(ang), -math.cos(ang)); vv = (math.cos(ang), math.sin(ang))
def R(u, v): return (O[0] + u*uu[0] + v*vv[0], O[1] + u*uu[1] + v*vv[1])
dock = [R(0,-25), R(0,25), R(96,25), R(96,-25)]
poly(dr, dock, DOCKC, (232, 228, 214), 6)          # 坞墙顶
poly(dr, [R(2.5,-22.5), R(2.5,22.5), R(93.5,22.5), R(93.5,-22.5)],
     (158, 165, 166), (110, 116, 116), 1)          # 坞底
# 坡道（西墙）
poly(dr, [R(6,-22), R(66,-22), R(66,-17), R(6,-17)], (196, 192, 178), (140, 136, 122), 1)
for i in range(9):
    u0 = 8 + i*6.5
    line(dr, [R(u0,-22), R(u0,-17)], (150, 146, 134), 1)
# 格栅
for gu in (76, 88):
    poly(dr, [R(gu,-12), R(gu+1.2,-12), R(gu+1.2,12), R(gu,12)], (96, 102, 102))

# 西区门岛 + 断头院 + 桥
poly(dr, [(16,36),(46,36),(46,84),(16,84)], LAND, SEAWALL, 4)
poly(dr, [(32,52),(46,52),(46,68),(32,68)], ROAD, SEAWALL, 2)
# 西侧电梯塔小岛
poly(dr, [(2,100),(20,100),(20,128),(2,128)], LAND, SEAWALL, 3)

# ================= 3. 投影层 =================
shadow_rect(68,112,78,117, dx=3, dy=5, alpha=80)             # 办公舱
for cu in (40,50,60,70,78):
    c = R(cu,16)
    od.polygon([(X(c[0]-3)+3, Y(c[1]+1.2)+5), (X(c[0]+3)+3, Y(c[1]+1.2)+5),
                (X(c[0]+3)+3, Y(c[1]-1.2)+5), (X(c[0]-3)+3, Y(c[1]-1.2)+5)],
               fill=(0,0,0,70))
od.polygon([(X(p[0])+7, Y(p[1])+26) for p in [(100,45),(140,45),(140,75),(100,75)]],
           fill=(0,0,0,60))                                   # 总裁盒悬投影
eq = [R(18,10), R(34,10), R(34,24), R(18,24)]
od.polygon([(X(q[0])+3, Y(q[1])+5) for q in eq], fill=(0,0,0,70))  # ENTRANCE 蓝盒
img = Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')
dr = ImageDraw.Draw(img)

# ================= 4. 环路 + 标线 =================
RING = [(79,-7),(165,-7),(187,15),(187,105),(165,127),(79,127),(53,105),(53,15),(79,-7)]
line(dr, RING, ROAD, 14*S if False else int(14*S))
line(dr, RING, (96,102,102), 1)
dashes(dr, RING, (210,190,90), 1, 4, 5)
# 斑马线（每个门口）
for gx, gy, horiz in [(90,0,True),(150,0,True),(90,120,True),(150,120,True)]:
    if horiz:
        for i in range(4):
            rect(dr, gx-6+i*3.4, gy-1.2, gx-6+i*3.4+1.6, gy+1.2, (210,206,190))

# ================= 5. 四栋楼 =================
ROOMS = {
    'H1': ((60,0),(120,60),  TAN,        'H1 离心'),
    'H2': ((60,60),(120,120),(172,178,172),'H2 浮力'),
    'H3': ((120,60),(180,120),(160,168,176),'H3 蓝室'),
    'H4': ((120,0),(180,60), (150,158,148),'H4 黑室'),
}
for k, ((x0,y0),(x1,y1), col, name) in ROOMS.items():
    rect(dr, x0, y0, x1, y1, col)
for k, ((x0,y0),(x1,y1), col, name) in ROOMS.items():
    rect(dr, x0, y0, x1, y1, None, (64,66,60), 3)

# 六个门开口：两侧房间地板色盖住墙线
GATES = [((90,60),'H1','H2'), ((150,60),'H4','H3'),
         ((90,0),'H1',None), ((150,0),'H4',None),
         ((90,120),'H2',None), ((150,120),'H3',None)]
ROOM_COL = {k: v[2] for k, v in ROOMS.items()}
for (gx, gy), a, b in GATES:
    if gy in (0, 120):
        rect(dr, gx-1.6, gy-1.6, gx+1.6, gy+1.6, ROOM_COL[a])
        rect(dr, gx-1.6, gy+(-2.6 if gy==120 else 1.6) if gy==120 else gx, gx, gy, PLATFORM) if False else None
        rect(dr, gx-1.6, gy-2.8 if gy==120 else gy-1.6, gx+1.6, gy+1.6 if gy==120 else gy+2.8,
             PLATFORM if gy in (0,120) else ROOM_COL[a])
    else:
        half = 1.6
        rect(dr, gx-half, gy-half, gx+half, gy+half, ROOM_COL[a])
        rect(dr, gx-half, gy-half, gx+half, gy+half, ROOM_COL[b] if b else ROOM_COL[a])
        rect(dr, gx-half, gy-half, gx+half, gy+half, (150,150,142))
for gx, gy in [(90,60),(150,60),(90,0),(150,0),(90,120),(150,120)]:
    rect(dr, gx-1.6, gy-1.6, gx+1.6, gy+1.6, (198,196,180))

# --- H1 离心 ---
circle(dr, 90, 30, 22, None, (96,104,110), 5)         # Ø44 圆墙
circle(dr, 90, 30, 22, None, (214,150,60), 1)         # 橙黑警示带(示意)
rect(dr, 86, 6.5, 94, 9.5, TAN)                        # 南门洞
rect(dr, 86, 50.5, 94, 53.5, TAN)                      # 北门洞
circle(dr, 98, 27, 9, None, YELLOW, 1)                 # Ø18 转盘
c = R(0,0) if False else None
podc = (99, 28)
a15 = math.radians(-15)
pc = [ (podc[0]+9*math.cos(a15)-2*math.sin(a15), podc[1]+9*math.sin(a15)+2*math.cos(a15)),
       (podc[0]+9*math.cos(a15)+2*math.sin(a15), podc[1]+9*math.sin(a15)-2*math.cos(a15)),
       (podc[0]-9*math.cos(a15)+2*math.sin(a15), podc[1]-9*math.sin(a15)-2*math.cos(a15)),
       (podc[0]-9*math.cos(a15)-2*math.sin(a15), podc[1]-9*math.sin(a15)+2*math.cos(a15))]
poly(dr, pc, (96,100,104), (52,56,58), 1)
circle(dr, 90, 30, 1, (70,74,78))
rect(dr, 71, 54.5, 81, 58, (140,146,150), (80,86,90), 1)   # 控制室
for yy in (12, 20, 28):
    rect(dr, 60.6, yy, 62.4, yy+2.4, (120,126,130))         # 西墙柜
rect(dr, 118.2, 14, 119.4, 17.4, (120,126,130))
rect(dr, 65.2, 3, 68.2, 5.8, (120,126,130))                 # 料箱
# --- H2 浮力 ---
rect(dr, 68, 79, 104, 101, (44, 84, 96), (198,206,198), 2)  # 深池
line(dr, [(64,102),(108,102)], (70,74,72), 2)               # 龙门吊梁
for lx in (64, 108):
    line(dr, [(lx,102),(lx,110)], (70,74,72), 2)
def caps(cx, cy, adeg, col=STEEL):
    a = math.radians(adeg); hl, hw2 = 7, 2
    ux, uy = math.cos(a), math.sin(a)
    pts = [(cx-ux*hl-hw2*uy, cy-uy*hl+hw2*ux), (cx+ux*hl-hw2*uy, cy+uy*hl+hw2*ux),
           (cx+ux*hl+hw2*uy, cy+uy*hl-hw2*ux), (cx-ux*hl+hw2*uy, cy-uy*hl-hw2*ux)]
    poly(dr, pts, col, (58,66,68), 1)
caps(76, 88, 20); caps(104, 108, 0); caps(96, 95, -10)
rect(dr, 63, 109.5, 73, 114.5, (150,154,150), (96,100,96), 1)  # 办公舱
for xx in (76, 80, 100):
    rect(dr, xx, 118.2, xx+1.6, 119.4, (120,126,130))
# --- H3 蓝室 ---
rect(dr, 136, 79, 160, 101, (96, 108, 118), (70,80,88), 2)  # 下沉坑
rect(dr, 137.5, 80.5, 158.5, 99.5, (86, 98, 108))
circle(dr, 148, 90, 1.5, (216,178,80))                      # 卫星
rect(dr, 141.5, 89.4, 145, 90.6, (196,168,86))
rect(dr, 151, 89.4, 154.5, 90.6, (196,168,86))
circle(dr, 141, 90, 0.8, (90,96,100)); circle(dr, 155, 90, 0.8, (90,96,100))
poly(dr, [(161,92),(167,92),(167,86),(161,86)], (176,182,178), (110,116,112), 1)  # 坡道
for xx in range(122, 179, 6):                                # 肋板墙
    rect(dr, xx, 118.6, xx+2.2, 119.4, (108,116,122))
for yy in range(62, 119, 6):
    rect(dr, 120.6, yy, 121.4, yy+2.2, (108,116,122))
    rect(dr, 178.6, yy, 179.4, yy+2.2, (108,116,122))
# --- H4 黑室 ---
rect(dr, 120.6, 57.4, 179.4, 59.4, HGREEN)                  # 绿墙北
rect(dr, 177.6, 0.6, 179.4, 59.4, HGREEN)                   # 绿墙东
rect(dr, 145, 48, 155, 60, (70, 108, 140), (40,70,96), 1)   # 筒拱
line(dr, [(146,49),(154,49)], (198,214,224), 2)
circle(dr, 177, 28, 4.5, (58, 66, 70), (150,156,150), 2)      # Ø10 舱门
circle(dr, 177, 28, 1.2, (150,156,150))
for (ax,ay,bx,by) in [(126,10,138,10.8),(140,22,156,22.8),(132,32,144,32.8)]:
    rect(dr, ax, ay, bx, by, (96,102,96))                   # 三道矮墙
line(dr, [(124,44),(176,44)], (70,74,72), 2)                # 行车
poly(dr, [(160,42.5),(168,42.5),(168,45.5),(160,45.5)], (96,100,104), (52,56,58), 1)
rect(dr, 146, 36, 154, 40, (120,126,124), (80,86,84), 1)    # 装配台
for yy in (12, 20, 28, 36, 44):
    rect(dr, 122.2, yy, 123.8, yy+1.6, (110,104,84))        # 军用箱

# ================= 6. 屋顶导轨 + 总裁盒 =================
line(dr, [(120,120),(120,0)], (206,210,202), 2)
for ty in range(4, 118, 8):
    line(dr, [(119,ty),(121,ty)], (206,210,202), 1)
rect(dr, 100, 45, 140, 75, (236, 224, 196), ACCENT, 3)
rect(dr, 101.2, 46.2, 138.8, 73.8, None, (196,180,140), 1)
line(dr, [(120,53),(120,67)], (96,92,80), 2)                # 屏风
rect(dr, 118.6, 72.2, 121.4, 73.8, (70,66,60))              # 保险柜
circle(dr, 130, 62, 1.5, (208,168,74), (150,118,40), 1)
rect(dr, 105, 72, 110, 74, (150,120,90))
rect(dr, 106, 49, 110, 51, (140,130,116))
rect(dr, 109, 67, 111, 69, None, ACCENT, 1)                 # 舱口 V1
rect(dr, 129, 51, 131, 53, None, ACCENT, 1)                 # 舱口 V2
text(dr, 111, 58, '总裁', 15, (110,86,44), True, 'mm')
text(dr, 111, 52, '悬空 12 m', 9, (130,108,64), False, 'mm')

# ================= 7. 花园 =================
circle(dr, 120, -39, 11, (214,210,196), (120,124,116), 2)
circle(dr, 120, -39, 5, (52, 92, 98), (150,180,180), 1)
text(dr, 120, -39, '◎ 喷泉', 10, (60,88,88), False, 'mm')
for (px_, py_) in [(98,-30),(142,-30)]:
    poly(dr, [(px_,py_+2),(px_+4,py_-3),(px_-3,py_-4)], ACCENT, (150,86,30), 1)
for (px_, py_) in [(78,-18),(163,-18),(78,-60),(120,-62),(163,-60)]:
    circle(dr, px_, py_, 1.2, (86,118,78))
    line(dr, [(px_,py_),(px_,py_+2)], (120,100,70), 1)
rect(dr, 75, -57.5, 85, -54.5, (92,140,180), (60,96,130), 1)   # 摆渡车
for (tx,ty) in [(150,-19),(166,-39)]:
    poly(dr, [(tx-3,ty+3),(tx+3,ty+3),(tx,ty-3)], (226,196,84), (160,134,50), 1)
text(dr, 88, -20, '南侧花园半岛 100×50', 12, (98,94,78), True, 'lm')
text(dr, 155, -42, '花园 70 m', 10, (150,70,20), True, 'lm')

# ================= 8. 坞内物件 =================
for cu in (40,50,60,70,78):
    c = R(cu, 16)
    pts = [(c[0]-3*uu[0]-1.2*vv[0], c[1]-3*uu[1]-1.2*vv[1]),
           (c[0]+3*uu[0]-1.2*vv[0], c[1]+3*uu[1]-1.2*vv[1]),
           (c[0]+3*uu[0]+1.2*vv[0], c[1]+3*uu[1]+1.2*vv[1]),
           (c[0]-3*uu[0]+1.2*vv[0], c[1]-3*uu[1]+1.2*vv[1])]
    poly(dr, pts, CONT, (40,52,50), 1)
for pu in (72, 79, 86):
    c = R(pu, -23)
    rect(dr, c[0]-1, c[1]-1, c[0]+1, c[1]+1, (176,160,124), (120,108,80), 1)
for i in range(6):
    c = R(18 + (i % 3)*1.6, -24.2 - (i//3)*1.4)
    circle(dr, c[0], c[1], 0.35, (150,96,60), (100,64,40), 1)
pc = [R(34,2.5), R(46,2.5), R(46,5.5), R(34,5.5)]
poly(dr, pc, (150,154,150), (100,104,100), 1)               # Ø3 管段
poly(dr, [R(18,10), R(34,10), R(34,24), R(18,24)], BLUE, (26,70,110), 2)
gd = [R(24.4,10), R(27.6,10), R(27.6,12.4), R(24.4,12.4)]
poly(dr, gd, (96,180,120))                                   # 绿门洞
et = R(26,20)
dr.text((X(et[0]), Y(et[1])), 'ENTRANCE', font=f(8, True), fill=(238,236,226), anchor='mm')
# 蓝腰带 + 撤离黄框
line(dr, [R(80,24.6), R(96,24.6)], BLUE, 3)
rect(dr, 218.6, -216.1, 222.6, -212.1, (240,206,90), (150,110,20), 2)
text(dr, 214, -210, '撤离点', 10, (240,206,90), True, 'rm')
text(dr, 186, -184, '水平试车间', 15, (60,62,58), True, 'mm')
text(dr, 186, -190, '坞底 ±0 · 墙顶 +9', 9, (76,80,78), False, 'mm')

# ================= 9. 外围设施 =================
rect(dr, 4, 36, 16, 84, (128,126,116), SEAWALL, 2)
text(dr, 10, 60, '断\n头\n院', 9, (110,108,96), True, 'mm')
rect(dr, 22, 72, 26, 76, (150,150,140), (96,98,92), 1)
text(dr, 24, 90, '西区大门（封死）', 10, (232,226,210), True, 'ma')
line(dr, [(11,114),(11,114-26)], (214,218,214), 3)
line(dr, [(4,114-24),(18,114-24)], (214,218,214), 4)
text(dr, 24, 106, '电梯塔（远景）', 9, (200,206,200), True, 'lm')

# ================= 10. 撤离路线 =================
dock_uv = [(0,0),(6,-18),(66,-18),(74,-16),(74,19),(90,19)]
dock_xy = [R(u,v) for u,v in dock_uv]
route = [(90,30),(90,0),(120,0),(120,-14),(120,-27),(131,-31),(133,-39),
         (131,-47),(145,-54),(160,-58),(172,-136)] + dock_xy[1:]
pts = [P(*p) for p in route]
dr.line(pts, fill=ACCENT, width=4, joint='curve')
for p in pts:
    dr.ellipse([p[0]-3, p[1]-3, p[0]+3, p[1]+3], fill=ACCENT)
for lbl, lx, ly, anc in [('30 m', 87, 16, 'rm'), ('44 m', 104, -3, 'lm'),
                          ('79 m', 181, -104, 'lm'), ('138 m', 175, -150, 'lm')]:
    text(dr, lx, ly, lbl, 10, (240,170,90), True, anc)

# ================= 11. 图面标注 =================
for (x0,y0,x1,y1), name in zip([(60,0,120,60),(60,60,120,120),(120,60,180,120),(120,0,180,60)],
                               ['H1 离心','H2 浮力','H3 蓝室','H4 黑室']):
    text(dr, (x0+x1)/2, (y0+y1)/2+14, name, 17, DARKTX, True, 'mm')
text(dr, 128, 111, '屋顶导轨（不可通行）', 8, (216,218,208), True, 'lm')
text(dr, 63, 88, '深池 36×22', 8, (238,236,226), False, 'lm')
text(dr, 133, 76.5, '下沉坑 24×22', 8, (58,66,74), False, 'lm')
text(dr, 62, 1.2, 'Ø44 圆墙 · 吊舱 · 转盘', 8, (110,96,70), False, 'lm')
text(dr, 152, 6, 'HAAVK 绿墙 · 筒拱', 8, (46,84,60), False, 'lm')
text(dr, 152, -60, '跨水堤道 18 m', 10, (208,212,206), True, 'la')
text(dr, 88, -110, '南 湾（水）', 13, (120,170,172), True, 'mm')

# ================= 12. 标题 / 图例 / 比例尺 =================
dr.text((PAD_L, 34), '航天基地 · 最终效果预览', font=f(40, True), fill=INK)
dr.text((PAD_L, 92), 'v3.10 ｜ 北朝上 ｜ 四面环水 · 核心切角岛 · 花园半岛 · 跨水堤道 · 东南干船坞 ｜ 撤离 361 m ≈ 60 s',
        font=f(16), fill=MUTED)
lx, ly = PAD_L, 140
items = [('陆地/平台', PLATFORM), ('花园', GARDEN), ('坞底', DOCKC), ('环路', ROAD),
         ('水', WATER), ('撤离路线', ACCENT)]
for i, (label, col) in enumerate(items):
    xx = lx + i * 176
    dr.rectangle([xx, ly, xx+18, ly+18], fill=col, outline=MUTED)
    dr.text((xx+24, ly+1), label, font=f(13), fill=MUTED)
# 指北针
nx, ny = W - 90, 88
dr.ellipse([nx-26, ny-20, nx+26, ny+34], fill=(16,28,32), outline=(70,96,98))
dr.polygon([(nx, ny-14), (nx-9, ny+16), (nx, ny+9), (nx+9, ny+16)], fill=INK)
dr.text((nx-5, ny+18), 'N', font=f(13, True), fill=INK)
# 比例尺
bx, by = PAD_L, H - 60
dr.line([(bx, by), (bx + 100*S, by)], fill=INK, width=4)
for xx in (bx, bx+50*S, bx+100*S):
    dr.line([(xx, by-7), (xx, by+7)], fill=INK, width=4)
dr.text((bx, by+10), '0', font=f(13), fill=INK)
dr.text((bx+50*S-12, by+10), '50', font=f(13), fill=INK)
dr.text((bx+100*S-24, by+10), '100 m', font=f(13), fill=INK)
# 底部数据条
stats = '6 门（每栋 2）｜ 室内 159 件 · 摆件 26 ｜ 全图 255 件 ≈ 54k 面 ｜ 对角借道 194 m · 纯绕 310 m'
dr.text((PAD_L + 260, by+10), stats, font=f(13), fill=MUTED)

os.makedirs('planning/art', exist_ok=True)
out = 'planning/art/_final_preview.png'
img.save(out)
print('saved', out, img.size)
