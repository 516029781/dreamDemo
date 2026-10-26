const sharp=require('C:/软件/鼠鼠/.tooling/node_modules/sharp');
const T2='C:/软件/鼠鼠/delivery/next_cycle/T2';
async function label(buf,text){
  const svg=Buffer.from(`<svg width="1280" height="46"><rect width="1280" height="46" fill="rgba(20,20,20,0.75)"/><text x="16" y="32" font-family="Arial" font-size="26" fill="#fff">${text}</text></svg>`);
  return sharp(buf).composite([{input:svg,top:0,left:0}]).png().toBuffer();
}
(async()=>{
  const cb=await label(`${T2}/tree_crown_before.png`,'BEFORE crown: fragmented ball clumps, see-through gaps (build GLB 00483c58)');
  const ca=await label(`${T2}/tree_crown_after.png`,'AFTER crown: continuous massed lobes + accent cards (build GLB c01dd774)');
  const fb=await label(`${T2}/tree_before_formal.png`,'BEFORE formal camera, UI hidden (tris 166294)');
  const fa=await label(`${T2}/tree_after_formal.png`,'AFTER formal camera, UI hidden (tris 155302)');
  const half=async b=>sharp(b).resize(1264,711,{fit:'fill'}).png().toBuffer();
  const [cb2,ca2,fb2,fa2]=await Promise.all([cb,ca,fb,fa].map(half));
  await sharp({create:{width:2560,height:1462,channels:3,background:{r:10,g:10,b:10}}})
    .composite([{input:cb2,top:4,left:4},{input:ca2,top:4,left:1276},{input:fb2,top:731,left:4},{input:fa2,top:731,left:1276}])
    .png().toFile(`${T2}/tree_before_after.png`);
  console.log('COMPOSITE_DONE');
})().catch(e=>{console.error(e);process.exit(1);});
