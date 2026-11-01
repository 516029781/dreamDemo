const fs=require('fs'),path=require('path'),{createRequire}=require('module');
const req=createRequire('C:/软件/鼠鼠/.tooling/package.json'),puppeteer=req('puppeteer-core');
const {captureCanvas}=require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');
const out='C:/软件/鼠鼠/delivery/next_cycle/n5/T6/candidate_n5s1j/captures';fs.mkdirSync(out,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{const b=await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});const p=await b.newPage();const errors=[];p.on('pageerror',e=>errors.push(String(e)));await p.goto('http://127.0.0.1:8806/',{waitUntil:'networkidle2',timeout:60000});await p.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:90000});const api=()=>window.__courtyard;
for(const [name,setup,cam] of [
 ['formal_no_ui',()=>{window.__courtyard.reset();window.__courtyard.closeDialogue();window.__courtyard.resetView();window.__courtyard.setUi(false);},{preset:'A',positionOffset:[-0.5,11.5,-9.4],lookOffset:[-0.5,2.4,1.5],spawn:[-4.5,0,-5.2],fov:37.5}],
 ['formal_ui',()=>{window.__courtyard.reset();window.__courtyard.closeDialogue();window.__courtyard.resetView();window.__courtyard.setUi(true);},{preset:'A',positionOffset:[-0.5,11.5,-9.4],lookOffset:[-0.5,2.4,1.5],spawn:[-4.5,0,-5.2],fov:37.5}],
 ['dialogue_page1',async()=>{window.__courtyard.reset();window.__courtyard.walkTo(-1.5,-5.2,0.12);await window.__courtyard.waitForFocus('gardener',3000);window.__courtyard.interact();},{preset:'A-dialogue',position:[0.5,11.5,-14.6],lookAt:[0.5,1.7,-3.7],fov:37.5}],
]){await p.evaluate(setup);await delay(1200);const state=await p.evaluate(()=>window.__courtyard.state());const shot=await captureCanvas(p,path.join(out,name+'.png'),{hideStats:true});fs.writeFileSync(path.join(out,name+'.json'),JSON.stringify({name,camera:cam,state,shot,pageErrors:errors},null,2)+'\n');}
await b.close();})().catch(e=>{console.error(e);process.exit(1)});





