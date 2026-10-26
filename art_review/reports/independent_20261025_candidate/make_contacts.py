from pathlib import Path
import json,math,hashlib
from PIL import Image,ImageDraw,ImageFont
root=Path(r'C:/软件/鼠鼠');out=root/'art_review/reports/independent_20261025_candidate'
index=json.loads((root/'delivery/next_cycle/T6/state_index.json').read_text(encoding='utf-8-sig'))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
for kind,rows in [('ui',index['ui_states']),('assets',index['assets'])]:
 for start in range(0,len(rows),12):
  page=rows[start:start+12];canvas=Image.new('RGB',(1600,math.ceil(len(page)/4)*258),(28,28,28));draw=ImageDraw.Draw(canvas)
  for i,row in enumerate(page):
   im=Image.open(root/row['path']).convert('RGB');im.thumbnail((396,224));x=(i%4)*400;y=(i//4)*258
   canvas.paste(im,(x,y+29));draw.text((x+5,y+5),row['id'],font=font,fill=(255,255,255))
  canvas.save(out/f'{kind}_contact_{start//12+1}.jpg',quality=90)
anims=[]
manifest=json.loads((root/'art_review/submissions/candidate_full/manifest.json').read_text(encoding='utf-8-sig'))
paths={a['path'] for a in manifest['artifacts'] if Path(a['path']).suffix.lower()=='.gif'}
for rel in paths:
 im=Image.open(root/rel);hashes=[];sizes=[]
 for i in range(getattr(im,'n_frames',1)):
  im.seek(i);frame=im.convert('RGBA');hashes.append(hashlib.sha256(frame.tobytes()).hexdigest());sizes.append(frame.size)
 anims.append({'path':rel,'frames':len(hashes),'unique_frames':len(set(hashes)),'size':sizes[0]})
(out/'manifest_animation_details.json').write_text(json.dumps(anims,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'ui':len(index['ui_states']),'assets':len(index['assets']),'animations':anims},ensure_ascii=False))