# -*- coding: utf-8 -*-
"""细节板：石地/台阶/树/草池/设备 的原尺寸局部拼成一张。"""
import os
from PIL import Image, ImageDraw, ImageFont
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src=Image.open(os.path.join(ROOT,"renders","final.png")).convert("RGB")
W,H=src.size
crops=[("石地与接缝",(560,520,1160,820)),("台阶与栏杆",(120,700,720,1000)),
       ("左树",(80,60,480,360)),("右侧草池",(1180,240,1720,540)),("中央设备",(640,180,1140,480))]
tiles=[]
for name,box in crops:
    c=src.crop(box); tiles.append((name,c))
tw,th=tiles[0][1].size
scale=0.55
tw2,th2=int(tw*scale),int(th*scale)
cols=3; rows=2
board=Image.new("RGB",(cols*tw2+40,rows*(th2+30)+20),(22,22,24))
d=ImageDraw.Draw(board); f=ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",16)
for i,(name,c) in enumerate(tiles):
    x=(i%cols)*(tw2+10)+10; y=(i//cols)*(th2+30)+28
    board.paste(c.resize((tw2,th2),Image.LANCZOS),(x,y))
    d.text((x,y-20),name,font=f,fill=(255,255,255))
board.save(os.path.join(ROOT,"renders","details.png"))
print("DETAILS DONE", board.size)
