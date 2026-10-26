const sharp=require('C:/软件/鼠鼠/.tooling/node_modules/sharp');
const T2='C:/软件/鼠鼠/delivery/next_cycle/T2';
async function label(buf,text){
  const svg=Buffer.from(`<svg width="1280" height="42"><rect width="1280" height="42" fill="rgba(20,20,20,0.75)"/><text x="14" y="30" font-family="Arial" font-size="24" fill="#fff">${text}</text></svg>`);
  return sharp(buf).composite([{input:svg,top:0,left:0}]).png().toBuffer();
}
(async()=>{
  const rows=[
    ['paving','stone paving: flat gray -> warm-gray tile pattern (tex_stone_tiles)'],
    ['bench','bench: flat color -> wood grain along slats (tex_wood_grain, box-UV)'],
    ['fence','fence/lamp: matte black -> dark metal with specular (tex_metal_brushed, metallic 0.8)'],
  ];
  const cells=[];
  for(const [name,text] of rows){
    const b=await label(`${T2}/mat_before_${name}.png`,'BEFORE '+text);
    const a=await label(`${T2}/mat_after_${name}.png`,'AFTER '+text);
    cells.push([await sharp(b).resize(1264,711,{fit:'fill'}).png().toBuffer(),
                await sharp(a).resize(1264,711,{fit:'fill'}).png().toBuffer()]);
  }
  const H=719,W=2560;
  const comp=sharp({create:{width:W,height:H*3+8,channels:3,background:{r:10,g:10,b:10}}});
  const items=[];
  cells.forEach((pair,i)=>{
    items.push({input:pair[0],top:4+i*H,left:4});
    items.push({input:pair[1],top:4+i*H,left:1276});
  });
  await comp.composite(items).png().toFile(`${T2}/material_comparison.png`);
  console.log('MAT_COMPOSITE_DONE');
})().catch(e=>{console.error(e);process.exit(1);});
