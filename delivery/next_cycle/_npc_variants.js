const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core'); const sharp=req('sharp');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT='C:/软件/鼠鼠/delivery/next_cycle';
const URL='http://127.0.0.1:8801/';
const VARIANTS=[
 {name:'vflip', t:[1,-1,0,1]},
 {name:'both',  t:[-1,-1,1,1]},
 {name:'mirror',t:[-1,1,1,0]},
 {name:'plain', t:[1,1,0,0]},
];
(async()=>{
 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage();
 page.on('pageerror',e=>console.log('PAGEERROR',String(e)));
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await new Promise(r=>setTimeout(r,800));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await page.evaluate(()=>{window.__courtyard.reset(); window.__courtyard.closeDialogue();});
 await new Promise(r=>setTimeout(r,1000));
 for(const v of VARIANTS){
  await page.evaluate((t)=>{
   const cc=window.cc; const scene=cc.director.getScene(); let target=null;
   const walk=n=>{ if(n.name==='NpcWorldQuad') target=n; for(const c of n.children) walk(c); };
   walk(scene);
   const mr=(target.components||[]).find(c=>c&&c.mesh);
   if(!mr) throw new Error('no MeshRenderer on NpcWorldQuad, comps='+(target.components||[]).map(c=>c&&c.constructor&&c.constructor.name));
   const mat=mr.getMaterial(0);
   mat.setProperty('tilingOffset', new cc.Vec4(t[0],t[1],t[2],t[3]));
  },v.t);
  await new Promise(r=>setTimeout(r,300));
  const shot=path.join(OUT,`_npc_${v.name}.png`);
  await page.screenshot({path:shot});
  await sharp(shot).extract({left:110,top:430,width:220,height:270}).resize(440,540,{fit:'fill'}).png().toFile(path.join(OUT,`_npc_${v.name}_crop.png`));
  console.log('done',v.name);
 }
 await browser.close();
})().catch(e=>{console.error('FATAL',e);process.exit(1);});
