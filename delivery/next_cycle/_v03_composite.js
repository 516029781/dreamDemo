const sharp=require('C:/软件/鼠鼠/.tooling/node_modules/sharp');
const T2='C:/软件/鼠鼠/delivery/next_cycle/T2';
async function label(buf,text){
  const svg=Buffer.from(`<svg width="1280" height="46"><rect width="1280" height="46" fill="rgba(20,20,20,0.75)"/><text x="16" y="32" font-family="Arial" font-size="26" fill="#fff">${text}</text></svg>`);
  return sharp(buf).composite([{input:svg,top:0,left:0}]).png().toBuffer();
}
(async()=>{
  const b=await label(`${T2}/plant_planter_before.png`,'BEFORE west planter: single sparse seedling, bare soil (GLB 00483c58)');
  const a=await label(`${T2}/plant_planter_after.png`,'AFTER west planter: 2 massed shrubs + dry grass + litter (GLB d9d86eae)');
  const half=async x=>sharp(x).resize(1264,711,{fit:'fill'}).png().toBuffer();
  const [b2,a2]=await Promise.all([b,a].map(half));
  await sharp({create:{width:2560,height:719,channels:3,background:{r:10,g:10,b:10}}})
    .composite([{input:b2,top:4,left:4},{input:a2,top:4,left:1276}])
    .png().toFile(`${T2}/plant_group.png`);
  console.log('PLANT_COMPOSITE_DONE');
})().catch(e=>{console.error(e);process.exit(1);});
