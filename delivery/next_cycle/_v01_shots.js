const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core'); const sharp=req('sharp');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const T2='C:/软件/鼠鼠/delivery/next_cycle/T2';
const URL='http://127.0.0.1:8801/';
const TAG=process.argv[2]||'before';
(async()=>{
 fs.mkdirSync(T2,{recursive:true});
 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage(); const logs=[];
 page.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
 page.on('console',m=>{const t=m.text(); if(t.includes('[COURTYARD]'))logs.push(t);});
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await new Promise(r=>setTimeout(r,800));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await page.evaluate(()=>{window.__courtyard.resetView();window.__courtyard.reset();window.__courtyard.closeDialogue();window.__courtyard.enableStats(true);});
 await new Promise(r=>setTimeout(r,1500));

 // 1) formal game camera, UI hidden
 await page.evaluate(()=>window.__courtyard.setUi(false));
 await new Promise(r=>setTimeout(r,600));
 const stats1=await page.evaluate(()=>window.__courtyard.renderStats());
 await page.screenshot({path:path.join(T2,`tree_${TAG}_formal.png`)});

 // 2) fixed inspection close-up on ENV006
 await page.evaluate(()=>window.__courtyard.focusAsset('ENV006'));
 await new Promise(r=>setTimeout(r,900));
 const stats2=await page.evaluate(()=>window.__courtyard.renderStats());
 await page.screenshot({path:path.join(T2,`tree_${TAG}_close.png`)});

 fs.writeFileSync(path.join(T2,`tree_${TAG}_stats.json`),JSON.stringify({tag:TAG,formal:stats1,closeup:stats2,logs:logs.slice(-12)},null,2)+'\n');
 await browser.close();
 console.log('V01_SHOTS_DONE',TAG,JSON.stringify(stats1),JSON.stringify(stats2));
})().catch(e=>{console.error('FATAL',e);process.exit(1);});
