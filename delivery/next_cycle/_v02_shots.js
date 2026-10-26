const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const T2='C:/软件/鼠鼠/delivery/next_cycle/T2';
const URL='http://127.0.0.1:8801/';
const TAG=process.argv[2]||'mat_before';
(async()=>{
 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage(); const logs=[];
 page.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
 page.on('console',m=>{const t=m.text(); if(t.includes('[MAT]')||t.includes('[COURTYARD]'))logs.push(t);});
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await new Promise(r=>setTimeout(r,800));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await page.evaluate(()=>{window.__courtyard.resetView();window.__courtyard.reset();window.__courtyard.closeDialogue();window.__courtyard.setUi(false);});
 await new Promise(r=>setTimeout(r,1200));
 await page.evaluate(()=>window.__courtyard.setCameraMode('inspect'));
 await new Promise(r=>setTimeout(r,400));
 const poses={
   paving:{pos:[-1.5,7.5,-10.5],look:[0,0.05,-2.5]},
   bench:{pos:[-6.0,3.4,-8.6],look:[-9.3,0.75,-4.4]},
   fence:{pos:[8.6,4.2,3.4],look:[11.9,1.0,4.8]},
 };
 for(const [name,p] of Object.entries(poses)){
   await page.evaluate((pos,look)=>{
     const walk=n=>{const k=n.getComponent&&n.getComponent(window.cc.Camera);if(k&&k.node.name!=='UICamera')return k;for(const ch of n.children){const r=walk(ch);if(r)return r;}return null;};
     const cam=walk(window.cc.director.getScene());
     cam.node.setPosition(pos[0],pos[1],pos[2]);
     cam.node.lookAt(new window.cc.Vec3(look[0],look[1],look[2]));
   },p.pos,p.look);
   await new Promise(r=>setTimeout(r,800));
   await page.screenshot({path:path.join(T2,`mat_${TAG}_${name}.png`)});
 }
 fs.writeFileSync(path.join(T2,`mat_${TAG}_stats.json`),JSON.stringify({tag:TAG,poses,logs:logs.slice(-20)},null,2)+'\n');
 await browser.close();
 console.log('MAT_SHOTS_DONE',TAG);
})().catch(e=>{console.error('FATAL',e);process.exit(1);});
