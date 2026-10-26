const path=require('path'); const fs=require('fs');
const {createRequire}=require('module'); const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer=req('puppeteer-core'); const sharp=req('sharp');
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT='C:/软件/鼠鼠/delivery/next_cycle';
const URL='http://127.0.0.1:8801/';
(async()=>{
 const browser=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],defaultViewport:{width:1280,height:720,deviceScaleFactor:1}});
 const page=await browser.newPage(); const logs=[];
 page.on('console',m=>logs.push('CONSOLE '+m.type()+' '+m.text()));
 page.on('pageerror',e=>logs.push('PAGEERROR '+String(e)));
 await page.goto(URL,{waitUntil:'networkidle2',timeout:60000});
 await page.addStyleTag({content:'html,body{overflow:hidden;background:#1c1b18;margin:0;padding:0}h1.header,p.footer{display:none!important}#GameDiv{width:1280px!important;height:720px!important;border:0!important;border-radius:0!important;box-shadow:none!important;margin:0!important}#Cocos3dGameContainer,#GameCanvas{width:1280px!important;height:720px!important}'});
 await page.setViewport({width:1280,height:720,deviceScaleFactor:1});
 await page.evaluate(()=>window.dispatchEvent(new Event('resize')));
 await new Promise(r=>setTimeout(r,600));
 await page.waitForFunction(()=>window.__COURTYARD_READY__===true,{timeout:60000});
 await page.evaluate(()=>{window.__courtyard.reset(); window.__courtyard.closeDialogue();});
 await new Promise(r=>setTimeout(r,1500));
 const shot=path.join(OUT,'_final_scene.png');
 await page.screenshot({path:shot});
 await sharp(shot).extract({left:110,top:430,width:220,height:270}).resize(440,540,{fit:'fill'}).png().toFile(path.join(OUT,'_final_npc_crop.png'));
 const state=await page.evaluate(()=>window.__courtyard.state());
 fs.writeFileSync(path.join(OUT,'_final_state.json'),JSON.stringify(state,null,2)+'\n');
 for(const id of ['FX002','FX003']){
  await page.evaluate((i)=>{window.__courtyard.resetView(); window.__courtyard.focusAsset(i);},id);
  await new Promise(r=>setTimeout(r,900));
  await page.screenshot({path:path.join(OUT,`_final_${id}.png`)});
 }
 await page.evaluate(()=>{window.__courtyard.resetView(); window.__courtyard.reset(); window.__courtyard.closeDialogue();});
 await browser.close();
 fs.writeFileSync(path.join(OUT,'_final_capture.log'),logs.join('\n')+'\n');
 console.log('FINAL_OK px='+state.metrics.px+' board='+state.boardState);
})().catch(e=>{console.error('FATAL',e);process.exit(1);});
