const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL='http://127.0.0.1:8801/';
(async()=>{
 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage();
 page.on('pageerror',e=>console.log('PAGEERROR',String(e&&e.stack||e)));
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await new Promise(r=>setTimeout(r,800));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await page.evaluate(()=>{window.__courtyard.reset(); window.__courtyard.closeDialogue();});
 await new Promise(r=>setTimeout(r,1200));
 const info=await page.evaluate(()=>{
  const cc=window.cc; const scene=cc.director.getScene();
  const found={};
  const walk=(n)=>{ if(found[n.name]===undefined) found[n.name]=n; for(const c of n.children) walk(c); };
  walk(scene);
  const camNode=found['Camera']||found['Main Camera']||found['camera'];
  let cam=null;
  scene.walk?.(n=>{});
  // find camera component
  const cameras=[];
  const walk2=(n)=>{ const c=n.getComponent&&n.getComponent(cc.Camera); if(c) cameras.push({node:n.name,cam:c}); for(const ch of n.children) walk2(ch); };
  walk2(scene);
  const main=cameras.length?cameras[0].cam:null;
  const v3=o=>o?{x:o.x,y:o.y,z:o.z}:null;
  const out={cameras:cameras.map(x=>x.node.name), mainPos:v3(main?main.node.worldPosition:null)};
  const report={};
  for(const name of ['NpcWorldQuad','PlayerWorldQuad','FX002_pickup','FX003_board','ContactShadow','CharRTCanvas']){
    const n=found[name];
    if(!n){report[name]='MISSING';continue;}
    const wp=n.worldPosition;
    const wr=new cc.Vec3(); n.worldRotation && n.worldRotation.getEulerAngles(wr);
    const sp=main?main.worldToScreen(wp):null;
    report[name]={active:n.active,activeInHierarchy:n.activeInHierarchy,worldPos:v3(wp),euler:v3(wr),screen:sp?{x:sp.x,y:sp.y}:null};
  }
  out.nodes=report;
  const st=window.__courtyard.state();
  out.metrics=st.metrics; out.player=st.player;
  return out;
 });
 console.log(JSON.stringify(info,null,1));
 await browser.close();
})().catch(e=>{console.error('FATAL',e);process.exit(1);});
