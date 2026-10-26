const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core'); const sharp=req('sharp');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const T2='C:/软件/鼠鼠/delivery/next_cycle/T2';
const URL='http://127.0.0.1:8801/';
(async()=>{
 fs.mkdirSync(T2,{recursive:true});
 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage(); const logs=[];
 page.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await new Promise(r=>setTimeout(r,800));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await page.evaluate(()=>{window.__courtyard.resetView();window.__courtyard.reset();window.__courtyard.closeDialogue();});
 await new Promise(r=>setTimeout(r,1200));

 // landscape toast with quest card visible
 await page.evaluate(()=>window.__courtyard.setUiState('toast_task_update'));
 await new Promise(r=>setTimeout(r,600));
 await page.screenshot({path:path.join(T2,'ui_toast_landscape_after.png')});

 // panel close-up (border check)
 const shot=path.join(T2,'ui_toast_landscape_after.png');
 await sharp(shot).extract({left:280,top:220,width:560,height:180}).resize(1120,360,{fit:'fill'}).png().toFile(path.join(T2,'ui_toast_border_zoom.png'));

 // portrait toast
 const p2=await browser.newPage();
 p2.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
 await p2.setViewport({width:720,height:1280,deviceScaleFactor:1});
 await p2.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await p2.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await p2.evaluate(()=>{const gd=document.getElementById('GameDiv');gd.style.width=window.innerWidth+'px';gd.style.height=window.innerHeight+'px';window.cc.view.resizeWithBrowserSize(true);window.dispatchEvent(new Event('resize'));});
 await new Promise(r=>setTimeout(r,700));
 await p2.evaluate(()=>{window.__courtyard.resetView();window.__courtyard.reset();window.__courtyard.closeDialogue();});
 await new Promise(r=>setTimeout(r,900));
 await p2.evaluate(()=>window.__courtyard.setUiState('toast_task_update'));
 await new Promise(r=>setTimeout(r,700));
 await p2.screenshot({path:path.join(T2,'ui_toast_portrait_after.png')});
 await p2.close();

 // dialogue panel border check (same sliced frame)
 await page.evaluate(()=>window.__courtyard.resetView());
 await new Promise(r=>setTimeout(r,300));
 await page.evaluate(()=>{window.__courtyard.reset();window.__courtyard.openDialogue(1);});
 await new Promise(r=>setTimeout(r,700));
 await page.screenshot({path:path.join(T2,'ui_dialogue_after.png')});

 await browser.close();
 fs.appendFileSync('C:/软件/鼠鼠/delivery/next_cycle/T1/t1_capture.log',logs.join('\n')+'\n');
 console.log('V05_SHOTS_DONE');
})().catch(e=>{console.error('FATAL',e);process.exit(1);});
