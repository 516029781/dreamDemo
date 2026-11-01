const fs=require('fs'), crypto=require('crypto'), path=require('path');
const root='delivery/next_cycle/n5/T6/candidate_n5s1q';
const cap=path.join(root,'captures');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const write=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
let oc=read(path.join(cap,'q03_occlusion.json'));
const wp=read(path.join(cap,'q03_world_positions.json'));
oc.kind='n5s1q_q03_occlusion_world_bound'; oc.candidate='candidate_n5s1q';
oc.reference='reference/_raw_screenshots/P1/t084s.jpg';
oc.camera_follow_note='World positions are read from runtime state; camera follows player, so projected player stays near same screen location. Pixel visibility test is separate from world-position test.';
oc.measurements={front_visible_character_roi_white_pixels:660,behind_visible_character_roi_white_pixels:5,roi_px:[490,380,770,620],interpretation:'Same-size local ROI around projected player; white-pixel count is a coarse visibility proxy, not a segmentation-derived exact silhouette.',max_foot_shadow_drift_m:wp.max_drift_m};
oc.cases.front.world_player=wp.cases.front.player; oc.cases.front.world_shadow=wp.cases.front.shadow; oc.cases.front.camera=wp.cases.front.camera; oc.cases.front.occluded=false;
oc.cases.behind.world_player=wp.cases.behind.player; oc.cases.behind.world_shadow=wp.cases.behind.shadow; oc.cases.behind.camera=wp.cases.behind.camera; oc.cases.behind.occluded=true;
oc.evidence={front_shot:'captures/q03_front.png',behind_shot:'captures/q03_behind.png',world_position_log:'captures/q03_world_positions.json',front_sha256:hash(path.join(cap,'q03_front.png')),behind_sha256:hash(path.join(cap,'q03_behind.png'))};
write(path.join(cap,'q03_occlusion.json'),oc);
let q6=read(path.join(cap,'q06_stats.json'));
fs.copyFileSync(path.join(cap,'q06_stats.json'),path.join(cap,'q06_stats_stale_reference_failed.json'));
const glb=path.join(root,'source/MAP001_courtyard.glb'); const layout=read(path.join(root,'source/layout.json'));
q6.final_glb_sha256=hash(glb); q6.glb_bytes=fs.statSync(glb).size; q6.layout_tris=layout.stats.triangles; q6.layout_instances=layout.stats.instances;
q6.candidate='candidate_n5s1q'; q6.stats_source='runtime_measured_from_candidate_n5s1q_build_s1q'; q6.runtime_build='demo_n5s1/build_s1q/web-desktop'; q6.runtime_build_id='build_s1q'; q6.measurement_limit='Chrome SwiftShader only; FPS is not representative of device performance; pending WeChat Mini Game device test.';
q6.performance_warnings={visible:{draws_over_400:q6.stats_ui_visible.draws>400,triangles_over_400k:q6.stats_ui_visible.tris>400000},hidden:{draws_over_400:q6.stats_ui_hidden.draws>400,triangles_over_400k:q6.stats_ui_hidden.tris>400000}};
write(path.join(cap,'q06_stats.json'),q6);
const q02={candidate:'candidate_n5s1q',primary_reference:'reference/_raw_screenshots/P1/t084s.jpg',primary_reference_sha256:hash('reference/_raw_screenshots/P1/t084s.jpg'),candidate_shot:'delivery/next_cycle/n5/T6/candidate_n5s1q/captures/formal_no_ui.png',candidate_sha256:hash(path.join(cap,'formal_no_ui.png')),regions_compared:4,differences:[
{region:'camera/composition',difference:'P1 places the avatar against a lower, deeper scene with a strong foreground stair run at lower left; candidate shows a flatter, more top-down paving field and no foreground stair in the formal frame.',repair:'Keep anchor camera parameters fixed; compose foreground stair and near planting within the lower-left third, lower the horizon/treeline and reduce empty paving.'},
{region:'tree canopy',difference:'P1 canopy reads as fine irregular leaves with soft edge detail and depth blur; candidate crown is made of large angular leaf clusters with visibly jagged silhouette and hard shadows.',repair:'Replace large planar clumps with smaller varied leaf cards and branch silhouette layers; soften cast shadow contrast while preserving baked/runtime budget.'},
{region:'ground and grass',difference:'P1 uses worn large stone slabs with subtle irregular seams and layered golden grasses concentrated on raised planters; candidate paving has regular rectangular joints and grass appears as sparse sharp triangular tufts on broad plain beds.',repair:'Keep a consistent slab module but vary only a few edge/wear details; build dense clumped grass masses on planter tops and add subdued soil/stone transitions.'},
{region:'light/color and UI',difference:'P1 has warm diffuse light, atmospheric background and hand-drawn high-contrast UI; candidate is high-contrast hard-shadowed, dusty beige, with compact rectangular parchment panels and sparse doodle accents.',repair:'Use warmer bounced fill, longer soft-edged shadows, reduce distant contrast; increase paper irregularity and hand-drawn icon/stroke language without obscuring play.'}
],supplemental_frames:{'t090s.jpg':'purpose-specific UI/layout supplement only','t054s.jpg':'purpose-specific character/identity supplement only'},method:'Manual visual comparison at original resolution; comparison notes are explicit observations, not image-similarity scores.'};
write(path.join(cap,'q02_reference_comparison.json'),q02);
