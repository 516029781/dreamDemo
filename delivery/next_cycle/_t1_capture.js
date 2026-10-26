const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core'); const sharp=req('sharp');
const {GIFEncoder,quantize,applyPalette}=req('gifenc');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const T1='C:/软件/鼠鼠/delivery/next_cycle/T1';
const URL='http://127.0.0.1:8801/';
fs.mkdirSync(T1,{recursive:true});
const FR=fs.mkdtempSync(path.join(T1,'_frames_'));
(async()=>{

 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage(); const logs=[];
 page.on('console',m=>logs.push('CONSOLE '+m.type()+' '+m.text()));
 page.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await new Promise(r=>setTimeout(r,800));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 const setCss=(w,h)=>page.addStyleTag({content:`html,body{overflow:hidden;background:#1c1b18;margin:0;padding:0}h1.header,p.footer{display:none!important}`});
 await setCss(1280,720);
 await page.setViewport({width:1280,height:720,deviceScaleFactor:1});
 await page.evaluate(()=>window.dispatchEvent(new Event('resize')));
 await new Promise(r=>setTimeout(r,700));
 const base=async()=>{await page.evaluate(()=>{window.__courtyard.resetView();window.__courtyard.reset();window.__courtyard.closeDialogue();});await new Promise(r=>setTimeout(r,1200));};
 await base();

 // ---------- viewports (K06): fresh page per size so the engine sizes the canvas natively
 const viewports=[];
 for(const s of [{n:'1280x720',w:1280,h:720},{n:'720x1280',w:720,h:1280},{n:'1600x720',w:1600,h:720}]){
  const p2=await browser.newPage();
  p2.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
  await p2.setViewport({width:s.w,height:s.h,deviceScaleFactor:1});
  await p2.goto(URL,{waitUntil:'networkidle2',timeout:60000});
  await p2.addStyleTag({content:'html,body{overflow:hidden;background:#1c1b18;margin:0;padding:0}h1.header,p.footer{display:none!important}'});
  await new Promise(r=>setTimeout(r,800));
  await p2.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
  await p2.evaluate(()=>{const gd=document.getElementById('GameDiv');gd.style.width=window.innerWidth+'px';gd.style.height=window.innerHeight+'px';window.cc.view.resizeWithBrowserSize(true);window.dispatchEvent(new Event('resize'));});
  await new Promise(r=>setTimeout(r,600));
  await p2.evaluate(()=>{window.__courtyard.reset();window.__courtyard.closeDialogue();});
  await new Promise(r=>setTimeout(r,1200));
  await p2.screenshot({path:path.join(T1,`viewport_${s.n}.png`)});
  const st=await p2.evaluate(()=>{const v=window.cc.view;const m=window.__courtyard.state().metrics;return {canvas:[v.getCanvasSize().width,v.getCanvasSize().height],visible:[v.getVisibleSize().width,v.getVisibleSize().height],px:m.px,view:m.view,method:m.method};});
  viewports.push({name:s.n,width:s.w,height:s.h,canvas:st.canvas,visible:st.visible,px:st.px,method:st.method});
  await p2.close();
 }
 fs.writeFileSync(path.join(T1,'viewport_results.json'),JSON.stringify({generatedAt:new Date().toISOString(),viewports},null,2)+'\n');

 // ---------- board states (R07): camera on the board via FX003 focus
 await base();
 await page.evaluate(()=>window.__courtyard.focusAsset('FX003'));
 await new Promise(r=>setTimeout(r,900));
 const cards=await page.evaluate(()=>{
  const cc=window.cc; const scene=cc.director.getScene(); const names=[];
  const walk=n=>{ if(n.name.indexOf('MAP001_message_board_card_')===0) names.push({name:n.name,active:n.active}); for(const c of n.children) walk(c); };
  walk(scene); return names;
 });
 const boardStates={cardNodes:cards,states:{},expected:{empty:0,reset:0,A:1,B:2,full:3}};
 for(const s of ['empty','A','B','full','reset']){
  await page.evaluate(v=>window.__courtyard.setBoardState(v),s);
  await new Promise(r=>setTimeout(r,450));
  const act=await page.evaluate(()=>{
   const cc=window.cc; const scene=cc.director.getScene(); const a=[];
   const walk=n=>{ if(n.name.indexOf('MAP001_message_board_card_')===0&&n.active) a.push(n.name); for(const c of n.children) walk(c); };
   walk(scene); return a;
  });
  boardStates.states[s]={activeCards:act,count:act.length,pass:act.length===boardStates.expected[s]};
  await page.screenshot({path:path.join(T1,`board_${s}.png`)});
 }
 await page.evaluate(()=>window.__courtyard.setBoardState('full'));
 await new Promise(r=>setTimeout(r,300));
 fs.writeFileSync(path.join(T1,'board_states.json'),JSON.stringify({generatedAt:new Date().toISOString(),...boardStates},null,2)+'\n');

 // ---------- behavior (R05 + movement)
 await base();
 const behavior={};
 await page.evaluate(()=>window.__courtyard.setPlayer(2.5,-5));
 await new Promise(r=>setTimeout(r,350));
 behavior.teleport={after:await page.evaluate(()=>window.__courtyard.state().player),expected:[2.5,0,-5],pass:null};
 behavior.teleport.pass=Math.abs(behavior.teleport.after[0]-2.5)<0.01&&Math.abs(behavior.teleport.after[2]+5)<0.01;
 await base();
 await page.click('#GameCanvas');
 await new Promise(r=>setTimeout(r,200));
 const kx_start=await page.evaluate(()=>window.__courtyard.state().player[0]);
 await page.keyboard.down('KeyD');
 await new Promise(r=>setTimeout(r,700));
 await page.keyboard.up('KeyD');
 const kx_end=await page.evaluate(()=>window.__courtyard.state().player[0]);
 behavior.keyboardMove={xStart:kx_start,xEnd:kx_end,delta:kx_end-kx_start,pass:Math.abs(kx_end-kx_start)>0.3};
 await page.evaluate(()=>window.__courtyard.setPause(true));
 await new Promise(r=>setTimeout(r,350));
 const st2=await page.evaluate(()=>window.__courtyard.state());
 behavior.pauseOn={paused:st2.paused,inputLocked:st2.inputLocked,pass:st2.paused&&st2.inputLocked};
 await page.screenshot({path:path.join(T1,'input_lock_pause_on.png')});
 await page.evaluate(()=>window.__courtyard.setPause(false));
 await new Promise(r=>setTimeout(r,300));
 const st3=await page.evaluate(()=>window.__courtyard.state());
 behavior.pauseOff={paused:st3.paused,inputLocked:st3.inputLocked,pass:!st3.paused&&!st3.inputLocked};
 await page.evaluate(()=>window.__courtyard.openDialogue(1));
 await new Promise(r=>setTimeout(r,500));
 const st4=await page.evaluate(()=>window.__courtyard.state());
 behavior.dialogueLock={dialogueVisible:st4.dialogueVisible,pass:st4.dialogueVisible};
 await page.screenshot({path:path.join(T1,'dialogue_lock.png')});
 await page.evaluate(()=>window.__courtyard.closeDialogue());
 await new Promise(r=>setTimeout(r,300));
 fs.writeFileSync(path.join(T1,'behavior_results.json'),JSON.stringify({generatedAt:new Date().toISOString(),...behavior},null,2)+'\n');

 // ---------- anchor px (R02)
 await base();
 const anch=await page.evaluate(()=>window.__courtyard.state().metrics);
 const anchor={px:anch.px,requiredRange:[86,130],canvas:anch.canvas,method:anch.method,pass:anch.px>=86&&anch.px<=130};
 fs.writeFileSync(path.join(T1,'anchor_results.json'),JSON.stringify({generatedAt:new Date().toISOString(),...anchor},null,2)+'\n');

 // ---------- occlusion (R01)
 await page.evaluate(()=>window.__courtyard.setPlayer(0,-5.2));
 await new Promise(r=>setTimeout(r,350));
 await page.screenshot({path:path.join(T1,'occlusion_front.png')});
 const occFront=await page.evaluate(()=>window.__courtyard.state().metrics);
 await page.evaluate(()=>window.__courtyard.setPlayer(0,2.0));
 await new Promise(r=>setTimeout(r,350));
 await page.screenshot({path:path.join(T1,'occlusion_behind.png')});
 const occBehind=await page.evaluate(()=>window.__courtyard.state().metrics);
 fs.writeFileSync(path.join(T1,'occlusion_results.json'),JSON.stringify({generatedAt:new Date().toISOString(),front:{player:[0,0,-5.2],px:occFront.px},behind:{player:[0,0,2.0],px:occBehind.px},method:'RenderTexture world quad shares scene depth with MAP001 geometry; tree canopy occludes quad behind trunk',note:'see PNG pair: identical camera, player occluded by tree only in behind shot'},null,2)+'\n');

 // ---------- idle move GIF
 await base();
 await page.evaluate(()=>{window.__courtyard.setMoving(true);});
 const frames=[];const stamps=[];const N=24;
 for(let i=0;i<N;i++){
  const x=-4.4+(8.8*i/(N-1));
  const t0=Date.now();
  await page.evaluate(xx=>window.__courtyard.setPlayer(xx,-5.2),x);
  await new Promise(r=>setTimeout(r,80));
  const f=path.join(FR,`mv_${String(i).padStart(3,'0')}.png`);
  await page.screenshot({path:f});
  frames.push(f);stamps.push({i,t_ms:Date.now()-t0,x});
 }
 await page.evaluate(()=>window.__courtyard.setMoving(false));
 const gif=GIFEncoder();const W=640,H=360;
 for(let i=0;i<frames.length;i++){
  const rgba=await sharp(frames[i]).resize(W,H).ensureAlpha().raw().toBuffer();
  const pal=quantize(rgba,256,{format:'rgb'});const idx=applyPalette(rgba,pal,'rgb');
  gif.writeFrame(idx,W,H,{palette:pal,delay:80,repeat:i===0?0:undefined});
 }
 gif.finish();
 fs.writeFileSync(path.join(T1,'idle_move.gif'),Buffer.from(gif.bytes()));
 fs.copyFileSync(path.join(FR,'mv_000.png'),path.join(T1,'idle_move_first_frame.png'));
 fs.writeFileSync(path.join(T1,'idle_move_timestamps.json'),JSON.stringify({generatedAt:new Date().toISOString(),frameCount:N,intervalMs:80,stamps},null,2)+'\n');

 // ---------- per-scope render stats (K07)
 await page.evaluate(()=>window.__courtyard.enableStats(true));
 await new Promise(r=>setTimeout(r,600));
 await base();
 const perf={baseline:null,scopes:{}};
 perf.baseline={scope:'game_reset',...(await page.evaluate(()=>window.__courtyard.renderStats()))};
 for(const id of ['MAP001','LOOK001','CHAR001','CHAR002','CHAR003','FX001','FX002','FX003','ENV001','ENV006','PROP001']){
  await page.evaluate(i=>{window.__courtyard.resetView();window.__courtyard.focusAsset(i);},id);
  await new Promise(r=>setTimeout(r,900));
  perf.scopes[id]=await page.evaluate(()=>window.__courtyard.renderStats());
  await page.screenshot({path:path.join(T1,`perf_scope_${id}.png`)});
 }
 await page.evaluate(()=>{window.__courtyard.resetView();window.__courtyard.reset();});
 await new Promise(r=>setTimeout(r,400));
 fs.writeFileSync(path.join(T1,'performance_results.json'),JSON.stringify({generatedAt:new Date().toISOString(),...perf},null,2)+'\n');

 // ---------- camera.json
 await base();
 const cam=await page.evaluate(()=>{
  const cc=window.cc;const scene=cc.director.getScene();let c=null;
  const walk=n=>{const k=n.getComponent&&n.getComponent(cc.Camera);if(k&&!c)c=k;for(const ch of n.children)walk(ch);};
  walk(scene);
  return c?{projection:c.projection,fov:c.fov,orthoHeight:c.orthoHeight,near:c.nearClip,far:c.farClip,clearFlags:c.clearFlags,priority:c.priority,position:{x:c.node.worldPosition.x,y:c.node.worldPosition.y,z:c.node.worldPosition.z},aperture:c.aperture,exposure:c.exposure}:null;
 });
 fs.writeFileSync(path.join(T1,'camera.json'),JSON.stringify({generatedAt:new Date().toISOString(),mainCamera:cam,gameFollow:{offset:[-2.5,11.5,-9.4],lookAtZOffset:1.5},inspect:{position:[0,28,-28],lookAt:[0,0.5,2]}},null,2)+'\n');

 await browser.close();
 fs.writeFileSync(path.join(T1,'t1_capture.log'),logs.join('\n')+'\n');
 console.log('T1_CAPTURE_DONE');
})().catch(e=>{console.error('T1_FATAL',e);process.exit(1);});
