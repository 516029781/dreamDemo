# Depth method — characters/NPC/FX in world depth (R01, K02/K03)

## Pipeline

Player (CHAR001/CHAR002, Spine 1015_aglna2) is NOT a screen-space sprite. It is rendered by a
second offscreen pass into a `RenderTexture` and composited as a transparent world quad that
shares scene depth with MAP001:

1. `CharRTCanvas` node parked at x=20000 (outside the main view), with a `Camera`
   (orthoHeight 512, clearFlag SOLID_COLOR with alpha 0, priority −1, `targetTexture` = RT 1024×1024).
2. `PlayerSpineRT` (real Spine component, locked source 1015_aglna2) renders into that RT each frame.
3. `PlayerWorldQuad` — a custom 4-vertex mesh (1.75 m × 1.75 m, bottom-anchored at the player's
   ground position) with `builtin-unlit` technique 1, `mainTexture` = RT, shadow casting OFF —
   is positioned at `playerPos` and rotated to the main camera rotation every frame
   (`updateCharacterTransform`), so it is camera-aligned but still depth-sorted in the 3D scene.
4. NPC (CHAR003) and world FX (FX002 pickup, FX003 board cards) use the same quad builder
   (`makeScreenQuad`) with regular `Texture2D` at fixed world positions
   (NPC (3,0,−5), FX002 (−7,0.2,−3), FX003 (0,0.9,6.9)), rotated to the camera every frame
   in `updateWorldBillboards`.

## UV / orientation handling

- RenderTexture sampling is bottom-up: quad tilingOffset `(1,1,0,0)` renders upright; when the
  character faces left the X axis flips via `(−1,1,1,0)`.
- Regular Texture2D uploads are top-down: NPC/FX quads need a V-flip `(1,−1,0,1)`
  (verified empirically against the source pose, see `_npc_vflip_crop.png` vs the slice asset).
- Screen anchor metric: `projectToCanvas` analytic projection of feet/head world points gives
  `px` (character height on canvas). At spawn: 97.8 px, within the required 86–130 px band.

## Occlusion proof

`occlusion_front.png` / `occlusion_behind.png` — same camera offset, player at (0,0,−5.2) (visible,
in front of the tree) vs (0,0,2.0) (fully hidden behind tree canopy). The quad is depth-tested
against MAP001 geometry, so characters walk behind world objects correctly.

## Verification artifacts (this folder)

- `occlusion_front.png`, `occlusion_behind.png`, `occlusion_results.json`
- `anchor_results.json` (px = 97.84, range 86–130, pass)
- full-scene check `../_final_scene.png`, `../_final_npc_crop.png` (NPC orientation matches source)
