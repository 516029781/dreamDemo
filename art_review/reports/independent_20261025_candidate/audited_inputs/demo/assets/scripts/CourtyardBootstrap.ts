import {
    _decorator, Component, Node, Camera, DirectionalLight, Color, Vec3, Vec4, Vec2,
    MeshRenderer, Material, primitives, utils, resources, Prefab, instantiate, Sprite,
    SpriteFrame, Label, UITransform, Canvas, Layers, view, ResolutionPolicy, Graphics,
    input, Input, KeyCode, EventTouch, Texture2D, ImageAsset, director,
    sp, Font, UIOpacity, profiler, RenderTexture,
} from 'cc';

const { ccclass } = _decorator;

const DESIGN_W = 1280;
const DESIGN_H = 720;
const PAVING_TOP = 0.0;
const PLAYER_HEIGHT_M = 1.4;
const MAP_BOUNDS_X = 13.0;
const MAP_BOUNDS_Z = 9.2;

const C = {
    paper: new Color(243, 240, 230, 255),
    paperHigh: new Color(250, 248, 241, 255),
    ink: new Color(46, 50, 52, 255),
    inkBody: new Color(58, 62, 63, 255),
    muted: new Color(102, 106, 102, 255),
    faint: new Color(140, 143, 137, 255),
    mint: new Color(159, 216, 200, 255),
    mintDeep: new Color(79, 138, 121, 255),
    mintWash: new Color(159, 216, 200, 76),
    gold: new Color(216, 170, 88, 255),
    goldDeep: new Color(138, 100, 37, 255),
    white: new Color(255, 255, 255, 255),
};

function hexToColor(hex: string, alpha = 255): Color {
    const h = hex.replace('#', '');
    return new Color(parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16), alpha);
}

/**
 * Courtyard scene_demo bootstrap.
 *
 * Everything below builds real Cocos nodes, MeshRenderers, materials and 2D UI.
 * The 3D environment is the Blender-authored MAP001 courtyard GLB (129 layout
 * instances, 74 merged mesh/text objects) plus the Spine player and 2D UI.
 */
@ccclass('CourtyardBootstrap')
export class CourtyardBootstrap extends Component {
    private mainCamera: Camera = null!;
    private canvasNode: Node = null!;
    private canvasUT: UITransform = null!;
    private characterLayer: Node = null!;
    private hudRoot: Node = null!;
    private studioRoot: Node = null!;
    private studioActive = false;
    private charRT: RenderTexture | null = null;
    private charQuadNode: Node | null = null;
    private charQuadMR: MeshRenderer | null = null;
    private charRTCanvas: Node | null = null;
    private charRTCamera: Camera | null = null;
    private npcQuadNode: Node | null = null;
    private npcQuadMR: MeshRenderer | null = null;
    private npcNode: Node | null = null;
    private npcTexture: Texture2D | null = null;
    private fxTextures: Record<string, Texture2D> = {};
    private fxPickupNode: Node | null = null;
    private fxBoardNode: Node | null = null;
    private cardNodes: Node[] = [];
    private boardState = 'full';
    private presentationScale = 1.0;
    private viewerId = '';
    private clock = 0;
    private inputLocked = false;
    private paused = false;
    private cameraMode: 'game' | 'inspect' = 'game';
    private scrim: Node = null!;
    private dialogueRoot: Node = null!;

    private playerAnchor: Node = null!;
    private spineNode: Node | null = null;
    private spine: sp.Skeleton | null = null;
    private shadowNode: Node | null = null;
    private paperFrame: SpriteFrame | null = null;
    private shadowMaterial: Material | null = null;

    private questTitle: Label = null!;
    private questSub: Label = null!;
    private questBadge: Label = null!;
    private speakerLabel: Label = null!;
    private bodyLabel: Label = null!;
    private pageLabel: Label = null!;
    private hintLabel: Label = null!;
    private nextLabel: Label = null!;
    private portraitSprite: Sprite = null!;

    private labelsSans: Label[] = [];
    private labelsSerif: Label[] = [];
    private iconTargets = new Map<string, Sprite[]>();
    private actionRoot: Node = null!;
    private joystickRoot: Node = null!;
    private joystickKnob: Node = null!;
    private joystickBase: Node | null = null;
    private actionPaper: Sprite | null = null;
    private actionLabel: Label | null = null;
    private actionSub: Label | null = null;
    private actionIconSprite: Sprite | null = null;
    private dialogueNextSprite: Sprite | null = null;
    private dialogueNextLabel: Label | null = null;
    private dialogueActionNode: Node = null!;

    private keys = new Set<number>();
    private joy = new Vec2(0, 0);
    private playerPos = new Vec3(0, PAVING_TOP, -5.2);
    private facing = 1;
    private moving = false;
    private manualMoving = false;
    private speed = 3.0;
    private dialoguePage = 1;
    private dialogueVisible = false;
    private accepted = false;
    private uiVisible = true;
    private currentAnim = '';

    private loadErrors: string[] = [];
    private pendingLoads = 0;
    private assetsReady = false;

    onLoad(): void {
        profiler.hideStats();
        view.setDesignResolutionSize(DESIGN_W, DESIGN_H, ResolutionPolicy.SHOW_ALL);
        this.setupCamera();
        this.setupLights();
        this.setupWorldAnchors();
        this.setupUI();
        this.setupInput();
        this.loadAssets();
        console.log('[COURTYARD] onLoad complete; loading native assets');
    }

    // ------------------------------------------------------------------ scene

    private setupCamera(): void {
        const scene = director.getScene()!;
        const camNode = scene.getChildByName('Main Camera')!;
        camNode.setPosition(-2.5, 11.5, -14.6);
        camNode.lookAt(new Vec3(-2.5, 3.5, -3.7));
        const cam = camNode.getComponent(Camera)!;
        cam.fov = 35;
        cam.near = 0.1;
        cam.far = 120;
        cam.clearFlags = Camera.ClearFlag.SOLID_COLOR;
        cam.clearColor = hexToColor('#C9C4B6');
        cam.visibility = Layers.Enum.DEFAULT;
        this.mainCamera = cam;

        const globals = scene.globals;
        globals.skybox.enabled = false;
        globals.ambient.skyColor = new Vec4(0.57, 0.62, 0.68, 1);
        globals.ambient.skyIllum = 23000;
        globals.ambient.groundLightingColor = new Color(120, 110, 96, 255);
        globals.shadows.enabled = true;
        (globals.shadows as any).type = 0; // ShadowMap
        globals.shadows.shadowMapSize = 4096;
        globals.shadows.maxReceived = 4;

        console.log('[COURTYARD] camera ready mode=game fov=35 pos=(-2.5,11.5,-14.6)');
    }

    private setupLights(): void {
        const scene = director.getScene()!;
        const keyNode = scene.getChildByName('Main Light')!;
        keyNode.setRotationFromEuler(-50, -32, 0);
        const key = keyNode.getComponent(DirectionalLight)!;
        key.color = hexToColor('#FFD7A0');
        key.illuminance = 82000;
        key.shadowEnabled = true;
        (key as any).shadowPcf = 3; // SOFT_4X: contact shadows readable, not hard-edged
        (key as any).shadowBias = 0.0003;
        (key as any).shadowNormalBias = 0.35;
        (key as any).shadowDistance = 30;
        (key as any).shadowSaturation = 0.72;

        const fillNode = new Node('Fill Light');
        fillNode.parent = scene;
        fillNode.setRotationFromEuler(-28, 148, 0);
        const fill = fillNode.addComponent(DirectionalLight);
        fill.color = hexToColor('#A9C2D6');
        fill.illuminance = 28000;
        fill.shadowEnabled = false;
        console.log('[COURTYARD] lights ready key warm + cool fill');
    }

    private setupWorldAnchors(): void {
        this.playerAnchor = new Node('PlayerAnchor');
        this.playerAnchor.parent = this.node;
        this.playerAnchor.setPosition(this.playerPos);
    }

    private buildEnvironment(): void {
        const map = instantiate(this.prefabs['map']);
        map.name = 'MAP001_courtyard';
        map.parent = this.node;
        map.setPosition(0, 0, 0);
        const renderers = map.getComponentsInChildren(MeshRenderer);
        for (const mr of renderers) {
            const n = mr.node.name.toLowerCase();
            const flat = n.indexOf('ground') >= 0 || n.indexOf('paving') >= 0 || n.indexOf('skirt') >= 0;
            const lightCaster = n.indexOf('railing') >= 0 || n.indexOf('low_wall') >= 0 || n.indexOf('curb') >= 0 || n.indexOf('steps') >= 0 || n.indexOf('_text') >= 0;
            mr.receiveShadow = true;
            mr.shadowCastingMode = (flat || lightCaster) ? MeshRenderer.ShadowCastingMode.OFF : MeshRenderer.ShadowCastingMode.ON;
        }
        for (const key of ['A', 'B', 'C']) {
            const card = this.findNode(map, 'MAP001_message_board_card_' + key);
            if (card) this.cardNodes.push(card);
        }
        this.setBoardState('full');
        this.applyMaterialOverrides(map);
        console.log('[COURTYARD] full MAP001 instantiated renderers=' + renderers.length + ' cards=' + this.cardNodes.length);
    }

    // V02 material separation: procedural texture sources in
    // art/full/source/textures/ (tools/textures/make_procedural_textures.py)
    // + world-space box UVs baked in build_map001.py. Palette tints carry the
    // color; textures carry pattern; roughness/metallic separate families.
    private static readonly MAT_OVERRIDES: Record<string, { tex: string; color: string; rough: number; metal: number }> = {
        ENG_MAT_stone_base: { tex: 'textures/tex_stone_tiles/texture', color: '#B3AA99', rough: 0.90, metal: 0.0 },
        ENG_MAT_stone_light: { tex: 'textures/tex_stone_tiles/texture', color: '#CDC4B2', rough: 0.86, metal: 0.0 },
        ENG_MAT_stone_dark: { tex: 'textures/tex_stone_tiles/texture', color: '#837A6B', rough: 0.94, metal: 0.0 },
        ENG_MAT_mortar: { tex: 'textures/tex_stone_tiles/texture', color: '#6F6759', rough: 0.96, metal: 0.0 },
        ENG_MAT_ground_soil: { tex: 'textures/tex_soil_noise/texture', color: '#3F362C', rough: 0.98, metal: 0.0 },
        ENG_MAT_soil: { tex: 'textures/tex_soil_noise/texture', color: '#3F362C', rough: 0.98, metal: 0.0 },
        ENG_MAT_wood_dark: { tex: 'textures/tex_wood_grain/texture', color: '#4E3E2E', rough: 0.72, metal: 0.0 },
        ENG_MAT_wood_old: { tex: 'textures/tex_wood_grain/texture', color: '#7A6249', rough: 0.66, metal: 0.0 },
        ENG_MAT_bench_wood: { tex: 'textures/tex_wood_grain/texture', color: '#6E5238', rough: 0.62, metal: 0.0 },
        ENG_MAT_bench_metal: { tex: 'textures/tex_metal_brushed/texture', color: '#3F3E3B', rough: 0.34, metal: 0.88 },
        ENG_MAT_metal_iron: { tex: 'textures/tex_metal_brushed/texture', color: '#3C3D40', rough: 0.36, metal: 0.90 },
        ENG_MAT_metal_brass: { tex: 'textures/tex_metal_brushed/texture', color: '#A9834B', rough: 0.35, metal: 0.85 },
        ENG_MAT_metal_rust: { tex: 'textures/tex_metal_brushed/texture', color: '#7A5540', rough: 0.85, metal: 0.30 },
    };

    private applyMaterialOverrides(map: Node): void {
        const renderers = map.getComponentsInChildren(MeshRenderer);
        const texPaths = Array.from(new Set(Object.values(CourtyardBootstrap.MAT_OVERRIDES).map(o => o.tex)));
        texPaths.push('textures/tex_bark/texture');
        const texMap: Record<string, Texture2D> = {};
        let pending = texPaths.length;
        for (const p of texPaths) {
            resources.load(p, Texture2D, (err: any, tex: Texture2D) => {
                if (err) console.warn('[MAT] texture load failed ' + p + ' ' + err);
                else texMap[p] = tex;
                pending -= 1;
                if (pending === 0) this.finishMaterialOverrides(renderers, texMap);
            });
        }
    }

    private finishMaterialOverrides(renderers: MeshRenderer[], texMap: Record<string, Texture2D>): void {
        const unknown = new Set<string>();
        let replaced = 0;
        for (const mr of renderers) {
            const anyMr = mr as any;
            const slotCount = anyMr.materials && anyMr.materials.length ? anyMr.materials.length : 1;
            for (let i = 0; i < slotCount; i++) {
                const src = mr.getMaterial(i);
                const name = src ? src.name : '';
                const isBark = mr.node.name.toLowerCase().indexOf('tree_bark') >= 0;
                const ov = isBark
                    ? { tex: 'textures/tex_bark/texture', color: '#4A3A2C', rough: 0.88, metal: 0.0 }
                    : CourtyardBootstrap.MAT_OVERRIDES[name];
                if (!ov) {
                    if (name) unknown.add(name);
                    continue;
                }
                const tex = texMap[ov.tex];
                if (!tex) continue;
                const m = new Material();
                m.initialize({ effectName: 'builtin-standard' });
                m.setProperty('mainTexture', tex);
                m.setProperty('mainColor', hexToColor(ov.color));
                m.setProperty('roughness', ov.rough);
                m.setProperty('metallic', ov.metal);
                mr.setMaterial(m, i);
                replaced += 1;
            }
        }
        console.log('[MAT] overrides applied replaced=' + replaced + ' unknown=[' + Array.from(unknown).join(',') + ']');
    }

    private findNode(root: Node, name: string): Node | null {
        if (root.name === name) return root;
        for (const child of root.children) {
            const found = this.findNode(child, name);
            if (found) return found;
        }
        return null;
    }

    private setBoardState(state: string): void {
        this.boardState = state;
        const visible = state === 'full' ? 3 : state === 'empty' || state === 'reset' ? 0 : state === 'A' ? 1 : state === 'B' ? 2 : 3;
        for (let i = 0; i < this.cardNodes.length; i++) {
            this.cardNodes[i].active = i < visible;
        }
        if (this.fxBoardNode) this.fxBoardNode.active = false;
        console.log('[COURTYARD] board=' + state + ' cards=' + visible);
    }

    private makePrimitive(name: string, geometry: any, mat: Material, pos: Vec3): Node {
        const node = new Node(name);
        node.parent = this.node;
        node.setPosition(pos);
        const mr = node.addComponent(MeshRenderer);
        mr.mesh = utils.MeshUtils.createMesh(geometry);
        mr.setMaterial(mat, 0);
        return node;
    }

    // ------------------------------------------------------------- assets/UI

    private prefabs: Record<string, Prefab> = {};
    private paperTexture: Texture2D | null = null;
    private portraitTextures: Record<string, Texture2D> = {};
    private iconTextures: Record<string, Texture2D> = {};
    private fontSans: Font | null = null;
    private fontSerif: Font | null = null;

    private loadAssets(): void {
        const load = (path: string, type: any, cb: (err: any, asset: any) => void) => {
            this.pendingLoads++;
            resources.load(path, type, (err: any, asset: any) => {
                if (err || !asset) {
                    const message = '[COURTYARD] load failed: ' + path + ' :: ' + (err ? err.message || err : 'null');
                    console.warn(message);
                    this.loadErrors.push(message);
                }
                cb(err, asset);
                this.pendingLoads--;
                this.maybeFinish();
            });
        };

        load('models/MAP001_courtyard/MAP001_courtyard', Prefab, (_e, p) => { this.prefabs['map'] = p; });
        load('ui/paper_panel_384/texture', Texture2D, (_e, t) => { this.paperTexture = t; });
        load('ui/portrait_npc_gardener/texture', Texture2D, (_e, t) => { this.portraitTextures['npc'] = t; });
        load('ui/portrait_player_1015/texture', Texture2D, (_e, t) => { this.portraitTextures['player'] = t; });
        load('fonts/NotoSansSC-VF', Font, (_e, f) => { this.fontSans = f; });
        load('fonts/NotoSerifSC-VF', Font, (_e, f) => { this.fontSerif = f; });
        for (const icon of [
            'icon_arrow', 'icon_check', 'icon_close', 'icon_continue', 'icon_copy', 'icon_info', 'icon_leaf',
            'icon_lock', 'icon_menu', 'icon_pickup', 'icon_pin', 'icon_place', 'icon_postcard', 'icon_restart',
            'icon_retry', 'icon_rotate', 'icon_sound_off', 'icon_sound_on', 'icon_sparkle', 'icon_talk', 'icon_view',
        ]) {
            load('ui/icons/' + icon + '/texture', Texture2D, (_e, t) => { this.iconTextures[icon] = t; });
        }
        load('ui/postcard_bench/texture', Texture2D, (_e, t) => { if (t) this.iconTextures['postcard_bench'] = t; });
        load('ui/postcard_flower/texture', Texture2D, (_e, t) => { if (t) this.iconTextures['postcard_flower'] = t; });
        load('ui/postcard_pergola/texture', Texture2D, (_e, t) => { if (t) this.iconTextures['postcard_pergola'] = t; });
        load('char/npc_gardener_slice/texture', Texture2D, (_e, t) => { this.npcTexture = t; });
        load('fx/FX002_pickup_feedback/texture', Texture2D, (_e, t) => { if (t) this.fxTextures['pickup'] = t; });
        load('fx/FX003_board_completion/texture', Texture2D, (_e, t) => { if (t) this.fxTextures['board'] = t; });
        load('char/1015_aglna2', sp.SkeletonData, (_e, data) => {
            if (data) this.buildCharacter(data);
        });

        // Fonts/portraits are applied after load; UI skeleton exists already.
        this.scheduleOnce(() => this.applyLoadedUiAssets(), 0.15);
    }

    private applyLoadedUiAssets(): void {
        if (this.paperTexture && !this.paperFrame) {
            const sf = new SpriteFrame();
            sf.texture = this.paperTexture;
            this.paperFrame = sf;
        }
        for (const [key, tex] of Object.entries(this.portraitTextures)) {
            const sprite = this.portraitSprites[key];
            if (sprite) {
                const sf = new SpriteFrame();
                sf.texture = tex;
                sprite.spriteFrame = sf;
                sprite.color = C.white;
            }
        }
        for (const [icon, sprites] of this.iconTargets) {
            const tex = this.iconTextures[icon];
            if (!tex) continue;
            const sf = new SpriteFrame();
            sf.texture = tex;
            for (const s of sprites) {
                s.spriteFrame = sf;
                s.color = C.ink;
            }
        }
        for (const label of this.labelsSans) {
            if (this.fontSans) { label.font = this.fontSans; label.useSystemFont = false; }
        }
        for (const label of this.labelsSerif) {
            if (this.fontSerif) { label.font = this.fontSerif; label.useSystemFont = false; }
        }
        // Apply the paper texture to every nine-slice panel that was built empty.
        for (const sprite of this.paperSprites) {
            const frame = this.makeSlicedFrame();
            if (frame) {
                sprite.spriteFrame = frame;
                sprite.type = Sprite.Type.SLICED;
            }
        }
        console.log('[COURTYARD] UI assets applied, font=' + (this.fontSans ? 'Noto Sans SC' : 'fallback'));
    }

    private paperSprites: Sprite[] = [];
    private portraitSprites: Record<string, Sprite> = {};

    private makeSlicedFrame(): SpriteFrame | null {
        if (!this.paperTexture) return null;
        const sf = new SpriteFrame();
        sf.texture = this.paperTexture;
        // texture is a 3x export of the 128 design; slice margin is 32 design px = 96 tex px
        sf.insetLeft = 96;
        sf.insetRight = 96;
        sf.insetTop = 96;
        sf.insetBottom = 96;
        return sf;
    }

    private maybeFinish(): void {
        if (this.pendingLoads > 0 || this.assetsReady) return;
        if (!this.prefabs['map'] || !this.spine) {
            if (this.loadErrors.length > 0) {
                console.error('[COURTYARD] required assets missing: ' + this.loadErrors.join(' | '));
            }
            return;
        }
        this.assetsReady = true;
        this.buildEnvironment();
        this.buildContactShadow();
        this.buildNpcAndFx();
        this.applyLoadedUiAssets();
        this.updateCharacterTransform();
        this.scheduleOnce(() => {
            (globalThis as any).__COURTYARD_READY__ = true;
            console.log('[COURTYARD] READY spine=' + (this.spine ? 'yes' : 'no') + ' anims=Relax,Move,Interact');
        }, 0.6);
    }

    // --------------------------------------------------------------- character

    private buildCharacter(data: sp.SkeletonData): void {
        const rt = new RenderTexture();
        rt.reset({ width: 1024, height: 1024 });
        this.charRT = rt;

        const canvasNode = new Node('CharRTCanvas');
        canvasNode.layer = Layers.Enum.UI_2D;
        canvasNode.parent = director.getScene()!;
        canvasNode.setPosition(20000, 0, 0);
        const cut = canvasNode.addComponent(UITransform);
        cut.setContentSize(1024, 1024);
        const canvas = canvasNode.addComponent(Canvas);
        const camNode = new Node('CharRTCamera');
        camNode.layer = Layers.Enum.UI_2D;
        camNode.parent = canvasNode;
        camNode.setPosition(0, 0, 1000);
        const cam = camNode.addComponent(Camera);
        cam.projection = Camera.ProjectionType.ORTHO;
        cam.orthoHeight = 512;
        cam.near = 0.1;
        cam.far = 2000;
        cam.clearFlags = Camera.ClearFlag.SOLID_COLOR;
        cam.clearColor = new Color(0, 0, 0, 0);
        cam.visibility = Layers.Enum.UI_2D;
        cam.priority = -1;
        cam.targetTexture = rt;
        canvas.cameraComponent = cam;
        this.charRTCanvas = canvasNode;
        this.charRTCamera = cam;

        const node = new Node('PlayerSpineRT');
        node.layer = Layers.Enum.UI_2D;
        node.parent = canvasNode;
        node.setPosition(0, -500, 0);
        const ut = node.addComponent(UITransform);
        ut.setAnchorPoint(0.5, 0);
        ut.setContentSize(1024, 1024);
        const skel = node.addComponent(sp.Skeleton);
        skel.skeletonData = data;
        skel.defaultSkin = 'default';
        skel.premultipliedAlpha = false;
        skel.setAnimation(0, 'Relax', true);
        node.setScale(2.0, 2.0, 1);
        this.spineNode = node;
        this.spine = skel;
        this.currentAnim = 'Relax';

        const quad = this.makeScreenQuad('PlayerWorldQuad', 1.75, 1.75, rt, new Vec4(1, 1, 0, 0));
        const mr = quad.getComponent(MeshRenderer)!;
        this.charQuadNode = quad;
        this.charQuadMR = mr;
        console.log('[COURTYARD] spine loaded into RenderTexture 1024x1024 + world depth quad');
        this.updateCharacterTransform();
    }

    private updateCharacterTransform(): void {
        if (!this.charQuadNode || !this.spine) return;
        const q = this.charQuadNode;
        q.setPosition(this.playerPos.x, this.playerPos.y, this.playerPos.z);
        q.setRotation(this.mainCamera.node.rotation);
        q.setScale(1, 1, 1);
        const mat = this.charQuadMR ? this.charQuadMR.getMaterial(0) : null;
        if (mat) mat.setProperty('tilingOffset', this.facing < 0 ? new Vec4(-1, 1, 1, 0) : new Vec4(1, 1, 0, 0));
        const feet = this.projectToCanvas(new Vec3(this.playerPos.x, this.playerPos.y, this.playerPos.z));
        const head = this.projectToCanvas(new Vec3(this.playerPos.x, this.playerPos.y + 1.75, this.playerPos.z));
        const px = Math.max(24, head.y - feet.y);
        (globalThis as any).__COURTYARD_METRICS__ = {
            px, feet: [feet.x, feet.y], head: [head.x, head.y], depth: feet.depth,
            player: [this.playerPos.x, this.playerPos.y, this.playerPos.z],
            canvas: [this.canvasUT.width, this.canvasUT.height],
            view: [view.getVisibleSize().width, view.getVisibleSize().height],
            method: 'RenderTexture->world transparent quad',
        };
    }

    /** Projects a world point into Canvas coordinates (origin at screen centre). */
    private projectToCanvas(world: Vec3): { x: number; y: number; depth: number } {
        const eye = this.mainCamera.node.worldPosition;
        const f = this.mainCamera.node.forward;
        const dx = world.x - eye.x, dy = world.y - eye.y, dz = world.z - eye.z;
        const depth = dx * f.x + dy * f.y + dz * f.z;
        const rx = f.z, rz = -f.x;
        const rl = Math.hypot(rx, rz) || 1;
        const ux = f.y * (rz / rl) - f.z * 0;
        const uy = f.z * (rx / rl) - f.x * (rz / rl);
        const uz = f.x * 0 - f.y * (rx / rl);
        const tanV = Math.tan((this.mainCamera.fov * Math.PI / 180) / 2);
        const aspect = DESIGN_W / DESIGN_H;
        const ndcX = (dx * (rx / rl) + dz * (rz / rl)) / (depth * tanV * aspect);
        const ndcY = (dx * ux + dy * uy + dz * uz) / (depth * tanV);
        return { x: ndcX * DESIGN_W / 2, y: ndcY * DESIGN_H / 2, depth };
    }

    private spineNativeHeight(): number {
        const sk: any = this.spine ? (this.spine as any)._skeleton : null;
        if (!sk || !sk.bones || sk.bones.length === 0) return 0;
        try {
            sk.updateWorldTransform();
            let minY = Number.POSITIVE_INFINITY;
            let maxY = Number.NEGATIVE_INFINITY;
            for (const b of sk.bones) {
                if (typeof b.worldY === 'number') {
                    if (b.worldY < minY) minY = b.worldY;
                    if (b.worldY > maxY) maxY = b.worldY;
                }
            }
            const h = maxY - minY;
            return (isFinite(h) && h > 10) ? h : 0;
        } catch (e) {
            return 0;
        }
    }

    private updateAnimation(): void {
        if (!this.spine) return;
        const want = this.moving ? 'Move' : 'Relax';
        if (want !== this.currentAnim) {
            this.spine.setAnimation(0, want, true);
            this.currentAnim = want;
        }
    }

    private buildContactShadow(): void {
        const size = 128;
        const data = new Uint8Array(size * size * 4);
        for (let y = 0; y < size; y++) {
            for (let x = 0; x < size; x++) {
                const nx = (x + 0.5) / size * 2 - 1;
                const ny = (y + 0.5) / size * 2 - 1;
                const d = Math.sqrt(nx * nx + ny * ny);
                const a = Math.max(0, 1 - d);
                const alpha = Math.round(255 * Math.pow(a, 1.6) * 0.62);
                const i = (y * size + x) * 4;
                data[i] = 0; data[i + 1] = 0; data[i + 2] = 0; data[i + 3] = alpha;
            }
        }
        const image = new ImageAsset({
            _data: data, _compressed: false, width: size, height: size,
        } as any);
        const texture = new Texture2D();
        texture.image = image;
        texture.setFilters(Texture2D.Filter.LINEAR, Texture2D.Filter.LINEAR);

        const mat = new Material();
        mat.initialize({ effectName: 'builtin-unlit', technique: 1, defines: { USE_TEXTURE: true } });
        mat.setProperty('mainColor', C.white);
        mat.setProperty('mainTexture', texture);
        this.shadowMaterial = mat;

        const node = this.makePrimitive('ContactShadow', primitives.plane({ width: 1.45, length: 1.0 }), mat, new Vec3(this.playerPos.x, PAVING_TOP + 0.006, this.playerPos.z));
        const mr = node.getComponent(MeshRenderer)!;
        mr.shadowCastingMode = MeshRenderer.ShadowCastingMode.OFF;
        mr.receiveShadow = false;
        this.shadowNode = node;
        console.log('[COURTYARD] contact shadow generated (runtime radial texture, unlit alpha)');
    }

    private buildNpcAndFx(): void {
        // regular Texture2D quads need V-flip; the RT-based player quad samples bottom-up already
        if (this.npcTexture) {
            const quad = this.makeScreenQuad('NpcWorldQuad', 1.55 * (411 / 625), 1.55, this.npcTexture, new Vec4(1, -1, 0, 1));
            quad.setPosition(3, 0, -5);
            quad.setRotation(this.mainCamera.node.rotation);
            this.npcNode = quad;
            this.npcQuadNode = quad;
            this.npcQuadMR = quad.getComponent(MeshRenderer);
            quad.active = true;
        }
        if (this.fxTextures['pickup']) {
            this.fxPickupNode = this.makeScreenQuad('FX002_pickup', 1.4, 1.4, this.fxTextures['pickup'], new Vec4(1, -1, 0, 1));
            this.fxPickupNode.setPosition(-7, 0.2, -3);
            this.fxPickupNode.active = false;
        }
        if (this.fxTextures['board']) {
            this.fxBoardNode = this.makeScreenQuad('FX003_board', 1.9, 1.9, this.fxTextures['board'], new Vec4(1, -1, 0, 1));
            this.fxBoardNode.setPosition(0, 0.9, 6.9);
            this.fxBoardNode.active = false;
        }
        console.log('[COURTYARD] NPC + FX world quads ready npc=' + !!this.npcNode + ' fx=' + !!this.fxPickupNode + '/' + !!this.fxBoardNode);
    }

    private buildNpcStandee(texture: Texture2D): Node {
        const node = this.uiNode('NpcStandee', this.characterLayer, 0, 0, 380, 740);
        const ut = node.getComponent(UITransform)!;
        ut.setAnchorPoint(0.5, 0);
        const groundNode = this.uiNode('NpcGroundShadow', node, 0, 10, 240, 40);
        const ground = groundNode.addComponent(Graphics);
        ground.fillColor = new Color(38, 36, 31, 55);
        ground.ellipse(0, 0, 120, 18);
        ground.fill();
        const post = node.addComponent(Graphics);
        post.fillColor = new Color(92, 70, 50, 255);
        post.roundRect(-14, 0, 28, 300, 6);
        post.fill();
        post.fillColor = new Color(120, 93, 66, 255);
        post.roundRect(-44, 282, 88, 16, 6);
        post.fill();

        const frame = this.uiNode('NpcFrame', node, 0, 305, 350, 510);
        const fs = frame.addComponent(Sprite);
        fs.sizeMode = Sprite.SizeMode.CUSTOM;
        fs.type = Sprite.Type.SLICED;
        fs.color = new Color(255, 255, 255, 252);
        const sf = this.makeSlicedFrame();
        if (sf) fs.spriteFrame = sf;

        const portraitNode = this.uiNode('NpcPortrait', frame, 0, 8, 300, 432);
        const ps = portraitNode.addComponent(Sprite);
        ps.sizeMode = Sprite.SizeMode.CUSTOM;
        const psf = new SpriteFrame();
        psf.texture = texture;
        ps.spriteFrame = psf;
        portraitNode.getComponent(UITransform)!.setContentSize(300, 432);

        const tab = this.uiNode('NpcNameTab', frame, 0, -236, 150, 34);
        const tg = tab.addComponent(Graphics);
        tg.fillColor = new Color(246, 240, 226, 255);
        tg.roundRect(-75, -17, 150, 34, 17);
        tg.fill();
        this.label(tab, '园丁', 17, C.ink, 0, 0, 120, 28, Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        return node;
    }

    private makeScreenQuad(name: string, w: number, h: number, texture: Texture2D, tiling: Vec4): Node {
        const node = new Node(name);
        node.parent = this.node;
        const mesh = utils.MeshUtils.createMesh({
            positions: new Float32Array([-w / 2, 0, 0, w / 2, 0, 0, w / 2, h, 0, -w / 2, h, 0]),
            uvs: new Float32Array([0, 0, 1, 0, 1, 1, 0, 1]),
            normals: new Float32Array([0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1]),
            indices: new Uint16Array([0, 1, 2, 0, 2, 3]),
        });
        const mr = node.addComponent(MeshRenderer);
        mr.mesh = mesh;
        const mat = new Material();
        mat.initialize({ effectName: 'builtin-unlit', technique: 1, defines: { USE_TEXTURE: true } });
        mat.setProperty('mainColor', C.white);
        mat.setProperty('mainTexture', texture);
        mat.setProperty('tilingOffset', tiling);
        mr.setMaterial(mat, 0);
        mr.shadowCastingMode = MeshRenderer.ShadowCastingMode.OFF;
        mr.receiveShadow = false;
        return node;
    }

    private makeWorldSprite(name: string, texture: Texture2D, w: number, h: number, anchorY: number): Node {
        const node = this.uiNode(name, this.characterLayer, 0, 0, w, h);
        const ut = node.getComponent(UITransform)!;
        ut.setAnchorPoint(0.5, anchorY);
        const sprite = node.addComponent(Sprite);
        sprite.sizeMode = Sprite.SizeMode.CUSTOM;
        const sf = new SpriteFrame();
        sf.texture = texture;
        sprite.spriteFrame = sf;
        ut.setContentSize(w, h);
        return node;
    }

    private updateWorldBillboards(): void {
        const camRot = this.mainCamera.node.rotation;
        for (const n of [this.npcNode, this.fxPickupNode, this.fxBoardNode]) {
            if (n && n.active) n.setRotation(camRot);
        }
    }

    // --------------------------------------------------------------------- UI

    private setupUI(): void {
        const scene = director.getScene()!;
        this.canvasNode = new Node('Canvas');
        this.canvasNode.layer = Layers.Enum.UI_2D;
        this.canvasNode.parent = scene;
        const ut = this.canvasNode.addComponent(UITransform);
        ut.setContentSize(DESIGN_W, DESIGN_H);
        const canvas = this.canvasNode.addComponent(Canvas);

        const camNode = new Node('UICamera');
        camNode.layer = Layers.Enum.UI_2D;
        camNode.parent = this.canvasNode;
        camNode.setPosition(0, 0, 1000);
        const cam = camNode.addComponent(Camera);
        cam.projection = Camera.ProjectionType.ORTHO;
        cam.orthoHeight = DESIGN_H / 2;
        cam.near = 0.1;
        cam.far = 2000;
        cam.clearFlags = Camera.ClearFlag.DEPTH_ONLY;
        cam.visibility = Layers.Enum.UI_2D;
        cam.priority = 10;
        canvas.cameraComponent = cam;
        this.canvasUT = ut;

        this.characterLayer = this.uiNode('CharacterLayer', this.canvasNode, 0, 0, DESIGN_W, DESIGN_H);
        this.scrim = this.uiNode('Scrim', this.canvasNode, 0, 0, DESIGN_W, DESIGN_H);
        const scrimG = this.scrim.addComponent(Graphics);
        scrimG.fillColor = new Color(38, 36, 31, 118);
        scrimG.rect(-DESIGN_W / 2, -DESIGN_H / 2, DESIGN_W, DESIGN_H);
        scrimG.fill();
        this.scrim.active = false;

        this.hudRoot = this.uiNode('HudRoot', this.canvasNode, 0, 0, DESIGN_W, DESIGN_H);
        this.dialogueRoot = this.uiNode('DialogueRoot', this.canvasNode, 0, 0, DESIGN_W, DESIGN_H);
        this.hudRoot.setPosition(0, 0, 0);
        this.dialogueRoot.setPosition(0, 0, 0);
        this.dialogueRoot.active = false;

        this.buildHud();
        this.buildDialogue();
        this.studioRoot = this.uiNode('StudioRoot', this.canvasNode, 0, 0, DESIGN_W, DESIGN_H);
        this.studioRoot.active = false;
    }

    private uiNode(name: string, parent: Node, x: number, y: number, w: number, h: number): Node {
        const node = new Node(name);
        node.layer = Layers.Enum.UI_2D;
        node.parent = parent;
        const ut = node.addComponent(UITransform);
        ut.setContentSize(w || 100, h || 100);
        node.setPosition(x, y, 0);
        return node;
    }

    private paperPanel(parent: Node, x: number, y: number, w: number, h: number, name = 'PaperPanel'): Sprite {
        const node = this.uiNode(name, parent, x, y, w, h);
        const backing = this.uiNode(name + '_Backing', parent, x, y, w, h);
        const bg = backing.addComponent(Graphics);
        bg.fillColor = new Color(243, 240, 230, 245);
        bg.rect(-w / 2, -h / 2, w, h);
        bg.fill();
        backing.setSiblingIndex(node.getSiblingIndex());
        const sprite = node.addComponent(Sprite);
        sprite.sizeMode = Sprite.SizeMode.CUSTOM;
        sprite.type = Sprite.Type.SLICED;
        const frame = this.makeSlicedFrame();
        if (frame) sprite.spriteFrame = frame;
        const ut = node.getComponent(UITransform)!;
        ut.setContentSize(w, h);
        this.paperSprites.push(sprite);
        return sprite;
    }

    private label(parent: Node, text: string, size: number, color: Color, x: number, y: number, w: number, h: number,
        align: number = Label.HorizontalAlign.LEFT,
        valign: number = Label.VerticalAlign.CENTER,
        serif = false): Label {
        const node = this.uiNode('Label', parent, x, y, w, h);
        const label = node.addComponent(Label);
        label.string = text;
        label.fontSize = size;
        label.lineHeight = Math.round(size * 1.4);
        label.color = color;
        label.horizontalAlign = align;
        label.verticalAlign = valign;
        label.overflow = Label.Overflow.CLAMP;
        label.enableWrapText = true;
        label.useSystemFont = true;
        if (serif) this.labelsSerif.push(label); else this.labelsSans.push(label);
        return label;
    }

    private icon(parent: Node, key: string, x: number, y: number, size: number, color: Color): Sprite {
        const node = this.uiNode('Icon_' + key, parent, x, y, size, size);
        const sprite = node.addComponent(Sprite);
        sprite.sizeMode = Sprite.SizeMode.CUSTOM;
        sprite.color = color;
        const ut = node.getComponent(UITransform)!;
        ut.setContentSize(size, size);
        const tex = this.iconTextures[key];
        if (tex) {
            const sf = new SpriteFrame();
            sf.texture = tex;
            sprite.spriteFrame = sf;
        }
        if (!this.iconTargets.has(key)) this.iconTargets.set(key, []);
        this.iconTargets.get(key)!.push(sprite);
        return sprite;
    }

    private buildHud(): void {
        // Quest card, top left.
        const card = this.paperPanel(this.hudRoot, -428, 272, 368, 118, 'QuestCard');
        card.color = new Color(252, 249, 240, 218);
        const badgeNode = this.uiNode('QuestBadge', card.node, 138, 12, 80, 26);
        const badgeG = badgeNode.addComponent(Graphics);
        badgeG.fillColor = new Color(159, 216, 200, 90);
        badgeG.strokeColor = new Color(79, 138, 121, 120);
        badgeG.lineWidth = 1.5;
        badgeG.roundRect(-40, -13, 80, 26, 13);
        badgeG.fill();
        badgeG.stroke();
        this.questBadge = this.label(badgeNode, '待接取', 13, C.mintDeep, 0, 0, 76, 24, Label.HorizontalAlign.CENTER);

        this.icon(card.node, 'icon_pin', 146, 40, 18, C.goldDeep);
        this.icon(card.node, 'icon_talk', -146, 2, 24, C.mintDeep);

        this.label(card.node, '当前任务', 13, C.muted, -33, 38, 190, 20);
        this.questTitle = this.label(card.node, '和园丁聊聊', 24, C.ink, -13, 12, 230, 32, Label.HorizontalAlign.LEFT,
            Label.VerticalAlign.CENTER, true);
        this.questSub = this.label(card.node, '园丁就在南入口的路石旁', 15, C.muted, -3, -23, 250, 24);

        // Menu button, top right.
        const menu = this.paperPanel(this.hudRoot, 582, 250, 58, 58, 'MenuButton');
        menu.color = new Color(255, 255, 255, 225);
        this.icon(menu.node, 'icon_menu', 0, 0, 26, C.ink);

        // Joystick, bottom left.
        this.joystickRoot = this.uiNode('Joystick', this.hudRoot, -530, -212, 140, 140);
        const base = this.uiNode('JoystickBase', this.joystickRoot, 0, 0, 140, 140);
        this.joystickBase = base;
        const bg = base.addComponent(Graphics);
        bg.fillColor = new Color(250, 248, 241, 90);
        bg.strokeColor = new Color(46, 50, 52, 96);
        bg.lineWidth = 1.5;
        bg.circle(0, 0, 62);
        bg.fill();
        bg.stroke();
        bg.strokeColor = new Color(46, 50, 52, 56);
        bg.lineWidth = 1;
        bg.circle(0, 0, 46);
        bg.stroke();
        for (let i = 0; i < 8; i++) {
            const a = i * Math.PI / 4;
            bg.moveTo(Math.cos(a) * 54, Math.sin(a) * 54);
            bg.lineTo(Math.cos(a) * 60, Math.sin(a) * 60);
        }
        bg.stroke();
        const knob = this.uiNode('JoystickKnob', base, 0, 0, 52, 52);
        const kg = knob.addComponent(Graphics);
        kg.fillColor = new Color(246, 243, 234, 245);
        kg.strokeColor = new Color(79, 138, 121, 210);
        kg.lineWidth = 1.2;
        kg.circle(0, 0, 24);
        kg.fill();
        kg.stroke();
        kg.fillColor = new Color(159, 216, 200, 255);
        kg.circle(0, 0, 7);
        kg.fill();
        this.joystickKnob = knob;
        this.bindJoystick(base);

        // Action button, bottom right.
        this.actionRoot = new Node('ActionButton');
        this.actionRoot.layer = Layers.Enum.UI_2D;
        this.actionRoot.parent = this.hudRoot;
        this.actionRoot.setPosition(500, -212, 0);
        this.actionRoot.addComponent(UITransform).setContentSize(126, 126);
        const actionPaper = this.actionRoot.addComponent(Sprite);
        actionPaper.sizeMode = Sprite.SizeMode.CUSTOM;
        actionPaper.type = Sprite.Type.SLICED;
        actionPaper.color = new Color(255, 255, 255, 240);
        const actionFrame = this.makeSlicedFrame();
        if (actionFrame) actionPaper.spriteFrame = actionFrame;
        this.paperSprites.push(actionPaper);
        this.actionPaper = actionPaper;
        this.actionIconSprite = this.icon(this.actionRoot, 'icon_talk', 0, 30, 34, C.mintDeep);
        this.actionLabel = this.label(this.actionRoot, '交谈', 20, C.ink, 0, -8, 110, 30, Label.HorizontalAlign.CENTER);
        this.actionSub = this.label(this.actionRoot, '园丁', 14, C.muted, 0, -34, 100, 22, Label.HorizontalAlign.CENTER);
        this.actionRoot.on(Node.EventType.TOUCH_END, () => this.onActionPressed());

        console.log('[COURTYARD] HUD built (real Labels + nine-slice + Graphics joystick)');
    }

    private buildDialogue(): void {
        const panel = this.paperPanel(this.dialogueRoot, 0, -226, 1180, 220, 'DialoguePaper');
        panel.color = new Color(250, 247, 238, 222);

        const portraitBg = this.paperPanel(panel.node, -488, 0, 168, 168, 'PortraitPaper');
        portraitBg.color = new Color(255, 255, 255, 255);
        const portraitNode = this.uiNode('Portrait', portraitBg.node, 0, 0, 148, 148);
        const portrait = portraitNode.addComponent(Sprite);
        portrait.sizeMode = Sprite.SizeMode.CUSTOM;
        portrait.color = new Color(255, 255, 255, 0);
        const put = portraitNode.getComponent(UITransform)!;
        put.setContentSize(148, 148);
        this.portraitSprite = portrait;
        this.portraitSprites['npc'] = portrait;

        // player portrait is a second sprite, hidden until page 2
        const playerNode = this.uiNode('PortraitPlayer', portraitBg.node, 0, 0, 148, 148);
        const playerSprite = playerNode.addComponent(Sprite);
        playerSprite.sizeMode = Sprite.SizeMode.CUSTOM;
        playerSprite.color = new Color(255, 255, 255, 0);
        playerNode.getComponent(UITransform)!.setContentSize(148, 148);
        playerNode.active = false;
        this.portraitSprites['player'] = playerSprite;
        this.playerPortraitNode = playerNode;

        this.speakerLabel = this.label(panel.node, '园丁', 28, C.ink, -280, 64, 180, 34, Label.HorizontalAlign.LEFT,
            Label.VerticalAlign.CENTER, true);
        this.pageLabel = this.label(panel.node, '第 1 页 / 共 2 页', 13, C.mintDeep, 30, 62, 190, 24);
        this.bodyLabel = this.label(panel.node, '风把留言板上的三张明信片吹散了，能帮我找回来吗？', 24, C.inkBody,
            -25, 8, 690, 68, Label.HorizontalAlign.LEFT, Label.VerticalAlign.TOP);
        this.hintLabel = this.label(panel.node, '点击「下一页」继续', 15, C.mintDeep, -210, -64, 320, 24);
        this.icon(panel.node, 'icon_sparkle', -384, -64, 12, C.mintDeep);
        this.icon(panel.node, 'icon_postcard', 330, 62, 36, C.goldDeep);
        const accent = this.uiNode('DialogueAccent', panel.node, -266, 38, 128, 6);
        const ag = accent.addComponent(Graphics);
        ag.fillColor = new Color(159, 216, 200, 170);
        ag.roundRect(-64, -1.5, 128, 3, 1.5);
        ag.fill();
        const underline = this.uiNode('SpeakerUnderline', panel.node, -272, 46, 120, 4);
        const ug = underline.addComponent(Graphics);
        ug.strokeColor = new Color(138, 100, 37, 110);
        ug.lineWidth = 1;
        ug.moveTo(-58, 0); ug.lineTo(58, 1.5);
        ug.stroke();
        this.icon(panel.node, 'icon_leaf', 285, -66, 14, C.mintDeep);

        this.dialogueActionNode = this.uiNode('DialogueNext', panel.node, 462, -18, 188, 62);
        const nextPaper = this.dialogueActionNode.addComponent(Sprite);
        this.dialogueNextSprite = nextPaper;
        nextPaper.sizeMode = Sprite.SizeMode.CUSTOM;
        nextPaper.type = Sprite.Type.SLICED;
        nextPaper.color = new Color(255, 255, 255, 255);
        const nf = this.makeSlicedFrame();
        if (nf) nextPaper.spriteFrame = nf;
        this.paperSprites.push(nextPaper);
        this.nextLabel = this.label(this.dialogueActionNode, '下一页', 20, C.ink, -14, 0, 120, 30, Label.HorizontalAlign.CENTER);
        this.dialogueNextLabel = this.nextLabel;
        this.icon(this.dialogueActionNode, 'icon_arrow', 66, 0, 20, C.ink);
        this.dialogueActionNode.on(Node.EventType.TOUCH_END, () => this.advanceDialogue());

        const pageNote = this.label(panel.node, '共 2 页', 13, C.muted, 462, -58, 120, 20, Label.HorizontalAlign.CENTER);
        pageNote.name = 'PageNote';

        const closeNode = this.uiNode('DialogueClose', panel.node, 548, 82, 44, 44);
        const closePaper = closeNode.addComponent(Sprite);
        closePaper.sizeMode = Sprite.SizeMode.CUSTOM;
        closePaper.type = Sprite.Type.SLICED;
        closePaper.color = new Color(255, 255, 255, 235);
        const cf = this.makeSlicedFrame();
        if (cf) closePaper.spriteFrame = cf;
        this.paperSprites.push(closePaper);
        this.icon(closeNode, 'icon_close', 0, 0, 18, C.ink);
        closeNode.on(Node.EventType.TOUCH_END, () => this.closeDialogue());

        console.log('[COURTYARD] dialogue built (real copy, portraits, page states)');
    }

    private playerPortraitNode: Node | null = null;

    private bindJoystick(base: Node): void {
        const handle = (event: EventTouch) => {
            if (this.dialogueVisible) return;
            const loc = event.getUILocation();
            const local = base.getComponent(UITransform)!.convertToNodeSpaceAR(new Vec3(loc.x, loc.y, 0), new Vec3());
            const len = Math.sqrt(local.x * local.x + local.y * local.y);
            const max = 46;
            const k = len > max ? max / len : 1;
            const x = local.x * k;
            const y = local.y * k;
            this.joystickKnob.setPosition(x, y, 0);
            const dead = 0.12;
            const nx = x / max;
            const ny = y / max;
            const nlen = Math.sqrt(nx * nx + ny * ny);
            this.joy.set(nlen > dead ? nx : 0, nlen > dead ? ny : 0);
        };
        base.on(Node.EventType.TOUCH_START, handle);
        base.on(Node.EventType.TOUCH_MOVE, handle);
        base.on(Node.EventType.TOUCH_END, () => this.resetJoystick());
        base.on(Node.EventType.TOUCH_CANCEL, () => this.resetJoystick());
    }

    private resetJoystick(): void {
        this.joy.set(0, 0);
        if (this.joystickKnob) this.joystickKnob.setPosition(0, 0, 0);
    }

    private setupInput(): void {
        input.on(Input.EventType.KEY_DOWN, this.onKeyDown, this);
        input.on(Input.EventType.KEY_UP, this.onKeyUp, this);
    }

    private onKeyDown(event: any): void {
        const code = event.keyCode;
        this.keys.add(code);
        if (code === KeyCode.KEY_E) {
            if (this.dialogueVisible) this.advanceDialogue();
            else this.openDialogue(1);
        } else if (code === KeyCode.KEY_H) {
            this.setUiVisible(!this.uiVisible);
        } else if (code === KeyCode.ESCAPE) {
            this.closeDialogue();
        }
    }

    private onKeyUp(event: any): void {
        this.keys.delete(event.keyCode);
    }

    private onActionPressed(): void {
        if (this.dialogueVisible) this.advanceDialogue();
        else this.openDialogue(1);
    }

    // ------------------------------------------------------------ state / UI

    private lockInput(): void {
        this.inputLocked = true;
        this.keys.clear();
        this.joy.set(0, 0);
        this.manualMoving = false;
        this.moving = false;
        this.resetJoystick();
    }

    private unlockInput(): void {
        this.inputLocked = false;
        this.keys.clear();
        this.joy.set(0, 0);
    }

    private setPause(paused: boolean): void {
        this.paused = paused;
        if (paused) this.lockInput();
        else if (!this.dialogueVisible) this.unlockInput();
        console.log('[COURTYARD] paused=' + paused);
    }

    private openDialogue(page = 1): void {
        if (!this.uiVisible) this.setUiVisible(true);
        this.lockInput();
        this.dialogueVisible = true;
        this.dialoguePage = page;
        this.applyDialoguePage();
        this.dialogueRoot.active = true;
        this.scrim.active = true;
        this.actionRoot.active = false;
        this.joystickRoot.active = false;
        this.resetJoystick();
        console.log('[COURTYARD] dialogue open page=' + page);
    }

    private applyDialoguePage(): void {
        const page1 = this.dialoguePage === 1;
        this.speakerLabel.string = page1 ? '园丁' : '主角';
        this.bodyLabel.string = page1
            ? '风把留言板上的三张明信片吹散了，能帮我找回来吗？'
            : '我去附近看看，很快回来。';
        this.pageLabel.string = '第 ' + this.dialoguePage + ' 页 / 共 2 页';
        this.nextLabel.string = page1 ? '下一页' : '接受';
        this.hintLabel.string = page1 ? '点击「下一页」继续' : '任务将开始';
        if (this.portraitSprite) this.portraitSprite.node.active = page1;
        if (this.playerPortraitNode) this.playerPortraitNode.active = !page1;
    }

    private advanceDialogue(): void {
        if (!this.dialogueVisible) return;
        if (this.dialoguePage === 1) {
            this.dialoguePage = 2;
            this.applyDialoguePage();
            console.log('[COURTYARD] dialogue page 2');
            return;
        }
        this.accepted = true;
        this.questTitle.string = '找回明信片 0/3';
        this.questSub.string = '长椅、花坛、廊架附近找找';
        this.questBadge.string = '任务中';
        this.closeDialogue();
        console.log('[COURTYARD] dialogue accepted; quest = COLLECTING (sample HUD only)');
    }

    private closeDialogue(): void {
        if (!this.dialogueVisible) {
            this.dialogueRoot.active = false;
            this.scrim.active = false;
            return;
        }
        this.dialogueVisible = false;
        this.dialogueRoot.active = false;
        this.scrim.active = false;
        this.actionRoot.active = true;
        this.joystickRoot.active = true;
        if (!this.paused) this.unlockInput();
        console.log('[COURTYARD] dialogue closed');
    }

    private setUiVisible(visible: boolean): void {
        this.uiVisible = visible;
        this.hudRoot.active = visible;
        if (!visible) {
            this.dialogueRoot.active = false;
            this.scrim.active = false;
            this.dialogueVisible = false;
        } else if (this.dialogueVisible) {
            this.dialogueRoot.active = true;
            this.scrim.active = true;
        }
        console.log('[COURTYARD] ui visible=' + visible);
    }

    // ----------------------------------------------------------------- update

    update(dt: number): void {
        if (!this.spineNode) return;
        this.clock += dt;
        let mx = 0;
        let mz = 0;
        if (!this.dialogueVisible && !this.inputLocked) {
            if (this.keys.has(KeyCode.KEY_W) || this.keys.has(KeyCode.ARROW_UP)) mz += 1;
            if (this.keys.has(KeyCode.KEY_S) || this.keys.has(KeyCode.ARROW_DOWN)) mz -= 1;
            if (this.keys.has(KeyCode.KEY_A) || this.keys.has(KeyCode.ARROW_LEFT)) mx -= 1;
            if (this.keys.has(KeyCode.KEY_D) || this.keys.has(KeyCode.ARROW_RIGHT)) mx += 1;
            mx += this.joy.x;
            mz += this.joy.y;
        }
        const len = Math.sqrt(mx * mx + mz * mz);
        this.moving = this.manualMoving || len > 0.08;
        if (len > 0.08) {
            mx /= len;
            mz /= len;
            if (mx > 0.15) this.facing = 1;
            else if (mx < -0.15) this.facing = -1;
            const step = this.speed * Math.min(dt, 0.05);
            this.tryMove(mx * step, mz * step);
        }
        this.playerAnchor.setPosition(this.playerPos);
        if (this.shadowNode) {
            this.shadowNode.setPosition(this.playerPos.x, PAVING_TOP + 0.006, this.playerPos.z);
        }
        if (this.cameraMode === 'game') {
            const cam = this.mainCamera.node;
            cam.setPosition(this.playerPos.x - 2.5, 11.5, this.playerPos.z - 9.4);
            cam.lookAt(new Vec3(this.playerPos.x - 2.5, 3.5, this.playerPos.z + 1.5));
        }
        this.updateAnimation();
        this.updateCharacterTransform();
        this.updateWorldBillboards();
    }

    private tryMove(dx: number, dz: number): void {
        const nx = Math.max(-MAP_BOUNDS_X, Math.min(MAP_BOUNDS_X, this.playerPos.x + dx));
        if (!this.blocked(nx, this.playerPos.z)) this.playerPos.x = nx;
        const nz = Math.max(-MAP_BOUNDS_Z, Math.min(MAP_BOUNDS_Z, this.playerPos.z + dz));
        if (!this.blocked(this.playerPos.x, nz)) this.playerPos.z = nz;
    }

    private blocked(x: number, z: number): boolean {
        const r = 0.32;
        if (x * x + z * z < (2.08 + r) * (2.08 + r)) return true;
        // bench AABB (rotated 90deg: 1.7 along Z, 0.7 along X)
        if (x > -9.3 - 0.35 - r && x < -9.3 + 0.35 + r &&
            z > -4.4 - 0.85 - r && z < -4.4 + 0.85 + r) return true;
        if (x > -11.8 - 1.64 - r && x < -11.8 + 1.64 + r &&
            z > 4.6 - 0.74 - r && z < 4.6 + 0.74 + r) return true;
        if (x > 11.8 - 0.74 - r && x < 11.8 + 0.74 + r &&
            z > -4.8 - 1.64 - r && z < -4.8 + 1.64 + r) return true;
        if (x > -1.25 - r && x < 1.25 + r && z > 6.9 - 0.16 - r && z < 6.9 + 0.16 + r) return true;
        for (const [lx, lz] of [[-6.8, -6.8], [6.8, -6.8], [-6.8, 6.8], [6.8, 6.8]]) {
            const dx = x - lx, dz = z - lz;
            if (dx * dx + dz * dz < (0.3 + r) * (0.3 + r)) return true;
        }
        const sdx = x + 3.4, sdz = z + 7.5;
        if (sdx * sdx + sdz * sdz < (0.28 + r) * (0.28 + r)) return true;
        return false;
    }

    // --------------------------------------------------------- engine viewer

    private clearViewer(): void {
        if (this.studioRoot) {
            this.studioRoot.removeAllChildren();
            this.studioRoot.active = false;
        }
        this.studioActive = false;
        this.presentationScale = 1.0;
        this.paused = false;
        this.inputLocked = false;
        this.keys.clear();
        this.joy.set(0, 0);
        this.moving = false;
        this.manualMoving = false;
        this.actionRoot.setScale(1, 1, 1);
        if (this.dialogueActionNode) this.dialogueActionNode.setScale(1, 1, 1);
        if (this.dialogueNextSprite) this.dialogueNextSprite.color = new Color(255, 255, 255, 255);
        if (this.fxPickupNode) this.fxPickupNode.active = false;
        if (this.fxBoardNode) this.fxBoardNode.active = false;
        if (this.npcNode) this.npcNode.active = true;
    }

    private viewerBackdrop(alpha = 236): void {
        this.studioRoot.active = true;
        const bg = this.uiNode('ViewerBackdrop', this.studioRoot, 0, 0, DESIGN_W, DESIGN_H);
        const g = bg.addComponent(Graphics);
        g.fillColor = new Color(243, 240, 230, alpha);
        g.rect(-DESIGN_W / 2, -DESIGN_H / 2, DESIGN_W, DESIGN_H);
        g.fill();
    }

    private viewerTitle(text: string, y: number, size = 46, serif = true): Label {
        return this.label(this.studioRoot, text, size, C.ink, 0, y, 1080, Math.round(size * 1.5),
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, serif);
    }

    private viewerButton(x: number, y: number, w: number, h: number, text: string,
        pressed = false, gold = false, iconKey = ''): Node {
        const panel = this.paperPanel(this.studioRoot, x, y, w, h, 'ViewerBtn_' + text);
        panel.color = pressed ? new Color(228, 220, 205, 255)
            : gold ? new Color(248, 238, 218, 255) : new Color(255, 255, 255, 245);
        const node = panel.node;
        if (pressed) node.setScale(0.97, 0.97, 1);
        const offset = iconKey ? -14 : 0;
        this.label(node, text, 20, gold ? C.goldDeep : C.ink, offset, 0, w - 50, 34, Label.HorizontalAlign.CENTER);
        if (iconKey) this.icon(node, iconKey, w / 2 - 30, 0, 20, gold ? C.goldDeep : C.ink);
        return node;
    }

    private viewerStamp(id: string): void {
        this.label(this.studioRoot, 'COCOS 3.8.8 · ' + id, 11, new Color(120, 122, 114, 255),
            -500, 330, 260, 20, Label.HorizontalAlign.LEFT);
    }

    private viewerPanel(x: number, y: number, w: number, h: number, tone: Color = new Color(255, 255, 255, 246)): Sprite {
        const p = this.paperPanel(this.studioRoot, x, y, w, h, 'ViewerPanel');
        p.color = tone;
        return p;
    }

    private setAction(label: string, sub: string, icon: string, opts: { hidden?: boolean; disabled?: boolean; gold?: boolean; pressed?: boolean } = {}): void {
        this.actionRoot.active = !opts.hidden;
        if (opts.hidden) return;
        if (this.actionLabel) this.actionLabel.string = label;
        if (this.actionSub) this.actionSub.string = sub;
        if (this.actionPaper) {
            this.actionPaper.color = opts.disabled ? new Color(226, 224, 216, 225)
                : opts.gold ? new Color(248, 235, 210, 250) : new Color(255, 255, 255, 240);
        }
        if (this.actionIconSprite) {
            const tex = this.iconTextures[icon];
            if (tex) {
                const sf = new SpriteFrame();
                sf.texture = tex;
                this.actionIconSprite.spriteFrame = sf;
            }
            this.actionIconSprite.color = opts.disabled ? C.faint : opts.gold ? C.goldDeep : C.mintDeep;
        }
        if (this.actionLabel) this.actionLabel.color = opts.disabled ? C.faint : C.ink;
        if (this.actionSub) this.actionSub.color = opts.disabled ? C.faint : C.muted;
        const s = opts.pressed ? 0.965 : 1;
        this.actionRoot.setScale(s, s, 1);
    }

    private setJoystick(visible: boolean, kx = 0, ky = 0): void {
        this.joystickRoot.active = visible;
        if (visible) this.joystickKnob.setPosition(kx, ky, 0);
    }

    private applyHudState(id: string): void {
        const table: Record<string, any> = {
            hud_talk: ['和园丁聊聊', '园丁就在南入口的石路旁', '待接取'],
            hud_0_3: ['找回明信片 0/3', '长椅、花坛、廊架各有一张', '0/3'],
            hud_1_3: ['找回明信片 1/3', '已找到 1 张，还有 2 张', '1/3'],
            hud_2_3: ['找回明信片 2/3', '还差最后 1 张', '2/3'],
            hud_3_3: ['将明信片挂回留言板', '三张已找齐，去中央广场', '可提交'],
            hud_submit: ['将明信片挂回留言板', '靠近留言板 · 布置', '可提交'],
            hud_done: ['留言板已布置完成', '可继续漫步，或从菜单重新开始', '完成'],
            interact_talk: ['和园丁聊聊', '园丁就在南入口的石路旁', '待接取'],
            interact_pick: ['找回明信片 0/3', '长椅、花坛、廊架各有一张', '0/3'],
            interact_place: ['将明信片挂回留言板', '三张已找齐，去中央广场', '可提交'],
            interact_view: ['留言板已布置完成', '可继续漫步，或从菜单重新开始', '完成'],
            interact_pressed: ['找回明信片 0/3', '长椅、花坛、廊架各有一张', '0/3'],
            interact_disabled: ['和园丁聊聊', '园丁就在南入口的石路旁', '待接取'],
            interact_hidden: ['找回明信片 2/3', '还差最后 1 张', '2/3'],
            joystick_idle: ['找回明信片 1/3', '已找到 1 张，还有 2 张', '1/3'],
            joystick_drag: ['找回明信片 1/3', '已找到 1 张，还有 2 张', '1/3'],
            joystick_hidden: ['找回明信片 1/3', '已找到 1 张，还有 2 张', '1/3'],
            toast_pickup: ['找回明信片 1/3', '已找到 1 张，还有 2 张', '1/3'],
            toast_task_update: ['将明信片挂回留言板', '三张已找齐，去中央广场', '可提交'],
            toast_error: ['找回明信片 0/3', '长椅、花坛、廊架各有一张', '0/3'],
            tip_first_move: ['找回明信片 0/3', '长椅、花坛、廊架各有一张', '0/3'],
            tip_first_interact: ['和园丁聊聊', '园丁就在南入口的石路旁', '待接取'],
            safe_area_landscape: ['找回明信片 2/3', '还差最后 1 张', '2/3'],
        };
        const row = table[id] || table.hud_talk;
        this.questTitle.string = row[0];
        this.questSub.string = row[1];
        this.questBadge.string = row[2];
        this.setUiVisible(true);
        this.closeDialogue();
        this.npcNode && (this.npcNode.active = true);
        this.setJoystick(true);
        if (id === 'hud_done' || id === 'interact_view') {
            this.setAction('查看', '留言板', 'icon_view');
        } else if (id === 'hud_3_3' || id === 'hud_submit' || id === 'interact_place' || id === 'toast_task_update') {
            this.setAction('布置留言板', '留言板', 'icon_place', { gold: true });
        } else if (id === 'interact_talk' || id === 'hud_talk' || id === 'tip_first_interact') {
            this.setAction('交谈', '园丁', 'icon_talk');
        } else if (id === 'interact_pick' || id === 'interact_pressed' || id === 'toast_pickup' || id === 'toast_error') {
            this.setAction('拾取', '明信片', 'icon_pickup', { pressed: id === 'interact_pressed' });
        } else if (id === 'interact_disabled') {
            this.setAction('拾取', '先问问园丁吧', 'icon_lock', { disabled: true });
        } else if (id === 'interact_hidden') {
            this.setAction('', '', 'icon_pickup', { hidden: true });
        } else {
            this.setAction('拾取', '明信片', 'icon_pickup');
        }
        if (id === 'interact_hidden') this.setAction('', '', 'icon_pickup', { hidden: true });
        if (id === 'joystick_hidden') {
            this.setJoystick(false);
            this.setAction('', '', 'icon_pickup', { hidden: true });
            this.annotate('MOVEMENT LOCKED · 对白/菜单打开时隐藏');
        } else if (id === 'joystick_drag') {
            this.setJoystick(true, 23, -13);
            this.annotate('DRAG · 死区 0.12 · 松手停止');
        }
    }

    private annotate(text: string): void {
        this.studioRoot.active = true;
        this.studioActive = true;
        const n = this.uiNode('ViewerNote', this.studioRoot, 0, -312, 900, 26);
        this.label(n, text, 13, C.muted, 0, 0, 900, 24, Label.HorizontalAlign.CENTER);
    }

    private setUiState(id: string): void {
        this.clearViewer();
        if (id.startsWith('spec_') || id === 'pack001') {
            this.viewerBackdrop(255);
            this.studioActive = true;
            this.lockInput();
            this.setUiVisible(false);
            this.viewerStamp(id);
            this.buildViewerSpec(id);
            return;
        }
        if (id === 'board_empty' || id === 'board_full' || id === 'board_reset') {
            this.focusAsset('FX003');
            this.setBoardState(id === 'board_full' ? 'full' : id === 'board_reset' ? 'reset' : 'empty');
            this.questTitle.string = id === 'board_full' ? '将明信片挂回留言板' : '找回明信片 0/3';
            this.questSub.string = id === 'board_full' ? '三张已找齐，去中央广场' : '长椅、花坛、廊架各有一张';
            this.questBadge.string = id === 'board_full' ? '可提交' : '0/3';
            this.setUiVisible(true);
            this.hudRoot.active = true;
            this.setJoystick(true);
            this.setAction(id === 'board_full' ? '布置留言板' : '拾取', id === 'board_full' ? '留言板' : '明信片',
                id === 'board_full' ? 'icon_place' : 'icon_pickup', { gold: id === 'board_full' });
            this.viewerId = id;
            return;
        }
        if (['title_initial', 'title_pressed', 'title_loading', 'loading_progress', 'loading_failure', 'loading_retry_pressed', 'pause_default', 'pause_sound_on', 'pause_restart_pressed', 'complete_default', 'complete_continue_pressed', 'rotate_notice'].includes(id)) {
            this.setUiVisible(false);
            this.studioActive = true;
            this.studioRoot.active = true;
            if (id.startsWith('pause_')) this.setPause(true);
            else this.lockInput();
            this.buildViewerOverlay(id);
            this.viewerStamp(id);
            return;
        }
        if (id === 'safe_area_landscape') {
            this.applyHudState(id);
            this.studioRoot.active = true;
            this.studioActive = true;
            this.buildViewerOverlay(id);
            this.viewerStamp(id);
            return;
        }
        if (id.startsWith('dialogue_')) {
            this.setUiVisible(true);
            this.questTitle.string = '和园丁聊聊';
            this.questSub.string = '园丁就在南入口的石路旁';
            this.questBadge.string = '待接取';
            this.openDialogue(id === 'dialogue_gardener_p1' ? 1 : 2);
            if (id === 'dialogue_accept_pressed') {
                this.nextLabel.string = '接受';
                this.dialogueActionNode.setScale(0.965, 0.965, 1);
                if (this.dialogueNextSprite) this.dialogueNextSprite.color = new Color(228, 220, 205, 255);
            }
            return;
        }
        if (id.startsWith('toast_') || id.startsWith('tip_')) {
            this.applyHudState(id);
            this.studioRoot.active = true;
            this.studioActive = true;
            this.viewerStamp(id);
            this.buildViewerNote(id);
            return;
        }
        if (id.startsWith('hud_') || id.startsWith('interact_') || id.startsWith('joystick_')) {
            this.applyHudState(id);
            this.studioRoot.active = true;
            this.studioActive = true;
            this.viewerStamp(id);
            return;
        }
        this.viewerBackdrop(255);
        this.studioActive = true;
        this.setUiVisible(false);
        this.viewerStamp(id);
    }

    private buildViewerSpec(id: string): void {
        if (id === 'spec_type') {
            this.viewerTitle('秋庭来信', 250, 64);
            this.label(this.studioRoot, '找回明信片', 34, C.inkBody, 0, 120, 900, 48, Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
            this.label(this.studioRoot, '风把留言板上的三张明信片吹散了，能帮我找回来吗？', 23, C.inkBody, 0, 55, 980, 40, Label.HorizontalAlign.CENTER);
            this.label(this.studioRoot, '0/3   1/3   2/3   3/3', 20, C.goldDeep, 0, 0, 700, 32, Label.HorizontalAlign.CENTER);
            this.label(this.studioRoot, '正文 Noto Sans SC · 标题/姓名 Noto Serif SC · 13 / 14 / 16 / 20 / 23 / 34 / 64 px', 14, C.muted, 0, -80, 1000, 26, Label.HorizontalAlign.CENTER);
            this.label(this.studioRoot, 'SAMPLE · 引擎内真实字体渲染', 12, C.faint, 0, -130, 700, 22, Label.HorizontalAlign.CENTER);
        } else if (id === 'spec_nine_slice') {
            this.viewerTitle('纸片九宫格与独立装饰', 290, 38);
            const panels = [
                [-390, 40, 300, 150, '小面板 300×150'],
                [0, 40, 380, 200, '对话纸片 380×200'],
                [400, 25, 280, 130, '按钮纸片 280×130'],
            ] as any[];
            for (const [x, y, w, h, label] of panels) {
                const p = this.viewerPanel(x, y, w, h);
                this.label(p.node, label, 14, C.muted, 0, -h / 2 + 22, w - 30, 22, Label.HorizontalAlign.CENTER);
                const g = p.node.addComponent(Graphics);
                g.strokeColor = new Color(166, 92, 76, 120);
                g.lineWidth = 1;
                g.moveTo(-w / 2 + 32, -h / 2); g.lineTo(-w / 2 + 32, h / 2);
                g.moveTo(w / 2 - 32, -h / 2); g.lineTo(w / 2 - 32, h / 2);
                g.moveTo(-w / 2, -h / 2 + 32); g.lineTo(w / 2, -h / 2 + 32);
                g.moveTo(-w / 2, h / 2 - 32); g.lineTo(w / 2, h / 2 - 32);
                g.stroke();
            }
            this.label(this.studioRoot, '128px 源 · 32px 切片 · 3× 导出 · 红色虚线为切片边界', 13, C.muted, 0, -150, 1000, 24, Label.HorizontalAlign.CENTER);
        } else if (id === 'spec_icons') {
            this.viewerTitle('图标家族 24 / 32 / 48', 292, 38);
            const names = [
                'icon_talk', 'icon_pickup', 'icon_place', 'icon_view', 'icon_retry', 'icon_sound_off', 'icon_sound_on',
                'icon_menu', 'icon_close', 'icon_arrow', 'icon_continue', 'icon_check', 'icon_lock', 'icon_rotate',
                'icon_pin', 'icon_postcard', 'icon_sparkle', 'icon_leaf', 'icon_info', 'icon_copy', 'icon_restart',
            ];
            for (let i = 0; i < names.length; i++) {
                const c = i % 7, r = Math.floor(i / 7);
                const x = -450 + c * 150, y = 155 - r * 145;
                if (this.iconTextures[names[i]]) this.icon(this.studioRoot, names[i], x, y, 42, C.ink);
                this.label(this.studioRoot, names[i].replace('icon_', ''), 11, C.muted, x, y - 42, 120, 18, Label.HorizontalAlign.CENTER);
            }
        } else {
            this.viewerTitle('PACK001 · 全美术清单与依赖包', 292, 36);
            const p = this.viewerPanel(0, -20, 1000, 480);
            const lines = [
                '47 组逻辑资产 · 0 缺项 · 47 组引擎查看器证据',
                'MAP001 / ENV001–012 / PROP001–006 / MAT001–005 / LOOK001',
                'CHAR001–005 · UI001–013（41 状态）· FX001–003',
                '源：Blender .blend/.glb · Spine 1015 · SVG/TTF · 原生 Cocos 场景',
                '构建：Cocos Creator 3.8.8 · web-desktop 1280×720',
                '门禁：逐项 review 绑定引擎预览 · 独立审核/控制器签认待外部完成',
            ];
            for (let i = 0; i < lines.length; i++) {
                this.label(p.node, lines[i], i === 0 ? 18 : 15, i === 0 ? C.ink : C.inkBody,
                    0, 170 - i * 52, 900, 30, Label.HorizontalAlign.CENTER);
            }
        }
    }

    private buildViewerOverlay(id: string): void {
        const dim = this.uiNode('ViewerDim', this.studioRoot, 0, 0, DESIGN_W, DESIGN_H);
        const dg = dim.addComponent(Graphics);
        const dimAlpha = id === 'safe_area_landscape' ? 0 : id === 'rotate_notice' ? 210 : 96;
        dg.fillColor = new Color(28, 27, 24, dimAlpha);
        dg.rect(-DESIGN_W / 2, -DESIGN_H / 2, DESIGN_W, DESIGN_H);
        dg.fill();

        if (id.startsWith('title_')) {
            this.viewerPanel(0, 15, 880, 430, new Color(250, 247, 239, 248));
            this.viewerTitle('秋庭来信', 135, 66);
            this.label(this.studioRoot, '沿着秋日的石路，找回三封未寄出的问候。', 19, C.inkBody, 0, 62, 900, 30, Label.HorizontalAlign.CENTER);
            const pressed = id === 'title_pressed';
            const loading = id === 'title_loading';
            this.viewerButton(0, -75, 240, 64, loading ? '正在进入…' : '进入花园', pressed, false);
            if (loading) this.label(this.studioRoot, '正在载入场景资源 · 62%', 14, C.muted, 0, -140, 600, 24, Label.HorizontalAlign.CENTER);
        } else if (id.startsWith('loading_')) {
            const fail = id !== 'loading_progress';
            const p = this.viewerPanel(0, 0, 640, 350);
            this.label(p.node, fail ? '关键资源加载失败' : '正在载入秋庭', 30, fail ? new Color(150, 70, 56, 255) : C.ink, 0, 125, 560, 42, Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
            if (fail) {
                this.label(p.node, 'ENV02 · 主树与花坛', 16, C.inkBody, 0, 70, 520, 26, Label.HorizontalAlign.CENTER);
                this.label(p.node, '请求超时 12s', 14, C.muted, 0, 38, 520, 24, Label.HorizontalAlign.CENTER);
                this.viewerButton(0, -40, 220, 54, '重试', id === 'loading_retry_pressed', true, 'icon_retry');
                this.label(p.node, '复制错误摘要', 13, C.muted, 0, -100, 300, 22, Label.HorizontalAlign.CENTER);
            } else {
                this.label(p.node, '场景资源 · 石路与花坛', 15, C.inkBody, 0, 62, 520, 24, Label.HorizontalAlign.CENTER);
                this.label(p.node, '角色骨骼 · 1015_aglna2', 15, C.inkBody, 0, 30, 520, 24, Label.HorizontalAlign.CENTER);
                this.label(p.node, '界面 · Noto Sans / Serif', 15, C.inkBody, 0, -2, 520, 24, Label.HorizontalAlign.CENTER);
                const bar = this.uiNode('ProgressBar', p.node, 0, -60, 480, 14);
                const bg = bar.addComponent(Graphics);
                bg.fillColor = new Color(210, 204, 191, 255); bg.roundRect(-240, -7, 480, 14, 7); bg.fill();
                bg.fillColor = C.mintDeep; bg.roundRect(-240, -7, 298, 14, 7); bg.fill();
                this.label(p.node, '62%', 22, C.ink, 0, -100, 120, 28, Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
                this.label(p.node, '首次载入约需几秒，请保持横屏', 12, C.muted, 0, -140, 500, 22, Label.HorizontalAlign.CENTER);
            }
        } else if (id.startsWith('pause_')) {
            const p = this.viewerPanel(0, 0, 480, 420);
            this.viewerTitleOn(p.node, '暂停', 150, 38);
            this.viewerButtonOn(p.node, 0, 70, 320, 56, '继续游戏', false, false, 'icon_continue');
            const soundOn = id === 'pause_sound_on';
            this.viewerButtonOn(p.node, 0, -5, 320, 56, soundOn ? '声音  开' : '声音  关', false, false, soundOn ? 'icon_sound_on' : 'icon_sound_off');
            this.viewerButtonOn(p.node, 0, -80, 320, 56, '重新开始', id === 'pause_restart_pressed', false, 'icon_restart');
            this.label(p.node, soundOn ? '声音已开启；关闭后不影响任务完成' : '默认静音；可随时打开', 12, C.muted, 0, -145, 380, 20, Label.HorizontalAlign.CENTER);
        } else if (id.startsWith('complete_')) {
            const p = this.viewerPanel(0, 0, 860, 510);
            this.label(p.node, '秋庭来信 · 完成', 34, C.ink, 0, 205, 760, 44, Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
            const cards = ['postcard_bench', 'postcard_flower', 'postcard_pergola'];
            for (let i = 0; i < cards.length; i++) {
                if (this.iconTextures[cards[i]]) this.icon(p.node, cards[i], -180 + i * 180, 95, 128, C.white);
            }
            this.label(p.node, '谢谢你，花园又热闹起来了。', 18, C.inkBody, 0, 5, 700, 28, Label.HorizontalAlign.CENTER);
            this.viewerButtonOn(p.node, -130, -125, 240, 56, '继续漫步', id === 'complete_continue_pressed', false, 'icon_continue');
            this.viewerButtonOn(p.node, 130, -125, 240, 56, '重新开始', false, false, 'icon_restart');
        } else if (id === 'safe_area_landscape') {
            const g = this.uiNode('SafeFrame', this.studioRoot, 0, 0, DESIGN_W, DESIGN_H).addComponent(Graphics);
            g.strokeColor = new Color(216, 170, 88, 230); g.lineWidth = 3;
            g.rect(-640 + 32, -360 + 24, 1280 - 64, 720 - 44); g.stroke();
            g.strokeColor = new Color(159, 216, 200, 220); g.lineWidth = 2;
            g.rect(640 - 32 - 120, 360 - 20 - 56, 120, 56); g.stroke();
            this.label(this.studioRoot, 'SAFE 32 · 20 · 32 · 24', 13, C.goldDeep, 0, 326, 520, 22, Label.HorizontalAlign.CENTER);
            this.label(this.studioRoot, '微信胶囊避让 120×56', 12, C.mintDeep, 640 - 32 - 60, 360 - 20 - 28 - 48, 240, 20, Label.HorizontalAlign.CENTER);
            this.label(this.studioRoot, 'TOUCH ≥48 · 摇杆/交互按钮固定角位', 12, C.muted, 0, -326, 620, 20, Label.HorizontalAlign.CENTER);
            for (const [x, y] of [[-534, -212], [522, -212]]) {
                const t = this.uiNode('TouchTarget', this.studioRoot, x, y, 126, 126).addComponent(Graphics);
                t.strokeColor = new Color(159, 216, 200, 220); t.lineWidth = 2; t.circle(0, 0, 63); t.stroke();
            }
        } else if (id === 'rotate_notice') {
            this.viewerBackdrop(255);
            const p = this.viewerPanel(0, 0, 520, 420);
            if (this.iconTextures['icon_rotate']) this.icon(p.node, 'icon_rotate', 0, 130, 48, C.goldDeep);
            this.label(p.node, '请横屏游玩', 34, C.ink, 0, 55, 420, 44, Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
            this.label(p.node, '横屏后自动继续，当前进度保留。', 16, C.inkBody, 0, 0, 420, 26, Label.HorizontalAlign.CENTER);
            this.label(p.node, '当前 720×1280 · 设计基准 1280×720', 12, C.muted, 0, -90, 420, 20, Label.HorizontalAlign.CENTER);
        }
    }

    private viewerTitleOn(parent: Node, text: string, y: number, size: number): Label {
        return this.label(parent, text, size, C.ink, 0, y, 420, Math.round(size * 1.4),
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
    }

    private viewerButtonOn(parent: Node, x: number, y: number, w: number, h: number, text: string,
        pressed = false, gold = false, iconKey = ''): Node {
        const sprite = this.paperPanel(parent, x, y, w, h, 'Btn_' + text);
        sprite.color = pressed ? new Color(228, 220, 205, 255) : gold ? new Color(248, 238, 218, 255) : new Color(255, 255, 255, 245);
        const node = sprite.node;
        if (pressed) node.setScale(0.97, 0.97, 1);
        this.label(node, text, 19, gold ? C.goldDeep : C.ink, iconKey ? -12 : 0, 0, w - 46, 30, Label.HorizontalAlign.CENTER);
        if (iconKey) this.icon(node, iconKey, w / 2 - 28, 0, 18, gold ? C.goldDeep : C.ink);
        return node;
    }

    private buildViewerNote(id: string): void {
        if (id.startsWith('toast_')) {
            const p = this.viewerPanel(0, 130, 560, 110, new Color(255, 255, 255, 250));
            if (id === 'toast_error') {
                this.label(p.node, '拾取失败', 20, new Color(150, 70, 56, 255), 0, 28, 500, 28, Label.HorizontalAlign.CENTER);
                this.label(p.node, '明信片未能收入信包，请再试一次。· ITEM01', 13, C.muted, 0, -2, 510, 22, Label.HorizontalAlign.CENTER);
                this.viewerButtonOn(p.node, 0, -38, 120, 34, '重试', false, false, 'icon_retry');
            } else if (id === 'toast_task_update') {
                this.label(p.node, '将明信片挂回留言板', 20, C.ink, 0, 28, 500, 28, Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
                this.label(p.node, '任务更新 · 三张已找齐，前往中央广场', 13, C.muted, 0, -4, 510, 22, Label.HorizontalAlign.CENTER);
                this.label(p.node, '3/3', 13, C.mintDeep, 0, -38, 100, 20, Label.HorizontalAlign.CENTER);
            } else {
                this.label(p.node, '找到一张明信片', 20, C.ink, 0, 28, 500, 28, Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
                this.label(p.node, '长椅旁 · 已放入信包', 13, C.muted, 0, -4, 510, 22, Label.HorizontalAlign.CENTER);
                this.label(p.node, '1/3', 13, C.goldDeep, 0, -38, 100, 20, Label.HorizontalAlign.CENTER);
            }
        } else if (id.startsWith('tip_')) {
            const p = this.viewerPanel(0, -230, 520, 180);
            const move = id === 'tip_first_move';
            this.label(p.node, move ? '第一次移动' : '第一次交互', 12, C.goldDeep, 0, 62, 420, 20, Label.HorizontalAlign.CENTER);
            this.label(p.node, move ? '拖动左侧摇杆' : '靠近物件再点按', 22, C.ink, 0, 34, 460, 30, Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
            this.label(p.node, move ? '轻推摇杆行走，松开即停。' : '右侧按钮会显示「交谈」「拾取」或「布置」。', 14, C.inkBody, 0, 0, 470, 24, Label.HorizontalAlign.CENTER);
            this.viewerButtonOn(p.node, 0, -52, 150, 40, '知道了', false, true);
            this.label(p.node, move ? '1 / 2' : '2 / 2', 11, C.muted, 220, 62, 60, 18, Label.HorizontalAlign.CENTER);
        }
    }


    // --------------------------------------------------------- debug / capture

    private focusAsset(id: string): void {
        this.clearViewer();
        this.viewerId = id;
        this.closeDialogue();
        this.setUiVisible(false);
        this.studioActive = false;
        if (this.studioRoot) this.studioRoot.active = false;
        const isChar = id === 'CHAR001' || id === 'CHAR002';
        const isNpc = id === 'CHAR003';
        const isFx = id === 'FX001' || id === 'FX002' || id === 'FX003';
        if (this.spineNode) this.spineNode.active = isChar || id === 'FX001';
        if (this.npcNode) this.npcNode.active = isNpc;
        if (this.fxPickupNode) this.fxPickupNode.active = id === 'FX002';
        if (this.fxBoardNode) this.fxBoardNode.active = id === 'FX003';
        this.presentationScale = isFx ? 1.0 : 1.2;
        if (isChar) {
            this.manualMoving = id === 'CHAR002';
            this.moving = this.manualMoving;
            if (this.spine) {
                this.spine.setAnimation(0, this.manualMoving ? 'Move' : 'Relax', true);
                this.currentAnim = this.manualMoving ? 'Move' : 'Relax';
            }
        }
        if (this.shadowNode) this.shadowNode.active = isChar || id === 'FX001';
        if (this.fxPickupNode) this.fxPickupNode.active = id === 'FX002';
        if (this.fxBoardNode) this.fxBoardNode.active = id === 'FX003';

        const positions: Record<string, [number, number, number]> = {
            MAP001: [0, 0.5, 2], LOOK001: [0, 0.5, 2],
            ENV001: [-4, 0, -4], ENV002: [-2, 0, -9], ENV003: [0, 0, 9.4], ENV004: [-13, 0, -9.9],
            ENV005: [-4.6, 0, -9.05], ENV006: [0, 1.6, 0], ENV007: [0, 0.6, 0], ENV008: [-11.8, 0.3, 4.6],
            ENV009: [-12.4, 0.5, -6.2], ENV010: [-12.3, 0.5, 1], ENV011: [-11.9, 0.4, 2], ENV012: [0.4, 0.1, 2.3],
            PROP001: [-9.3, 0.5, -4.4], PROP002: [11.6, 1.4, 6.4], PROP003: [0, 1.0, 6.9], PROP004: [-6.8, 1.4, -6.8],
            PROP005: [-3.4, 1.0, -7.5], PROP006: [-7, 0.4, -3],
            MAT001: [0, 0.05, -4], MAT002: [-9.3, 0.5, -4.4], MAT003: [6.8, 1.2, -6.8], MAT004: [0, 2.4, 0], MAT005: [0, 1.0, 6.9],
            CHAR001: [0, 0.9, -5.2], CHAR002: [0, 0.9, -5.2], CHAR003: [3, 0.9, -5],
            FX001: [0, 0.25, -5.2], FX002: [-7, 0.6, -3], FX003: [0, 1.2, 6.9],
        };
        if (id === 'PACK001') {
            this.setUiState('pack001');
            return;
        }
        if (id === 'CHAR004' || id === 'CHAR005') {
            this.setUiState(id === 'CHAR004' ? 'dialogue_player_p2' : 'dialogue_gardener_p1');
            return;
        }
        const target = positions[id] || positions.MAP001;
        const cam = this.mainCamera.node;
        if (id === 'MAP001' || id === 'LOOK001') {
            cam.setPosition(0, 28, -28);
            cam.lookAt(new Vec3(0, 0.5, 2));
            this.cameraMode = 'inspect';
        } else if (id === 'CHAR001' || id === 'CHAR002') {
            cam.setPosition(0, 5.2, -12.2);
            cam.lookAt(new Vec3(0, 1.0, -5.2));
            this.cameraMode = 'inspect';
        } else if (id === 'CHAR003') {
            cam.setPosition(3, 4.6, -11.2);
            cam.lookAt(new Vec3(3, 0.9, -5));
        } else if (id === 'FX001') {
            cam.setPosition(0, 2.4, -9.8);
            cam.lookAt(new Vec3(0, 0.25, -5.2));
        } else if (id === 'FX003') {
            cam.setPosition(6.2, 4.2, 2.2);
            cam.lookAt(new Vec3(0, 1.2, 6.9));
        } else if (id === 'PROP003' || id === 'MAT005') {
            cam.setPosition(5.6, 4.3, 2.4);
            cam.lookAt(new Vec3(0, 1.0, 6.9));
        } else if (id === 'ENV003' || id === 'ENV004') {
            cam.setPosition(0, 4.6, 3.2);
            cam.lookAt(new Vec3(0, 0.7, 9.5));
        } else if (id === 'ENV006' || id === 'MAT004') {
            cam.setPosition(6.5, 4.6, -6.0);
            cam.lookAt(new Vec3(0, 1.8, 0));
        } else if (id === 'ENV007') {
            cam.setPosition(4.0, 3.6, -6.0);
            cam.lookAt(new Vec3(0, 0.6, 0));
        } else {
            const x = target[0], z = target[2];
            cam.setPosition(x, 5.0, z - 6.0);
            cam.lookAt(new Vec3(x, target[1], z));
        }
        this.cameraMode = 'inspect';
        console.log('[COURTYARD] focus ' + id + ' camera=' + JSON.stringify([cam.position.x, cam.position.y, cam.position.z]));
    }

    private resetView(): void {
        this.clearViewer();
        this.viewerId = '';
        this.setUiVisible(true);
        if (this.spineNode) this.spineNode.active = true;
        if (this.npcNode) this.npcNode.active = true;
        if (this.shadowNode) this.shadowNode.active = true;
        this.manualMoving = false;
        if (this.spine) {
            this.spine.setAnimation(0, 'Relax', true);
            this.currentAnim = 'Relax';
        }
        const cam = this.mainCamera.node;
        cam.setPosition(-2.5, 11.5, -14.6);
        cam.lookAt(new Vec3(-2.5, 3.5, -3.7));
        this.cameraMode = 'game';
        this.playerPos.set(0, PAVING_TOP, -5.2);
    }

    private exposeCaptureApi(): void {
        const api = {
            version: '1.0.0',
            state: () => ({
                ready: this.assetsReady,
                uiVisible: this.uiVisible,
                dialogueVisible: this.dialogueVisible,
                dialoguePage: this.dialoguePage,
                accepted: this.accepted,
                moving: this.moving,
                paused: this.paused,
                inputLocked: this.inputLocked,
                boardState: this.boardState,
                cameraMode: this.cameraMode,
                anim: this.currentAnim,
                animNames: this.spine && this.spine.skeletonData ? this.getAnimNames() : [],
                player: [this.playerPos.x, this.playerPos.y, this.playerPos.z],
                viewer: this.viewerId,
                loadErrors: this.loadErrors,
                boneBounds: this.spineNativeHeight(),
                metrics: (globalThis as any).__COURTYARD_METRICS__ || null,
                spine: this.spine ? (() => { const u = this.spineNode!.getComponent(UITransform)!; return { width: u.width, height: u.height, premultipliedAlpha: this.spine!.premultipliedAlpha }; })() : null,
            }),
            setUi: (v: boolean) => this.setUiVisible(v),
            setUiState: (id: string) => { this.viewerId = id; this.setUiState(id); },
            focusAsset: (id: string) => { this.focusAsset(id); },
            resetView: () => this.resetView(),
            setPause: (v: boolean) => { if (v) { this.setUiState('pause_default'); } else { this.resetView(); } },
            setBoardState: (v: string) => this.setBoardState(v),
            enableStats: (v: boolean) => { if (v) profiler.showStats(); else profiler.hideStats(); },
            renderStats: () => {
                const s: any = (profiler as any).stats;
                if (!s) return null;
                return {
                    draws: s.draws.counter.value,
                    tris: s.tricount.counter.value,
                    instances: s.instances.counter.value,
                    textureMB: s.textureMemory.counter.value,
                    bufferMB: s.bufferMemory.counter.value,
                    fps: s.fps.counter.value,
                };
            },
            setCameraMode: (v: string) => {
                this.cameraMode = v === 'inspect' ? 'inspect' : 'game';
                if (this.cameraMode === 'inspect') {
                    const cam = this.mainCamera.node;
                    cam.setPosition(0, 28, -28);
                    cam.lookAt(new Vec3(0, 0.5, 2));
                }
            },
            openDialogue: (p = 1) => this.openDialogue(p),
            closeDialogue: () => this.closeDialogue(),
            setPlayer: (x: number, z: number) => { this.playerPos.x = x; this.playerPos.z = z; },
            setMoving: (v: boolean) => { this.manualMoving = v; this.moving = v; },
            reset: () => {
                this.accepted = false;
                this.questTitle.string = '和园丁聊聊';
                this.questSub.string = '园丁就在南入口的路石旁';
                this.questBadge.string = '待接取';
                this.setUiVisible(true);
                this.closeDialogue();
                this.manualMoving = false;
                this.playerPos.set(0, PAVING_TOP, -5.2);
            },
        };
        (globalThis as any).__courtyard = api;
    }

    private getAnimNames(): string[] {
        if (!this.spine || !this.spine.skeletonData) return [];
        const data: any = this.spine.skeletonData;
        try {
            const json = data.skeletonJson || data._skeletonJson;
            if (json && json.animations) return Object.keys(json.animations);
        } catch (e) { /* ignore */ }
        return [];
    }

    start(): void {
        this.exposeCaptureApi();
        console.log('[COURTYARD] BOOTSTRAP_OK version=1.0.0');
    }
}
