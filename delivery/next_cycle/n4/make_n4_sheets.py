from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path('C:/软件/鼠鼠'); N4=ROOT/'delivery/next_cycle/n4'; T3=N4/'T3'; T4=N4/'T4'; T6=N4/'T6'
FONT='C:/Windows/Fonts/NotoSansSC-VF.ttf'
def f(s):
    try: return ImageFont.truetype(FONT,s)
    except: return ImageFont.load_default()
def label(d,xy,s,size=20):
    d.text(xy,s,font=f(size),fill=(38,41,42))
def grid(images, cell, cols, out, title, labels=None):
    w,h=cell; rows=(len(images)+cols-1)//cols
    sheet=Image.new('RGB',(cols*w+40, rows*(h+40)+70),(246,242,233)); d=ImageDraw.Draw(sheet)
    label(d,(20,18),title,26)
    for i,im in enumerate(images):
        c,r=i%cols,i//cols; x=20+c*w; y=60+r*(h+40)
        im=im.convert('RGB'); sc=min(w/im.width,h/im.height); im=im.resize((int(im.width*sc),int(im.height*sc)),Image.LANCZOS)
        sheet.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))
        d.rectangle([x,y,x+w,y+h],outline=(170,164,150),width=2)
        if labels and i<len(labels): label(d,(x,y+h+6),labels[i],16)
    sheet.save(out); print(out)
# N02 material 2x2
mat=[Image.open(T3/f'mat_finalN4_{i}.png') for i in ['ENV001','ENV006','PROP001','PROP004']]
grid(mat,(620,400),2,T4/'N02_material_closeups.png','N02 material closeups · candidate_n4',['ENV001 stone paving','ENV006 autumn tree','PROP001 bench','PROP004 lamp'])
# N02 shadow / contact comparison against the rejected n2 candidate
n2_full=Image.open(ROOT/'delivery/next_cycle/T3/game_finalN2_formal_no_ui.png')
n4_full=Image.open(T3/'game_finalN4_formal_no_ui.png')
shadow_pairs=[
    ('tree + planter contact', n2_full, n4_full, (180, 10, 760, 470)),
    ('bench / lamp contact', n2_full, n4_full, (820, 360, 1280, 650)),
    ('foreground path edge', n2_full, n4_full, (0, 430, 620, 720)),
]
cw,ch=420,250
sheet=Image.new('RGB',(2*cw+90, 3*(ch+62)+54),(246,242,233)); d=ImageDraw.Draw(sheet)
label(d,(20,18),'N02 shadow/contact: n2 vs n4',26)
for i,(title,a,b,box) in enumerate(shadow_pairs):
    y=74+i*(ch+62)
    for j,img in enumerate((a,b)):
        im=img.crop(box).convert('RGB')
        sc=min(cw/im.width,ch/im.height); im=im.resize((int(im.width*sc),int(im.height*sc)),Image.LANCZOS)
        x=20+j*(cw+30)
        sheet.paste(im,(x+(cw-im.width)//2,y+(ch-im.height)//2))
        d.rectangle([x,y,x+cw,y+ch],outline=(170,164,150),width=2)
        label(d,(x,y+ch+6),f'{title} · {"n2" if j==0 else "n4"}',15)
sheet.save(T4/'N02_shadow_before_after.png'); print(T4/'N02_shadow_before_after.png')
# N04 sheet
vis=Image.open(T4/'N04_actor_visible.png'); hid=Image.open(T4/'N04_actor_hidden.png')
grid([vis,hid],(620,350),2,T4/'N04_actor_bbox.png','N04 real bbox: visible vs hidden PlayerWorldQuad · 130×130 px',['visible','hidden'])
# N05 sheet
imgs=[Image.open(T4/x) for x in ['N05_fresh_portrait.png','N05_resize_portrait.png','N05_restored_landscape.png']]
grid(imgs,(400,340),3,T4/'N05_orientation.png','N05 orientation: fresh portrait / resize / restore',['fresh portrait','resize portrait','restored landscape'])
# N07 sheet
idle=[Image.open(T6/'character_n'/f'idle_{i:02d}.png') for i in range(6)]
move=[Image.open(T6/'character_n'/f'move_{i:02d}.png') for i in range(6)]
grid(idle+move,(300,220),6,T6/'character_n/N07_animation_sheet.png','N07 idle (top) / move (bottom): 6 unique frames each',[f'idle {i}' for i in range(6)]+[f'move {i}' for i in range(6)])
