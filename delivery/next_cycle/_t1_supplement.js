const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core'); const sharp=req('sharp');
const {GIFEncoder,quantize,applyPalette}=req('gifenc');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const T1='C:/软件/鼠鼠/delivery/next_cycle/T1';
const URL='http://127.0.0.1:8801/';
(async()=>{
 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage(); const logs=[];
 page.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await new Promise(r=>setTimeout(r,800));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 const base=async()=>{await page.evaluate(()=>{window.__courtyard.resetView();window.__courtyard.reset();window.__courtyard.closeDialogue();});await new Promise(r=>setTimeout(r,1100));};

 // ---------- K04: displacement during locks (keyboard-driven)
 const lock={};
 await base();
 await page.click('#GameCanvas');
 await new Promise(r=>setTimeout(r,200));
 await page.evaluate(()=>window.__courtyard.setPause(true));
 await new Promise(r=>setTimeout(r,300));
 const p0=await page.evaluate(()=>window.__courtyard.state().player);
 await page.keyboard.down('KeyD');
 await new Promise(r=>setTimeout(r,700));
 await page.keyboard.up('KeyD');
 const p1=await page.evaluate(()=>window.__courtyard.state().player);
 lock.pausedDisplacement={before:p0,after:p1,delta:Math.hypot(p1[0]-p0[0],p1[2]-p0[2]),pass:Math.hypot(p1[0]-p0[0],p1[2]-p0[2])<=1e-3};
 await page.screenshot({path:path.join(T1,'input_lock_pause_key.png')});
 await page.evaluate(()=>window.__courtyard.setPause(false));
 await new Promise(r=>setTimeout(r,300));
 await page.evaluate(()=>window.__courtyard.openDialogue(1));
 await new Promise(r=>setTimeout(r,400));
 const d0=await page.evaluate(()=>window.__courtyard.state().player);
 await page.keyboard.down('KeyS');
 await new Promise(r=>setTimeout(r,700));
 await page.keyboard.up('KeyS');
 const d1=await page.evaluate(()=>window.__courtyard.state().player);
 lock.dialogueDisplacement={before:d0,after:d1,delta:Math.hypot(d1[0]-d0[0],d1[2]-d0[2]),pass:Math.hypot(d1[0]-d0[0],d1[2]-d0[2])<=1e-3};
 await page.evaluate(()=>window.__courtyard.closeDialogue());
 await new Promise(r=>setTimeout(r,300));
 await page.click('#GameCanvas');
 await new Promise(r=>setTimeout(r,150));
 const r0=await page.evaluate(()=>window.__courtyard.state().player);
 await page.keyboard.down('KeyD');
 await new Promise(r=>setTimeout(r,500));
 await page.keyboard.up('KeyD');
 const r1=await page.evaluate(()=>window.__courtyard.state().player);
 lock.resumeRespondsToNewInput={before:r0,after:r1,delta:Math.hypot(r1[0]-r0[0],r1[2]-r0[2]),pass:Math.hypot(r1[0]-r0[0],r1[2]-r0[2])>0.1};
 fs.writeFileSync(path.join(T1,'input_lock_results.json'),JSON.stringify({generatedAt:new Date().toISOString(),...lock,note:'mp4 replaced by PNG+JSON per task output_policy (no validated encoder)'},null,2)+'\n');

 // ---------- K05: board transition GIF + timestamps
 await base();
 await page.evaluate(()=>window.__courtyard.focusAsset('FX003'));
 await new Promise(r=>setTimeout(r,900));
 const seq=['empty','A','B','full','reset','full'];
 const frames=[];const stamps=[];
 for(let i=0;i<seq.length;i++){
  const t0=Date.now();
  await page.evaluate(s=>window.__courtyard.setBoardState(s),seq[i]);
  await new Promise(r=>setTimeout(r,500));
  const f=path.join(T1,`_bt_${i}_${seq[i]}.png`);
  await page.screenshot({path:f});
  frames.push(f);stamps.push({i,state:seq[i],t_ms:Date.now()-t0});
 }
 const gif=GIFEncoder();const W=640,H=360;
 for(let i=0;i<frames.length;i++){
  const rgba=await sharp(frames[i]).resize(W,H).ensureAlpha().raw().toBuffer();
  const pal=quantize(rgba,256,{format:'rgb'});const idx=applyPalette(rgba,pal,'rgb');
  gif.writeFrame(idx,W,H,{palette:pal,delay:500,repeat:0});
 }
 gif.finish();
 fs.writeFileSync(path.join(T1,'board_transition.gif'),Buffer.from(gif.bytes()));
 for(const f of frames) fs.unlinkSync(f);
 fs.writeFileSync(path.join(T1,'board_transition_timestamps.json'),JSON.stringify({generatedAt:new Date().toISOString(),sequence:seq,stamps,note:'mp4 replaced by GIF+timestamps per task output_policy'},null,2)+'\n');

 // ---------- K06: portrait toast readability
 await base();
 const p2=await browser.newPage();
 p2.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
 await p2.setViewport({width:720,height:1280,deviceScaleFactor:1});
 await p2.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await p2.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await p2.evaluate(()=>{const gd=document.getElementById('GameDiv');gd.style.width=window.innerWidth+'px';gd.style.height=window.innerHeight+'px';window.cc.view.resizeWithBrowserSize(true);window.dispatchEvent(new Event('resize'));});
 await new Promise(r=>setTimeout(r,700));
 await p2.evaluate(()=>{window.__courtyard.reset();window.__courtyard.closeDialogue();});
 await new Promise(r=>setTimeout(r,900));
 await p2.evaluate(()=>window.__courtyard.setUiState('toast_task_update'));
 await new Promise(r=>setTimeout(r,700));
 await p2.screenshot({path:path.join(T1,'viewport_portrait_toast_720x1280.png')});
 await p2.evaluate(()=>window.__courtyard.resetView());
 await p2.close();

 await browser.close();
 fs.appendFileSync(path.join(T1,'t1_capture.log'),logs.join('\n')+'\n');
 console.log('SUPPLEMENT_DONE',JSON.stringify({pausedDelta:lock.pausedDisplacement.delta,dialogueDelta:lock.dialogueDisplacement.delta,resumeDelta:lock.resumeRespondsToNewInput.delta}));
})().catch(e=>{console.error('FATAL',e);process.exit(1);});
