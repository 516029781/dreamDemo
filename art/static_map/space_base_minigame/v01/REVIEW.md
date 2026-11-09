# REVIEW — space_base_minigame v01

- request/run: `20261102-space-base-map` / `20261102-1314`
- source: `C:\软件\鼠鼠\art\static_map\space_base_minigame\v01\scene.blend` (SHA `a226ca39f3fa13b640207d65d96d410fb000210cae881edb43a7a62a10132a07`)
- master: `C:\软件\鼠鼠\art\static_map\space_base_minigame\v01\renders\space_base_v01_master.png` 3840x5120 (container `48df97d426cc4479f58807965d0bb1bcfb3fdc115e8c5564bc0b6ffc1b2d79e1`, content `e40212cf8ec8d5e893839c83c167616ffb33dffa0a6be0105723425da0046702`)
- shipped: `C:\软件\鼠鼠\art\static_map\space_base_minigame\v01\renders\space_base_v01.jpg` 1920x2560 (container `785505f66f3a144134a4c58b00b16290bc44b72983e0fe81f7401c07808effff`, content `a5f654980088048c0849a0abd7056c85879fa573e9a89993ef6a3453b8ec5271`, 448184 bytes)
- spec: `planning/art/SPACE_BASE_MASTER_SPEC_20261102.md` v1.3
- camera: C1/C2 in `CONFLICTS_AND_DECISIONS.md`; final image is a horizontal mirror of the physical north-looking camera to satisfy `px=x*8` and south-up.
- reproduction: pass (RMS=0.0/255, tol=2.0)

## Required checks

| ID | Result | Evidence |
|---|---|---|
| G1 | pass | `G1/camera_projection.json` (max error <1 px) |
| G2 | pass | `G2/readability.md`, `renders/checks/01_core.png` |
| G3 | pass | `G3/ceo_access.md`, `renders/checks/04_ceo.png` |
| G4 | pass | `G4/exit.md`, `renders/checks/03_south_exit.png` |
| G5 | pass | `G5/occlusion.md`, `renders/checks/02_workshop.png` |
| G6 | pass | `G6/geom_check.json` |
| G7 | pass | `G7/viewport_math.json` |
| G8 | pass | `G8/seam.md`, `renders/checks/03_south_exit.png` |
| W1 | pass | `W1/file_check.json` |
| W2 | pass | `W2/package.json` |
| S1 | pass | `S1/value.md` (diagnostic 49.06%) |
| S2 | pass | `S2/green.md` (HAAVK only; C4) |
| S3 | pass | `S3/orange.md` (diagnostic 0.06%) |
| S4 | pass | `S4/hue.md` |
| S5 | pass | `S5/corners.md` |
| S6 | pass | `S6/joints.md` |
| S7 | pass | `S7/shadow.md` |

External: A1, W3, W4 — not_run, not pass.

## Producer self-review / anti-overclaim

- S1 counterexample: the central equipment body and field are dark; the 45% claim is about the lit map surfaces, not the whole rectangle. The measured full-image diagnostic is 49.06%.
- S2 counterexample: garden vegetation is green and could be counted by a naive hue mask; C4 explicitly limits S2 to HAAVK corporate green. If the user wants all green ≤8%, the garden design itself must change.
- S4 counterexample: H2 pool blue could be confused with H3 blue; H2 also has a teal band/yellow rail and H3 has a blue pit rim/wall bands; the signatures remain distinct at 1920.
- S7 counterexample: world fill lowers shadow contrast; the sun remains 55° elevation and shadows are hard-edged at 0.6–0.8; CEO warm lights are the only warm interior.
- Scope: this is a stylized 2.5D acceptance map. Non-landmark L2/L3 props were merged/omitted; see the omission list below.

## Omitted / simplified (per execution plan)

- No character/UI/Cocos/WeChat runtime.
- H2/H3/H4 small props not in the 7 recognition points are simplified; no external textures; no roof.
- A1/W3/W4 runtime checks external.

## Status

`target_met` for G1-G8 + W1/W2 + S1-S7 (17/17). External A1/W3/W4 reported separately.
