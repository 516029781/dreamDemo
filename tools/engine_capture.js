const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core'); const sharp=req('sharp'); const {GIFEncoder,quantize,applyPalette}=req('gifenc');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT='C:/软件/鼠鼠/art/full/previews/engine';
const FRAMES=path.join(OUT,'frames');
const URL='http://127.0.0.1:8801/';
(async()=>{
 fs.mkdirSync(OUT,{recursive:true});
 fs.mkdirSync(FRAMES,{recursive:true});
 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage(); const logs=[];
 page.on('console',m=>logs.push('CONSOLE '+m.type()+' '+m.text()));
 page.on('pageerror',e=>logs.push('PAGEERROR '+String(e&&e.stack||e)));
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await page.addStyleTag({content:'html,body{overflow:hidden;background:#1c1b18;margin:0;padding:0}h1.header,p.footer{display:none!important}#GameDiv{width:1280px!important;height:720px!important;border:0!important;border-radius:0!important;box-shadow:none!important;margin:0!important}#Cocos3dGameContainer,#GameCanvas{width:1280px!important;height:720px!important}'});
 await page.setViewport({width:1280,height:720,deviceScaleFactor:1});
 await page.evaluate(()=>window.dispatchEvent(new Event('resize')));
 await new Promise(r=>setTimeout(r,600));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await page.evaluate(()=>{window.__courtyard.reset(); window.__courtyard.closeDialogue();});
 await new Promise(r=>setTimeout(r,1200));
 await page.screenshot({path:path.join(OUT,'scene_gameplay_1280x720.png')});
 await page.evaluate(()=>window.__courtyard.setUi(false));
 await new Promise(r=>setTimeout(r,300));
 await page.screenshot({path:path.join(OUT,'scene_no_ui_1280x720.png')});
 await page.evaluate(()=>{window.__courtyard.setUi(true); window.__courtyard.openDialogue(1);});
 await new Promise(r=>setTimeout(r,700));
 await page.screenshot({path:path.join(OUT,'dialogue_npc_1280x720.png')});
 await page.evaluate(()=>window.__courtyard.openDialogue(2));
 await new Promise(r=>setTimeout(r,500));
 await page.screenshot({path:path.join(OUT,'dialogue_player_1280x720.png')});
 // real engine movement frames: reset, then move player along a short path
 await page.evaluate(()=>{window.__courtyard.setUi(true); window.__courtyard.closeDialogue(); window.__courtyard.reset(); window.__courtyard.setMoving(true);});
 const frames=[]; const N=24;
 for(let i=0;i<N;i++){
   const x=-4.4 + (8.8*i/(N-1));
   await page.evaluate(({x})=>window.__courtyard.setPlayer(x,-5.2),{x});
   await new Promise(r=>setTimeout(r,80));
   const f=path.join(FRAMES,'move_'+String(i).padStart(3,'0')+'.png');
   await page.screenshot({path:f});
   frames.push(f);
 }
 const state=await page.evaluate(()=>window.__courtyard.state()).catch(()=>null);
 fs.writeFileSync(path.join(OUT,'engine_state.json'),JSON.stringify(state,null,2)+'\n');
 await browser.close();
 const gif=GIFEncoder(); const W=640,H=360; for(let i=0;i<frames.length;i++){
   const rgba=await sharp(frames[i]).resize(W,H).ensureAlpha().raw().toBuffer();
   const pal=quantize(rgba,256,{format:'rgb'}); const idx=applyPalette(rgba,pal,'rgb');
   gif.writeFrame(idx,W,H,{palette:pal,delay:80,repeat:i===0?0:undefined});
 }
 gif.finish(); fs.writeFileSync(path.join(OUT,'demo_recording.gif'),Buffer.from(gif.bytes()));
 fs.writeFileSync(path.join(OUT,'engine_capture.log'),logs.join('\n')+'\n');
 console.log('ENGINE_CAPTURE_DONE',JSON.stringify({frames:frames.length,state},null,1));
})().catch(e=>{console.error('ENGINE_CAPTURE_FATAL',e);process.exit(1);});
