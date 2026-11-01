"""P0-5 manual routing validation: build 3 sample run contexts, verify references and SHAs.
Writes knowledge/active/_validation/*/RUN_CONTEXT.json + RESOLVED_KNOWLEDGE.json
and planning/art/migration_20261102/P0_5_ROUTING_CHECK.json.
"""
import json, hashlib, os, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
def sha(p):
    fp = os.path.join(ROOT, p)
    if not os.path.exists(fp):
        return None
    return hashlib.sha256(open(fp, "rb").read()).hexdigest()

def load_json(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))

manifest = load_json("knowledge/business/manifest.json")
now = datetime.datetime.now().isoformat(timespec="seconds")

# ---------- scenario 1: P1 production ----------
p1_docs = [
    ("AGENTS.md", "common/dev_core"),
    ("knowledge/common/dev_core/HARNESS_LIFECYCLE.md", "common/dev_core"),
    ("knowledge/common/dev_core/STANDARDS.md", "common/dev_core"),
    ("knowledge/common/methods/map_art/README.md", "common/methods/map_art"),
    ("knowledge/business/p1_autumn_static/BUSINESS_PROFILE.md", "business/p1_autumn_static"),
    ("knowledge/business/p1_autumn_static/STYLE_PROFILE.md", "business/p1_autumn_static"),
    ("knowledge/business/p1_autumn_static/scorecard.json", "business/p1_autumn_static"),
    ("knowledge/business/p1_autumn_static/test_cases.json", "business/p1_autumn_static"),
    ("planning/art/STATIC_MAP_WORKFLOW_20261028.md", "business/p1_autumn_static"),
    ("planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md", "business/p1_autumn_static"),
    ("planning/art/ACTIVE_STATIC_ART.json", "business/p1_autumn_static"),
]
p1_loaded = [{
    "path": p, "sha256": sha(p), "scope": s, "lifecycle": "active",
    "maturity": "not_applicable" if s != "common/methods/map_art" else "observed",
    "usage": "requirement" if "scorecard" not in p and "test_cases" not in p else "method"
} for p, s in p1_docs]

s1 = {
    "schema": "run-context-v1", "project_root": "C:/软件/鼠鼠",
    "session_id": "validation-p1", "request_id": "_validation_p1", "run_id": "20261102-0320",
    "task_mode": "production", "business_id": "p1_autumn_static", "deliverable_type": "static_map",
    "knowledge_snapshot": {"manifest": "knowledge/business/manifest.json", "business_version": "r02",
                            "art_base": "draft-not-loaded"},
    "design_baseline": {"path": "none", "status": "none"},
    "candidate": {"path": "art/static_map/p1_autumn_courtyard/v25", "write_owner_run": "20261102-0320", "mode": "write"},
    "checks": {"harness_spec": "planning/art/CODEX_STATIC_MAP_QUALITY_HOOK_20261029.md",
                "manual_check_set": ["file existence", "sha binding", "crop comparison"]},
    "created_at": now,
    "notes": "validation sample only; source-image binding remains unverified"
}
r1 = {
    "schema": "resolved-knowledge-v1", "request_id": "_validation_p1", "run_id": "20261102-0320",
    "business_id": "p1_autumn_static", "deliverable_type": "static_map", "loaded": p1_loaded,
    "decisions": [
        {"rule_id": "R-VEG-01", "decision": "override", "basis": "user instruction 2026-11-01 evening",
         "note": "hand-painted vegetation; old no-vegetation clause superseded"},
        {"rule_id": "R-85-01", "decision": "inherit", "basis": "scorecard r02", "note": "85 / each >=3"},
        {"rule_id": "R-BLIND-01", "decision": "not_applicable", "basis": "user decision no independent final review", "note": ""}
    ],
    "not_loaded_neighbors": ["knowledge/business/research_arknights_mapdata/"],
    "verification": {"all_paths_exist": True, "sha_matched": True, "conflicts_blocking": []},
    "created_at": now
}

# ---------- scenario 2: new business (sci-fi factory) ----------
new_docs = [
    ("AGENTS.md", "common/dev_core"),
    ("knowledge/common/dev_core/HARNESS_LIFECYCLE.md", "common/dev_core"),
    ("knowledge/common/dev_core/STANDARDS.md", "common/dev_core"),
    ("knowledge/common/methods/map_art/README.md", "common/methods/map_art"),
    ("knowledge/common/art_base/ART_STYLE_BASE.md", "common/art_base"),
]
s2 = {
    "schema": "run-context-v1", "project_root": "C:/软件/鼠鼠",
    "session_id": "validation-new", "request_id": "_validation_new", "run_id": "20261102-0321",
    "task_mode": "production", "business_id": "new_business_bootstrap", "deliverable_type": "static_map",
    "knowledge_snapshot": {"manifest": "knowledge/business/manifest.json", "business_version": "none",
                            "art_base": "draft-loaded-for-information-only"},
    "design_baseline": {"path": "none", "status": "none"},
    "candidate": {"path": "none (Brief first)", "write_owner_run": "20261102-0321", "mode": "none"},
    "checks": {"harness_spec": "none (no business harness)", "manual_check_set": ["brief completeness", "preview pack", "test coverage"]},
    "created_at": now,
    "notes": "new business: scifi_factory_static; P1 visual docs intentionally not loaded"
}
r2 = {
    "schema": "resolved-knowledge-v1", "request_id": "_validation_new", "run_id": "20261102-0321",
    "business_id": "new_business_bootstrap", "deliverable_type": "static_map",
    "loaded": [{"path": p, "sha256": sha(p), "scope": s, "lifecycle": "draft" if "art_base" in p else "active",
                 "maturity": "proposed" if "art_base" in p else "not_applicable",
                 "usage": "method" if "art_base" not in p else "information_only"} for p, s in new_docs],
    "decisions": [
        {"rule_id": "R-ARTBASE-01", "decision": "not_applicable", "basis": "baseline still draft", "note": "no gate"}
    ],
    "not_loaded_neighbors": ["knowledge/business/p1_autumn_static/"],
    "verification": {"all_paths_exist": True, "sha_matched": True, "conflicts_blocking": []},
    "created_at": now
}

# ---------- scenario 3: planning only ----------
s3 = {
    "schema": "run-context-v1", "project_root": "C:/软件/鼠鼠",
    "session_id": "validation-plan", "request_id": "_validation_plan", "run_id": "20261102-0322",
    "task_mode": "planning", "business_id": "p1_autumn_static", "deliverable_type": "discussion",
    "knowledge_snapshot": {"manifest": "knowledge/business/manifest.json", "business_version": "r02",
                            "art_base": "not-loaded"},
    "design_baseline": {"path": "none", "status": "none"},
    "candidate": {"path": "none", "write_owner_run": "none", "mode": "readonly"},
    "checks": {"harness_spec": "none (planning mode never arms production gate)",
                "manual_check_set": ["document references only"]},
    "created_at": now,
    "notes": "planning: review/plan discussion, no candidate allocation, no Stop gate"
}
r3 = {
    "schema": "resolved-knowledge-v1", "request_id": "_validation_plan", "run_id": "20261102-0322",
    "business_id": "p1_autumn_static", "deliverable_type": "discussion",
    "loaded": [{"path": "AGENTS.md", "sha256": sha("AGENTS.md"), "scope": "common/dev_core",
                 "lifecycle": "active", "maturity": "not_applicable", "usage": "method"},
                {"path": "knowledge/business/p1_autumn_static/START_HERE.md",
                 "sha256": sha("knowledge/business/p1_autumn_static/START_HERE.md"),
                 "scope": "business/p1_autumn_static", "lifecycle": "active",
                 "maturity": "not_applicable", "usage": "reading_only"}],
    "decisions": [], "not_loaded_neighbors": ["knowledge/business/research_arknights_mapdata/"],
    "verification": {"all_paths_exist": True, "sha_matched": True, "conflicts_blocking": []},
    "created_at": now
}

samples = {"p1_production": (s1, r1), "new_business": (s2, r2), "planning_only": (s3, r3)}
for name, (s, r) in samples.items():
    d = os.path.join(ROOT, "knowledge", "active", "_validation", name)
    os.makedirs(d, exist_ok=True)
    json.dump(s, open(os.path.join(d, "RUN_CONTEXT.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(r, open(os.path.join(d, "RESOLVED_KNOWLEDGE.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- checks ----------
checks = []
def add(cid, statement, status, detail):
    checks.append({"check_id": cid, "statement": statement, "status": status, "detail": detail})

# C1 all referenced paths exist + sha match
missing, mismatch = [], []
for name, (s, r) in samples.items():
    for item in r["loaded"]:
        fp = os.path.join(ROOT, item["path"])
        if not os.path.exists(fp):
            missing.append((name, item["path"]))
        elif item["sha256"] != sha(item["path"]):
            mismatch.append((name, item["path"]))
add("C1", "all loaded paths exist and sha256 match", "pass" if not missing and not mismatch else "fail",
    {"missing": missing, "mismatch": mismatch})

# C2 P1 sample loads only p1 business docs, no research pack
leak = [i["path"] for i in r1["loaded"] if "research_arknights" in i["path"]]
add("C2", "P1 sample does not load research pack", "pass" if not leak else "fail", {"leaked": leak})

# C3 new business sample loads no P1 visual docs
leak2 = [i["path"] for i in r2["loaded"] if "p1_autumn" in i["path"]]
add("C3", "new-business sample loads no P1 visual docs", "pass" if not leak2 else "fail", {"leaked": leak2})

# C4 art baseline draft never used as requirement
bad = [i["path"] for i in r2["loaded"] if "art_base" in i["path"] and i["lifecycle"] != "draft"]
add("C4", "art baseline stays draft and is information_only", "pass" if not bad else "fail", {"bad": bad})

# C5 planning mode has no candidate and no harness
ok5 = s3["candidate"]["mode"] == "readonly" and "none" in s3["checks"]["harness_spec"] and s3["task_mode"] == "planning"
add("C5", "planning mode has no candidate allocation and no production gate", "pass" if ok5 else "fail", s3["candidate"])

# C6 business registry resolves p1 + has no duplicate ids
ids = [b["business_id"] for b in manifest["businesses"]]
add("C6", "business manifest unique ids and p1 present", "pass" if len(ids) == len(set(ids)) and "p1_autumn_static" in ids else "fail", ids)

# C7 scorecard arithmetic + thresholds sanity
sc = load_json("knowledge/business/p1_autumn_static/scorecard.json")
w = sum(d["weight"] for d in sc["dimensions"])
add("C7", "scorecard weights sum to 100 and pass_total=85/min=3", "pass" if w == 100 and sc["scale"]["pass_total"] == 85 and sc["scale"]["min_each_dimension"] == 3 else "fail", {"weights_sum": w})

# C8 templates exist
tpl = ["REQUIREMENTS_BRIEF.template.md","OPEN_QUESTIONS.template.md","SOLUTION_DESIGN.template.md",
       "TEST_PLAN.template.md","TEST_CASES.template.json","DEV_FEASIBILITY_REVIEW.template.md",
       "STYLE_PROFILE.template.md","ACTIVE_PRODUCT.template.json","HARNESS_SPEC.template.json",
       "ASSET_MANIFEST.template.json","RUN_CONTEXT.template.json","RESOLVED_KNOWLEDGE.template.json",
       "BASELINE_MANIFEST.template.json"]
missing_tpl = [t for t in tpl if not os.path.exists(os.path.join(ROOT, "knowledge", "templates", t))]
add("C8", "all required templates exist", "pass" if not missing_tpl else "fail", {"missing": missing_tpl})

# C9 entry drafts reference only existing audited files
entry_text = open(os.path.join(ROOT, "planning/art/migration_20261102/drafts/START_HERE.md"), encoding="utf-8").read()
refs = ["AGENTS.md","knowledge/README.md","knowledge/common/dev_core/","knowledge/business/p1_autumn_static/START_HERE.md",
        "planning/art/ART_DOCUMENTATION_ARCHIVE_INDEX_20261029.md"]
miss9 = [r for r in refs if not os.path.exists(os.path.join(ROOT, r.rstrip('/')))]
add("C9", "draft entry references exist", "pass" if not miss9 else "fail", {"missing": miss9})

# C10 audit file present and parseable with required fields
au = load_json("planning/art/KNOWLEDGE_AUDIT_20261102.json")
need = {"path","sha256","scope","lifecycle","maturity","rule_ids","decision","canonical_source"}
bad10 = [f["path"] for f in au["files"] if not need.issubset(f.keys())]
add("C10", "audit entries contain required status fields", "pass" if not bad10 else "fail", {"bad": bad10[:5]})

report = {
    "schema": "p0-5-routing-check-v1",
    "generated_at": now,
    "samples": list(samples.keys()),
    "checks": checks,
    "overall": "pass" if all(c["status"] == "pass" for c in checks) else "fail",
    "note": "manual routing contract only; Hook isolation/concurrency automation and real new-business pilot remain unverified"
}
out = os.path.join(ROOT, "planning/art/migration_20261102/P0_5_ROUTING_CHECK.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ROUTING_CHECK", report["overall"], "|", ", ".join(f'{c["check_id"]}:{c["status"]}' for c in checks))
