const fs=require('fs'),path=require('path'),{createRequire}=require('module');
const req=createRequire('C:/软件/鼠鼠/.tooling/package.json'),puppeteer=req('puppeteer-core');
const {captureCanvas}=require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');
const OUT='C:/软件/鼠鼠/delivery/next_cycle/n5/T6/candidate_n5s1q/captures';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const browser=await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('http://127.0.0.1:8806/',{waitUntil:'networkidle2',timeout:60000}); await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 const cases={};
 for(const [name,x,z] of [['front',0,-5.2],['behind',0,2.0]]){
  await page.evaluate(()=>{window.__courtyard.reset();window.__courtyard.closeDialogue();window.__courtyard.setUi(false);window.__courtyard.resetView()});
  await page.evaluate(([x,z])=>window.__courtyard.setPlayer(x,z),[x,z]);await sleep(900);
  const state=await page.evaluate(()=>window.__courtyard.state());
  const camera=await page.evaluate(()=>{const c=cc.director.getScene().getChildByName('Main Camera');return c?{position:[c.position.x,c.position.y,c.position.z],euler:[c.eulerAngles.x,c.eulerAngles.y,c.eulerAngles.z],fov:c.getComponent(cc.Camera).fov}:null});
  const shadow=await page.evaluate(()=>{const root=cc.director.getScene();let found=null;const visit=n=>{if(n.name==='ContactShadow')found=n;for(const c of n.children)if(!found)visit(c)};visit(root);if(!found)return null;const p=found.worldPosition;return [p.x,p.y,p.z]});
  const shot=await captureCanvas(page,path.join(OUT,'q03_'+name+'.png'),{hideStats:true});
  cases[name]={world_player:state.player,camera,state_camera:state.camera,shadow_world:shadow,metrics:state.metrics,capture:shot};
 }
 fs.writeFileSync(path.join(OUT,'q03_occlusion.json'),JSON.stringify({kind:'n5s1q_q03_occlusion',candidate:'candidate_n5s1q',viewport:[1280,720],cases,foot_shadow_drift_m:Math.max(...Object.values(cases).map(c=>Math.hypot(c.world_player[0]-c.shadow_world[0],c.world_player[2]-c.shadow_world[2]))),pageErrors:errors},null,2)+'\n');
 await browser.close();console.log(JSON.stringify({front:cases.front.world_player,behind:cases.behind.world_player,shadow:[cases.front.shadow_world,cases.behind.shadow_world],errors:errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
