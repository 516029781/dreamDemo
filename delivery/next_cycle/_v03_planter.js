const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const T2='C:/软件/鼠鼠/delivery/next_cycle/T2';
const URL='http://127.0.0.1:8801/';
const TAG=process.argv[2]||'planter_before';
(async()=>{
 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage(); const logs=[];
 page.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await new Promise(r=>setTimeout(r,800));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await page.evaluate(()=>{window.__courtyard.resetView();window.__courtyard.reset();window.__courtyard.closeDialogue();window.__courtyard.setUi(false);});
 await new Promise(r=>setTimeout(r,1200));
 await page.evaluate(()=>window.__courtyard.setCameraMode('inspect'));
 await new Promise(r=>setTimeout(r,400));
 // west planter close-up pose
 await page.evaluate(()=>{
   const walk=n=>{const k=n.getComponent&&n.getComponent(window.cc.Camera);if(k&&k.node.name!=='UICamera')return k;for(const ch of n.children){const r=walk(ch);if(r)return r;}return null;};
   const cam=walk(window.cc.director.getScene());
   cam.node.setPosition(-7.2,5.4,-0.6);
   cam.node.lookAt(new window.cc.Vec3(-11.8,0.7,4.6));
 });
 await new Promise(r=>setTimeout(r,900));
 const stats=await page.evaluate(()=>window.__courtyard.renderStats());
 await page.screenshot({path:path.join(T2,`plant_${TAG}.png`)});
 fs.writeFileSync(path.join(T2,`plant_${TAG}_stats.json`),JSON.stringify({tag:TAG,cameraPose:{position:[-7.2,5.4,-0.6],lookAt:[-11.8,0.7,4.6],fov:35},stats},null,2)+'\n');
 await browser.close();
 console.log('V03_PLANTER_DONE',TAG,JSON.stringify(stats));
})().catch(e=>{console.error('FATAL',e);process.exit(1);});
