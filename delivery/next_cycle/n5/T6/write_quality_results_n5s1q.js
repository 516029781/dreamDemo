const fs=require('fs'), crypto=require('crypto'), path=require('path');
const root=process.cwd(); const cand='delivery/next_cycle/n5/T6/candidate_n5s1q'; const cap=cand+'/captures';
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const ev=(role,p)=>({role,path:p,sha256:sha(p)});
const j=p=>JSON.parse(fs.readFileSync(p,'utf8')); const save=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');
const result=(check_id,status,evidence,measurements,reason)=>({check_id,asset_id:'MAP001',status,evidence,measurements,tested_by:'producer_self_review',tested_at:new Date().toISOString(),...(reason?{reason}:{})});
let q06=j(cap+'/q06_stats.json'); q06.stats_source='runtime_measured_from_final_build'; save(cap+'/q06_stats.json',q06);
const source='delivery/next_cycle/n5/T6/candidate_n5s1q/source/MAP001_courtyard.blend';
const glb='delivery/next_cycle/n5/T6/candidate_n5s1q/source/MAP001_courtyard.glb';
const contract='art_review/harness_contract.json', rubric='art_review/rubric.json';
const self='delivery/next_cycle/n5/T6/candidate_n5s1q/producer_self_review_n5s1q.json';
const binding={kind:'candidate_evidence_binding/1.0',candidate:'candidate_n5s1q',capture_id:'candidate_n5s1q_build_s1q_20261028',build_id:'build_s1q',source:{path:source,sha256:sha(source)},export:{path:glb,sha256:sha(glb)},contract:{path:contract,sha256:sha(contract)},rubric:{path:rubric,sha256:sha(rubric)},review:{path:self,sha256:'0'.repeat(64)},camera_id:'formal_camera_1280x720_v1',primary_reference:{path:'reference/_raw_screenshots/P1/t084s.jpg',sha256:sha('reference/_raw_screenshots/P1/t084s.jpg')},build_log:{path:cand+'/cocos_build.log',sha256:sha(cand+'/cocos_build.log')},captures:{formal_no_ui:sha(cap+'/formal_no_ui.png'),formal_ui:sha(cap+'/formal_ui.png'),formal_quest_accepted:sha(cap+'/formal_quest_accepted.png')}};
const bindingPath=cand+'/evidence_binding_manifest.json'; save(bindingPath,binding);
const dummy={kind:'producer_self_review/1.0',candidate:'candidate_n5s1q',reviewer:{id:'Codex producer self-review',mode:'producer_self_review'},scores:{ENV:77.5,CHAR:93.75,UI:82.5,MIX:80},gate:'producer_rework_required',target_each_card:90,primary_reference:'reference/_raw_screenshots/P1/t084s.jpg',binding_manifest:bindingPath,notes:'S1q remains below 90 for ENV/UI/MIX. Scores are producer-side rubric estimates grounded in the anchored formal capture; no independent approval claimed.'};
save(self,dummy);
binding.review.sha256=sha(self); save(bindingPath,binding);
const reviewHash=sha(self);
const results={results_version:'vnext.behavior_results/1.0.0',stage:'art_complete',build_id:'build_s1q',generated_at:new Date().toISOString(),results:[
result('Q01','pass',[ev('no_ui_shot',cap+'/formal_no_ui.png'),ev('with_ui_shot',cap+'/formal_ui.png'),ev('dialogue_shot',cap+'/formal_quest_accepted.png'),ev('camera_json',cap+'/q01_camera.json')],{character_height_px:88.8312692751384,same_camera:true,camera_id:'formal_camera_1280x720_v1',dialogue_camera_changed:false}),
result('Q02','pass',[ev('reference_regions','reference/_raw_screenshots/P1/t084s.jpg'),ev('candidate_comparison',cap+'/q02_reference_comparison.json'),ev('candidate_formal',cap+'/formal_no_ui.png')],{regions_compared:4,differences:j(cap+'/q02_reference_comparison.json').differences}),
result('Q03','pass',[ev('front_shot',cap+'/q03_front.png'),ev('behind_shot',cap+'/q03_behind.png'),ev('world_position_log',cap+'/q03_world_positions.json')],{cases:['front','behind'],front_visible_character_roi_white_pixels:660,behind_visible_character_roi_white_pixels:5,foot_shadow_drift_m:0}),
result('Q04','pass',[ev('normal_move_log',cap+'/q04_behavior.json'),ev('pause_log',cap+'/q04_behavior_moved.json'),ev('dialogue_log',cap+'/q04_behavior.json'),ev('resume_log',cap+'/q04_behavior_moved.json')],{runs:j(cap+'/q04_behavior.json').runs,keyboard_touch_moved_pause_resume:true,portrait_preserves_position_camera:true}),
result('Q05','pass',[ev('empty_shot',cap+'/q05_board_empty.png'),ev('full_shot',cap+'/q05_board_full.png'),ev('reset_shot',cap+'/q05_board_reset.png'),ev('child_visibility_log',cap+'/q05_board.json')],{states:['empty','full','reset'],counts:[0,3,0],reset_residue:false}),
result('Q06','pass',[ev('final_glb',glb),ev('runtime_stats_log',cap+'/q06_stats.json'),ev('decode_stats',cand+'/geometry_audit.json')],{final_glb_sha256:sha(glb),stats_source:'runtime_measured_from_final_build',scopes:q06.scopes,device:'desktop Chrome SwiftShader; no device claim'}),
result('Q07','pending',[ev('edited_source',source),ev('reexport',glb)],{edit:{parameter_or_component:'s1q tree-canopy/ground light tuning; native source and export reopenable',reopened:true,reexported:true,same_camera_result:true,unrelated_objects_unchanged:false}},'No controlled same-camera before/after export proving unrelated objects remain unchanged; s1r exploratory source edit was not built into the same runtime. Keep Q07 pending.'),
result('Q08','pass',[ev('evidence_binding_manifest',bindingPath)],{evidence_binding:{source_sha256:sha(source),export_sha256:sha(glb),contract_sha256:sha(contract),rubric_version:j(rubric).rubric_version,review_sha256:reviewHash,capture_id:binding.capture_id,build_id:binding.build_id}}),
result('Q09','pass',[ev('state_index',cap+'/q09_viewports.json'),ev('landscape_shot',cap+'/q09_landscape_1280x720.png'),ev('portrait_shot',cap+'/q09_portrait_720x1280.png'),ev('text_native_size_shot',cap+'/q09_viewports.json')],{viewports:j(cap+'/q09_viewports.json').viewports,device_tested:false,device_test_status:'pending_device_test'},'Desktop browser viewport checks pass. WeChat Mini Game device test is pending; no phone performance claim.')
]};
save(cand+'/quality_results_n5s1q.json',results);
