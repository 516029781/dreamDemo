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
const RT_LAYER = 1 << 19;
Layers.addLayer('UI_RT', 19);

// DEMO_EXECUTION_SPEC §5: BOOT→TITLE→PLAYING with DIALOGUE/PAUSE/COMPLETE_PANEL
// overlays; the quest walks NOT_STARTED → COLLECTING → READY → DONE.
type QuestState = 'NOT_STARTED' | 'COLLECTING' | 'READY' | 'DONE';

interface QuestTarget {
    id: string;
    kind: 'gardener' | 'postcard' | 'board';
    x: number;
    z: number;
    /** texture key in iconTextures for postcard world props */
    tex?: string;
}

const QUEST_INTERACT_DIST = 1.6;


const C = {
    paper: new Color(243, 240, 230, 255),
    paperHigh: new Color(250, 248, 241, 255),
    ink: new Color(46, 50, 52, 255),
    inkBody: new Color(42, 46, 46, 255),
    muted: new Color(78, 81, 76, 255),
    faint: new Color(116, 118, 110, 255),
    mint: new Color(159, 216, 200, 255),
    mintDeep: new Color(79, 138, 121, 255),
    // W1 typography: the 13-16 px meta lines used mintDeep on warm paper and read
    // as washed out. This keeps the same hue family at a legible contrast.
    meta: new Color(56, 100, 88, 255),
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
    // n5 batch 0: same world, two framings. A is the n4 formal camera; B is a
    // flatter, slightly further framing that trades paving area for background
    // depth. Captured from one build so the A/B costs no extra Cocos run.
    private static readonly CAMERA_PRESETS: Record<string, { pos: number[]; look: number[]; fov: number }> = {
        A: { pos: [-2.5, 11.5, -14.6], look: [-2.5, 3.5, -3.7], fov: 37.5 },
        B: { pos: [-2.5, 9.8, -15.4], look: [-2.5, 4.6, -3.7], fov: 36.0 },
    };
    private cameraPreset = 'A';
    // Dialogue framing: pitch the follow camera down so the player's feet land
    // above the dialogue panel instead of behind it (n5 P1-2 / layout_air).
    private dialogueCamera = false;
    private static readonly DIALOGUE_LOOK_Y = 1.7;
    private scrim: Node = null!;
    private dialogueRoot: Node = null!;
    private pauseRoot: Node | null = null;

    private playerAnchor: Node = null!;
    private spineNode: Node | null = null;
    private spine: sp.Skeleton | null = null;
    private shadowNode: Node | null = null;
    private paperFrame: SpriteFrame | null = null;
    private shadowMaterial: Material | null = null;
    private shadowTexture: Texture2D | null = null;
    private npcShadowMaterial: Material | null = null;

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
    private prePortraitState: any = null;
    private dialogueVisible = false;
    private uiVisible = true;
    private portraitBlocked = false;
    private currentAnim = '';

    // ------------------------------------------------------------- quest data
    // G01: one data source for the whole demo. HUD text, the action button, the
    // board cards and the world postcards are all derived from these three
    // fields; nothing may write questTitle/questSub directly any more.
    private questState: QuestState = 'NOT_STARTED';
    private collectedIds: Set<string> = new Set();
    private submittedOnce = false;
    private questFocusId: string | null = null;
    private gardenerLine: string | null = null;
    private postcardNodes = new Map<string, Node>();
    private toastLabel: Label | null = null;
    private toastNode: Node | null = null;
    private toastUntil = 0;
    private completeRoot: Node | null = null;
    private lastFocusKey = '';
    private boardManual = false;
    private billboardExtras: Node[] = [];
    private pauseSoundLabel: Label | null = null;
    private pauseSoundIcon: Sprite | null = null;

    /** Stable interaction candidates. Tie-breaks use array order, never distance
     * noise, so two objects at the same distance always resolve the same way. */
    private readonly questTargets: QuestTarget[] = [
        { id: 'gardener', kind: 'gardener', x: 3.0, z: -5.0 },
        { id: 'card_bench', kind: 'postcard', x: -8.4, z: -5.2, tex: 'postcard_bench' },
        { id: 'card_flower', kind: 'postcard', x: 5.2, z: -6.4, tex: 'postcard_flower' },
        { id: 'card_pergola', kind: 'postcard', x: 6.2, z: 6.2, tex: 'postcard_pergola' },
        { id: 'board', kind: 'board', x: 0, z: 6.9 },
    ];

    private loadErrors: string[] = [];
    private pendingLoads = 0;
    private assetsReady = false;
    /** G-harness: bumped every update() so tests can await real frames. */
    private frameTick = 0;

    onLoad(): void {
        profiler.hideStats();
        view.setDesignResolutionSize(DESIGN_W, DESIGN_H, ResolutionPolicy.SHOW_ALL);
        this.setupCamera();
        this.setupLights();
        this.setupWorldAnchors();
        this.setupInput();
        this.buildLoadingOverlay();
        this.setupLifecycle();
        this.loadAssets();
        console.log('[COURTYARD] onLoad complete; loading native assets');
    }

    /** G07: real progress, not a fake 62%. Local-first per spec §5.
     * Owns a Canvas + UI camera because it must render before setupUI builds
     * the main canvas (the 3D camera only renders the DEFAULT layer). */
    private buildLoadingOverlay(): void {
        const root = new Node('LoadingRoot');
        root.layer = Layers.Enum.UI_2D;
        root.parent = director.getScene()!;
        const ut = root.addComponent(UITransform);
        ut.setContentSize(DESIGN_W, DESIGN_H);
        const canvas = root.addComponent(Canvas);
        const camNode = new Node('LoadingCamera');
        camNode.layer = Layers.Enum.UI_2D;
        camNode.parent = root;
        camNode.setPosition(0, 0, 1000);
        const cam = camNode.addComponent(Camera);
        cam.projection = Camera.ProjectionType.ORTHO;
        cam.orthoHeight = DESIGN_H / 2;
        cam.near = 0.1;
        cam.far = 2000;
        cam.clearFlags = Camera.ClearFlag.SOLID_COLOR;
        cam.clearColor = new Color(0, 0, 0, 0);
        cam.visibility = Layers.Enum.UI_2D;
        cam.priority = 100;
        canvas.cameraComponent = cam;

        const bg = root.addComponent(Graphics);
        bg.fillColor = new Color(215, 206, 188, 255);
        bg.rect(-DESIGN_W / 2, -DESIGN_H / 2, DESIGN_W, DESIGN_H);
        bg.fill();
        this.label(root, '秋庭来信', 40, C.ink, 0, 96, 420, 52,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        this.label(root, '正在载入场景资源', 16, C.inkBody, 0, 30, 420, 24,
            Label.HorizontalAlign.CENTER);
        const barW = 360;
        this.loadingBarW = barW;
        const track = root.addComponent(Graphics);
        track.fillColor = new Color(196, 186, 165, 255);
        track.roundRect(-barW / 2, -24, barW, 12, 6);
        track.fill();
        const fillNode = this.uiNode('LoadingFill', root, 0, 0, barW, 12);
        this.loadingBarFill = fillNode.addComponent(Graphics);
        this.loadingStageLabel = this.label(root, '准备中', 13, C.meta, 0, -58, 460, 20,
            Label.HorizontalAlign.CENTER);
        root.active = true;
        this.loadingRoot = root;
    }

    private updateLoadingProgress(): void {
        if (!this.loadingRoot || !this.loadingBarFill) return;
        const pct = this.totalLoads > 0 ? this.doneLoads / this.totalLoads : 0;
        const g = this.loadingBarFill;
        g.clear();
        if (pct > 0) {
            g.fillColor = new Color(79, 138, 121, 255);
            g.roundRect(-this.loadingBarW / 2, -24, Math.max(12, this.loadingBarW * pct), 12, 6);
            g.fill();
        }
        if (this.loadingBarLabel === null && this.loadingStageLabel) {
            // one numeric label next to the stage text, created lazily
            this.loadingBarLabel = this.label(this.loadingRoot,
                Math.round(pct * 100) + '%', 14, C.inkBody, 0, -2, 80, 22,
                Label.HorizontalAlign.CENTER);
        }
        if (this.loadingBarLabel) this.loadingBarLabel.string = Math.round(pct * 100) + '%';
        if (this.loadingStageLabel) {
            const n = this.pendingLoads;
            this.loadingStageLabel.string = n > 0 ? '还剩 ' + n + ' 项资源' : '即将完成';
        }
    }

    private hideLoadingOverlay(): void {
        if (this.loadingRoot) this.loadingRoot.active = false;
    }

    /** G07: failure card with a copyable error summary and a real retry. */
    private showRetryCard(): void {
        if (this.retryRoot) {
            this.retryRoot.active = true;
            return;
        }
        const root = new Node('RetryRoot');
        root.layer = Layers.Enum.UI_2D;
        root.parent = director.getScene()!;
        const ut = root.addComponent(UITransform);
        ut.setContentSize(DESIGN_W, DESIGN_H);
        const canvas = root.addComponent(Canvas);
        const camNode = new Node('RetryCamera');
        camNode.layer = Layers.Enum.UI_2D;
        camNode.parent = root;
        camNode.setPosition(0, 0, 1000);
        const cam = camNode.addComponent(Camera);
        cam.projection = Camera.ProjectionType.ORTHO;
        cam.orthoHeight = DESIGN_H / 2;
        cam.near = 0.1;
        cam.far = 2000;
        cam.clearFlags = Camera.ClearFlag.SOLID_COLOR;
        cam.clearColor = new Color(0, 0, 0, 0);
        cam.visibility = Layers.Enum.UI_2D;
        cam.priority = 101;
        canvas.cameraComponent = cam;
        const bg = root.addComponent(Graphics);
        bg.fillColor = new Color(215, 206, 188, 255);
        bg.rect(-DESIGN_W / 2, -DESIGN_H / 2, DESIGN_W, DESIGN_H);
        bg.fill();
        this.label(root, '载入失败', 34, C.ink, 0, 150, 420, 44,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        this.label(root, '关键资源没有加载成功，可以重试。', 16, C.inkBody, 0, 96, 520, 24,
            Label.HorizontalAlign.CENTER);
        // Copyable summary: the raw first errors, monospace-ish small text.
        const summary = (this.loadErrors.length ? this.loadErrors : ['未知错误']).slice(0, 4).join('\n');
        this.retryErrorLabel = this.label(root, summary, 12, C.muted, 0, 8, 760, 120,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER);
        const copy = this.uiNode('RetryCopy', root, 0, -76, 240, 46);
        const cp = copy.addComponent(Sprite);
        cp.sizeMode = Sprite.SizeMode.CUSTOM;
        cp.type = Sprite.Type.SLICED;
        cp.color = new Color(255, 255, 255, 230);
        const cf = this.makeSlicedFrame(240, 46);
        if (cf) cp.spriteFrame = cf;
        this.paperSprites.push(cp);
        this.label(copy, '复制错误摘要', 16, C.ink, -14, 0, 170, 24,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER);
        this.icon(copy, 'icon_copy', 84, 0, 18, C.ink);
        copy.on(Node.EventType.TOUCH_END, () => this.copyErrorSummary());
        const retry = this.uiNode('RetryGo', root, 0, -148, 240, 46);
        const rp = retry.addComponent(Sprite);
        rp.sizeMode = Sprite.SizeMode.CUSTOM;
        rp.type = Sprite.Type.SLICED;
        rp.color = new Color(248, 235, 210, 250);
        const rf = this.makeSlicedFrame(240, 46);
        if (rf) rp.spriteFrame = rf;
        this.paperSprites.push(rp);
        this.label(retry, '重试', 17, C.ink, -14, 0, 170, 24,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER);
        this.icon(retry, 'icon_retry', 84, 0, 18, C.ink);
        retry.on(Node.EventType.TOUCH_END, () => this.retryFailedLoads());
        root.active = true;
        this.retryRoot = root;
        console.log('[COURTYARD] retry card shown errors=' + this.loadErrors.length);
    }

    /** WeChat keeps its own clipboard API; the web falls back to navigator.
     * Runs before the HUD exists, so confirmation goes on the card itself. */
    private copyErrorSummary(): void {
        const text = this.loadErrors.join('\n');
        let ok = false;
        try {
            const wxa = (globalThis as any).wx;
            if (wxa && wxa.setClipboardData) {
                wxa.setClipboardData({ data: text });
                ok = true;
            }
        } catch (e) { /* web path below */ }
        if (!ok && typeof navigator !== 'undefined' && navigator.clipboard) {
            try {
                navigator.clipboard.writeText(text);
                ok = true;
            } catch (e) { /* clipboard unavailable: text stays on the card */ }
        }
        const btn = this.retryRoot ? this.retryRoot.getChildByName('RetryCopy') : null;
        if (btn) {
            const l = btn.getComponentInChildren(Label);
            if (l) l.string = ok ? '已复制' : '请手动抄录';
        }
    }

    private retryFailedLoads(): void {
        if (this.failedLoads.length === 0) {
            console.log('[COURTYARD] retry: nothing failed, re-running maybeFinish');
            this.maybeFinish();
            return;
        }
        const again = this.failedLoads.slice();
        this.failedLoads.length = 0;
        for (const f of again) {
            this.pendingLoads++;
            this.totalLoads++;
            resources.load(f.path, f.type, (err: any, asset: any) => {
                if (err || !asset) {
                    const message = '[COURTYARD] load failed: ' + f.path + ' :: ' + (err ? err.message || err : 'null');
                    console.warn(message);
                    this.loadErrors.push(message);
                    this.failedLoads.push({ path: f.path, type: f.type, cb: f.cb });
                } else {
                    f.cb(err, asset);
                }
                this.pendingLoads--;
                this.doneLoads++;
                this.updateLoadingProgress();
                // assetsReady is still false here, so this re-evaluates the gate
                this.maybeFinish();
            });
        }
        if (this.retryRoot) this.retryRoot.active = false;
        if (this.loadingRoot) this.loadingRoot.active = true;
        this.updateLoadingProgress();
        console.log('[COURTYARD] retrying ' + again.length + ' failed loads');
    }

    /** G06: WeChat onHide/onShow plus a web visibilitychange fallback.
     * Background: zero the joystick, drop touches, pause. Return: stay paused
     * with progress intact — the player resumes deliberately. */
    private setupLifecycle(): void {
        const onHide = () => {
            this.joy.set(0, 0);
            this.keys.clear();
            this.manualMoving = false;
            this.moving = false;
            this.resetJoystick();
            if (!this.paused) this.setPause(true);
            console.log('[COURTYARD] lifecycle hide -> paused, input cleared');
        };
        const onShow = () => {
            // dt spikes after backgrounding are already clamped (Math.min(dt, 0.05));
            // the pause card waits for an explicit 继续游戏.
            console.log('[COURTYARD] lifecycle show -> still paused=' + this.paused);
        };
        try {
            const wxa = (globalThis as any).wx;
            if (wxa && wxa.onHide && wxa.onShow) {
                wxa.onHide(onHide);
                wxa.onShow(onShow);
                console.log('[COURTYARD] lifecycle wired via wx');
                return;
            }
        } catch (e) { /* web path below */ }
        if (typeof document !== 'undefined' && document.addEventListener) {
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) onHide();
                else onShow();
            });
            console.log('[COURTYARD] lifecycle wired via visibilitychange');
        }
    }

    // ------------------------------------------------------------------ scene

    private setupCamera(): void {
        const scene = director.getScene()!;
        const camNode = scene.getChildByName('Main Camera')!;
        const cam = camNode.getComponent(Camera)!;
        this.mainCamera = cam;
        this.applyCameraPreset(this.cameraPreset);
        cam.near = 0.1;
        cam.far = 120;
        cam.clearFlags = Camera.ClearFlag.SOLID_COLOR;
        cam.clearColor = hexToColor('#D7CEBC');
        cam.visibility = Layers.Enum.DEFAULT;

        const globals = scene.globals;
        globals.skybox.enabled = false;
        globals.ambient.skyColor = new Vec4(0.62, 0.69, 0.73, 1);
        globals.ambient.skyIllum = 12500;
        globals.ambient.groundLightingColor = new Color(158, 124, 88, 255);
        // n5: fog closes the exposed horizon behind the treeline and gives the
        // far layers the same aerial recession the haze palette is aiming at.
        // It starts past the player's depth (~14) so the character is untouched.
        globals.fog.enabled = true;
        globals.fog.type = 0;
        globals.fog.fogColor = new Color(201, 194, 176, 255);
        globals.fog.fogStart = 26;
        globals.fog.fogEnd = 72;
        globals.fog.accurate = false;
        globals.shadows.enabled = true;
        (globals.shadows as any).type = 0; // ShadowMap
        globals.shadows.shadowMapSize = 4096;
        globals.shadows.maxReceived = 4;

        console.log('[COURTYARD] camera ready preset=' + this.cameraPreset + ' fov=' + cam.fov);
    }

    private applyCameraPreset(name: string): void {
        const table = CourtyardBootstrap.CAMERA_PRESETS;
        const key = name in table ? name : 'A';
        const p = table[key];
        this.cameraPreset = key;
        const camNode = this.mainCamera.node;
        camNode.setPosition(p.pos[0], p.pos[1], p.pos[2]);
        camNode.lookAt(new Vec3(p.look[0], p.look[1], p.look[2]));
        this.mainCamera.fov = p.fov;
    }

    private setupLights(): void {
        const scene = director.getScene()!;
        const keyNode = scene.getChildByName('Main Light')!;
        // Lower, side-er sun than n4a so props throw a readable raked shadow
        // instead of sitting in a flat pool directly under themselves.
        keyNode.setRotationFromEuler(-41, -58, 0);
        const key = keyNode.getComponent(DirectionalLight)!;
        key.color = hexToColor('#FFCC96');
        key.illuminance = 112000;
        key.shadowEnabled = true;
        (key as any).shadowPcf = 3; // SOFT_4X: dappled, not ink-sharp
        (key as any).shadowBias = 0.00016;
        (key as any).shadowNormalBias = 0.32;
        (key as any).shadowDistance = 38;
        (key as any).shadowSaturation = 0.42;

        const fillNode = new Node('Fill Light');
        fillNode.parent = scene;
        fillNode.setRotationFromEuler(-24, 148, 0);
        const fill = fillNode.addComponent(DirectionalLight);
        fill.color = hexToColor('#A9C2D6');
        fill.illuminance = 11000;
        fill.shadowEnabled = false;

        // Warm front bounce: lifts benches, planter rims and the character
        // without adding another shadow-casting light.
        const bounceNode = new Node('Bounce Light');
        bounceNode.parent = scene;
        bounceNode.setRotationFromEuler(-16, 24, 0);
        const bounce = bounceNode.addComponent(DirectionalLight);
        bounce.color = hexToColor('#FFC58E');
        bounce.illuminance = 7000;
        bounce.shadowEnabled = false;

        // Frontal warm lift for the dense hedge face; the key is behind it.
        const hedgeFillNode = new Node('Hedge Fill');
        hedgeFillNode.parent = scene;
        hedgeFillNode.setRotationFromEuler(-24, 0, 0);
        const hedgeFill = hedgeFillNode.addComponent(DirectionalLight);
        hedgeFill.color = hexToColor('#FFD7AC');
        hedgeFill.illuminance = 6400;
        hedgeFill.shadowEnabled = false;

        // Cool-warm back rim separates the hedge and tree from the cream sky.
        const rimNode = new Node('Back Rim');
        rimNode.parent = scene;
        rimNode.setRotationFromEuler(-22, 168, 0);
        const rim = rimNode.addComponent(DirectionalLight);
        rim.color = hexToColor('#FFE0B4');
        rim.illuminance = 10500;
        rim.shadowEnabled = false;
        console.log('[COURTYARD] lights ready key warm + cool fill + warm bounce + rim');
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
            // Leaf-card shadows read as ink splatter at this scale. Only
            // structural solids (bark, stone, wood, metal) cast; the soft
            // dappled tree decal carries foliage shade.
            const low = n.toLowerCase();
            const shadowOff = low.includes('leaf') || low.includes('leaves')
                || low.includes('canopy') || low.includes('crown')
                || low.includes('tree_bark')
                || low.includes('hedge') || low.includes('treeline')
                || low.includes('cards') || low.includes('moss')
                || low.includes('grass') || low.includes('flower')
                || low.includes('shrub') || low.includes('clump')
                || low.includes('petal') || low.includes('litter')
                || low.includes('ring_cover');
            mr.shadowCastingMode = (flat || lightCaster || shadowOff) ? MeshRenderer.ShadowCastingMode.OFF : MeshRenderer.ShadowCastingMode.ON;
        }
        for (const key of ['A', 'B', 'C']) {
            const card = this.findNode(map, 'MAP001_message_board_card_' + key);
            if (card) this.cardNodes.push(card);
        }
        // G01: the quest machine owns board visibility (the cards start blown
        // off), so do not pin the manual override here.
        this.boardManual = false;
        this.refreshQuestHud();
        this.applyMaterialOverrides(map);
        console.log('[COURTYARD] full MAP001 instantiated renderers=' + renderers.length + ' cards=' + this.cardNodes.length);
    }

    // V02 material separation: procedural texture sources in
    // art/full/source/textures/ (tools/textures/make_procedural_textures.py)
    // + world-space box UVs baked in build_map001.py. Palette tints carry the
    // color; textures carry pattern; roughness/metallic separate families.
    private static readonly MAT_OVERRIDES: Record<string, { tex: string; color: string; rough: number; metal: number }> = {
        ENG_MAT_stone_base: { tex: 'textures/tex_stone_tiles/texture', color: '#B2A68F', rough: 0.90, metal: 0.0 },
        ENG_MAT_stone_light: { tex: 'textures/tex_stone_tiles/texture', color: '#C6BBA4', rough: 0.86, metal: 0.0 },
        ENG_MAT_stone_dark: { tex: 'textures/tex_stone_tiles/texture', color: '#8A7F6A', rough: 0.94, metal: 0.0 },
        ENG_MAT_mortar: { tex: 'textures/tex_stone_tiles/texture', color: '#786F5F', rough: 0.96, metal: 0.0 },
        ENG_MAT_ground_soil: { tex: 'textures/tex_soil_noise/texture', color: '#6B5B47', rough: 0.98, metal: 0.0 },
        ENG_MAT_soil: { tex: 'textures/tex_soil_noise/texture', color: '#5F4B37', rough: 0.98, metal: 0.0 },
        ENG_MAT_wood_dark: { tex: 'textures/tex_wood_grain/texture', color: '#5C4733', rough: 0.72, metal: 0.0 },
        ENG_MAT_wood_old: { tex: 'textures/tex_wood_grain/texture', color: '#7C6146', rough: 0.66, metal: 0.0 },
        ENG_MAT_bench_wood: { tex: 'textures/tex_wood_grain/texture', color: '#7A5B3D', rough: 0.62, metal: 0.0 },
        ENG_MAT_bench_metal: { tex: 'textures/tex_metal_brushed/texture', color: '#3F4145', rough: 0.34, metal: 0.88 },
        ENG_MAT_metal_iron: { tex: 'textures/tex_metal_brushed/texture', color: '#3F4145', rough: 0.36, metal: 0.90 },
        ENG_MAT_metal_brass: { tex: 'textures/tex_metal_brushed/texture', color: '#A9834B', rough: 0.35, metal: 0.85 },
        ENG_MAT_metal_rust: { tex: 'textures/tex_metal_brushed/texture', color: '#72513D', rough: 0.85, metal: 0.30 },
        ENG_MAT_leaf_ochre: { tex: 'textures/tex_leaf_detail/texture', color: '#DDB35A', rough: 0.58, metal: 0.0 },
        ENG_MAT_leaf_amber: { tex: 'textures/tex_leaf_detail/texture', color: '#C9823F', rough: 0.60, metal: 0.0 },
        ENG_MAT_leaf_olive: { tex: 'textures/tex_leaf_detail/texture', color: '#7E8F4C', rough: 0.62, metal: 0.0 },
        ENG_MAT_leaf_deep: { tex: 'textures/tex_leaf_detail/texture', color: '#7B6B3A', rough: 0.62, metal: 0.0 },
        ENG_MAT_leaf_gold: { tex: 'textures/tex_leaf_detail/texture', color: '#E0C068', rough: 0.54, metal: 0.0 },
        ENG_MAT_leaf_mass: { tex: 'textures/tex_leaf_detail/texture', color: '#514A2C', rough: 0.82, metal: 0.0 },
        ENG_MAT_leaf_far: { tex: 'textures/tex_leaf_detail/texture', color: '#68705E', rough: 0.70, metal: 0.0 },
        ENG_MAT_leaf_mid_haze: { tex: 'textures/tex_leaf_detail/texture', color: '#8A8F74', rough: 0.74, metal: 0.0 },
        ENG_MAT_leaf_haze: { tex: 'textures/tex_leaf_detail/texture', color: '#A3A78F', rough: 0.78, metal: 0.0 },
        ENG_MAT_grass_dry: { tex: 'textures/tex_leaf_detail/texture', color: '#C3AD72', rough: 0.72, metal: 0.0 },
        ENG_MAT_grass_pale: { tex: 'textures/tex_leaf_detail/texture', color: '#DCC991', rough: 0.70, metal: 0.0 },
        ENG_MAT_roof_tile: { tex: 'textures/tex_stone_tiles/texture', color: '#8C5B48', rough: 0.82, metal: 0.0 },
        ENG_MAT_flower_rose: { tex: 'textures/tex_leaf_detail/texture', color: '#D98F9B', rough: 0.62, metal: 0.0 },
        ENG_MAT_flower_cream: { tex: 'textures/tex_leaf_detail/texture', color: '#EFE2C6', rough: 0.60, metal: 0.0 },
    };

    private applyMaterialOverrides(map: Node): void {
        const renderers = map.getComponentsInChildren(MeshRenderer);
        const texPaths = Array.from(new Set(Object.values(CourtyardBootstrap.MAT_OVERRIDES).map(o => o.tex)));
        texPaths.push('textures/tex_bark/texture');
        texPaths.push('textures/tex_leaf_detail/texture');
        const texMap: Record<string, Texture2D> = {};
        let pending = texPaths.length;
        for (const p of texPaths) {
            resources.load(p, Texture2D, (err: any, tex: Texture2D) => {
                if (err) console.warn('[MAT] texture load failed ' + p + ' ' + err);
                else {
                    tex.setWrapMode(Texture2D.WrapMode.REPEAT, Texture2D.WrapMode.REPEAT);
                    texMap[p] = tex;
                }
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
                if (!isBark) {
                    const kind = this.surfaceKind(name);
                    const maps = this.surfaceMaps(kind);
                    if (maps) {
                        m.setProperty('normalMap', maps.normal);
                        m.setProperty('pbrMap', maps.pbr);
                        m.setProperty('normalStrength', kind === 'stone' ? 0.55 : kind === 'wood' ? 0.70 : kind === 'metal' ? 0.35 : 0.45);
                        m.setProperty('occlusion', kind === 'soil' ? 0.90 : 0.95);
                        m.recompileShaders({ USE_NORMAL_MAP: true, USE_PBR_MAP: true });
                    }
                }
                mr.setMaterial(m, i);
                replaced += 1;
            }
        }
        console.log('[MAT] overrides applied replaced=' + replaced + ' unknown=[' + Array.from(unknown).join(',') + ']');
    }

    private surfaceCache: Record<string, { normal: Texture2D; pbr: Texture2D }> = {};

    private surfaceKind(name: string): string {
        const n = name.toLowerCase();
        if (n.indexOf('stone') >= 0 || n.indexOf('mortar') >= 0 || n.indexOf('paving') >= 0) return 'stone';
        if (n.indexOf('wood') >= 0 || n.indexOf('bench') >= 0) return 'wood';
        if (n.indexOf('metal') >= 0) return 'metal';
        if (n.indexOf('soil') >= 0 || n.indexOf('ground') >= 0) return 'soil';
        return '';
    }

    private hash2(x: number, y: number): number {
        const v = Math.sin(x * 127.1 + y * 311.7) * 43758.5453123;
        return v - Math.floor(v);
    }

    private valueNoise(x: number, y: number): number {
        const xi = Math.floor(x), yi = Math.floor(y);
        const xf = x - xi, yf = y - yi;
        const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
        const a = this.hash2(xi, yi), b = this.hash2(xi + 1, yi);
        const c = this.hash2(xi, yi + 1), d = this.hash2(xi + 1, yi + 1);
        return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v;
    }

    private fbm(x: number, y: number, octaves = 4): number {
        let sum = 0, amp = 0.55, freq = 1;
        for (let i = 0; i < octaves; i++) {
            sum += amp * this.valueNoise(x * freq, y * freq);
            freq *= 2.03;
            amp *= 0.5;
        }
        return sum;
    }

    private surfaceHeight(kind: string, x: number, y: number): number {
        if (kind === 'stone') {
            const gx = Math.abs(((x * 4) % 1) - 0.5);
            const gy = Math.abs(((y * 4) % 1) - 0.5);
            const grout = Math.min(gx, gy) < 0.045 ? -0.22 : 0;
            const chip = Math.max(0, this.fbm(x * 26, y * 26, 3) - 0.74) * 0.10;
            return 0.56 + 0.13 * this.fbm(x * 7, y * 7) + 0.04 * this.fbm(x * 31, y * 31, 3) + grout - chip;
        }
        if (kind === 'wood') {
            const warp = 0.09 * Math.sin(2 * Math.PI * (y * 2.0 + 0.35 * Math.sin(2 * Math.PI * x)));
            const grain = Math.sin(2 * Math.PI * (y * 9 + warp));
            const knot = Math.exp(-((x - 0.68) ** 2 + (y - 0.30) ** 2) / 0.002) * 0.3;
            return 0.56 + 0.15 * grain + 0.10 * this.fbm(x * 4, y * 18, 3) - knot;
        }
        if (kind === 'metal') {
            return 0.56 + 0.055 * Math.sin(x * Math.PI * 46) + 0.05 * this.fbm(x * 32, y * 2, 3);
        }
        if (kind === 'soil') {
            return 0.50 + 0.30 * this.fbm(x * 7, y * 7) + 0.10 * this.fbm(x * 27, y * 27, 3);
        }
        return 0.56 + 0.12 * this.fbm(x * 9, y * 9);
    }

    private makeSurfaceTexture(kind: string, normal: boolean): Texture2D {
        const size = 512;
        const data = new Uint8Array(size * size * 4);
        const strength = kind === 'stone' ? 2.4 : kind === 'wood' ? 1.8 : kind === 'metal' ? 1.0 : 2.0;
        for (let y = 0; y < size; y++) {
            for (let x = 0; x < size; x++) {
                const u = x / size, v = y / size;
                const i = (y * size + x) * 4;
                if (normal) {
                    const eps = 1 / size;
                    const hl = this.surfaceHeight(kind, (x - 1) / size, v);
                    const hr = this.surfaceHeight(kind, (x + 1) / size, v);
                    const hd = this.surfaceHeight(kind, u, (y - 1) / size);
                    const hu = this.surfaceHeight(kind, u, (y + 1) / size);
                    let nx = (hl - hr) * strength, ny = (hd - hu) * strength, nz = 1;
                    const len = Math.sqrt(nx * nx + ny * ny + nz * nz);
                    nx /= len; ny /= len; nz /= len;
                    data[i] = Math.round((nx * 0.5 + 0.5) * 255);
                    data[i + 1] = Math.round((ny * 0.5 + 0.5) * 255);
                    data[i + 2] = Math.round((nz * 0.5 + 0.5) * 255);
                    data[i + 3] = 255;
                } else {
                    const h = this.surfaceHeight(kind, u, v);
                    const occ = Math.max(0.58, Math.min(1.0, 0.64 + h * 0.48));
                    const roughVar = 0.72 + 0.28 * this.fbm(u * 12, v * 12, 2);
                    const metal = kind === 'metal' ? 1.0 : 0.0;
                    data[i] = Math.round(occ * 255);
                    data[i + 1] = Math.round(roughVar * 255);
                    data[i + 2] = Math.round(metal * 255);
                    data[i + 3] = 255;
                }
            }
        }
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d')!;
        const imgData = ctx.createImageData(size, size);
        imgData.data.set(data);
        ctx.putImageData(imgData, 0, 0);
        const image = new ImageAsset(canvas);
        const tex = new Texture2D();
        tex.image = image;
        tex.setFilters(Texture2D.Filter.LINEAR, Texture2D.Filter.LINEAR);
        tex.setWrapMode(Texture2D.WrapMode.REPEAT, Texture2D.WrapMode.REPEAT);
        return tex;
    }

    private surfaceMaps(kind: string): { normal: Texture2D; pbr: Texture2D } | null {
        if (!kind || kind === 'leaf') return null;
        if (!this.surfaceCache[kind]) {
            this.surfaceCache[kind] = {
                normal: this.makeSurfaceTexture(kind, true),
                pbr: this.makeSurfaceTexture(kind, false),
            };
            console.log('[MAT] generated procedural normal/pbr maps kind=' + kind);
        }
        return this.surfaceCache[kind];
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
        // Evidence shots may pin the board to a specific card count; the quest
        // machine must not fight that until the next full reset.
        this.boardManual = true;
        this.boardState = state;
        const visible = state === 'full' ? 3 : state === 'empty' || state === 'reset' ? 0 : state === 'A' ? 1 : state === 'B' ? 2 : 3;
        this.applyBoardCards(visible);
    }

    /** Shared card-visibility writer for the manual override and the quest
     * derive, so both paths stay byte-identical in what they show. */
    private applyBoardCards(visible: number): void {
        for (let i = 0; i < this.cardNodes.length; i++) {
            this.cardNodes[i].active = i < visible;
        }
        if (this.fxBoardNode) this.fxBoardNode.active = false;
        console.log('[COURTYARD] board=' + this.boardState + ' cards=' + visible);
    }

    private makePrimitive(name: string, geometry: any, mat: Material, pos: Vec3): Node {
        const node = new Node(name);
        // W2: primitives spawned under a UI-layer root inherit that layer, and the
        // 3D camera only draws DEFAULT, so the contact-shadow patches were culled.
        node.layer = Layers.Enum.DEFAULT;
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

    // G06/G07: loading overlay, failure/retry card, sound preference.
    private failedLoads: Array<{ path: string; type: any; cb: (err: any, asset: any) => void }> = [];
    private loadingRoot: Node | null = null;
    private loadingBarLabel: Label | null = null;
    private loadingBarFill: Graphics | null = null;
    private loadingBarW = 0;
    private loadingStageLabel: Label | null = null;
    private retryRoot: Node | null = null;
    private retryErrorLabel: Label | null = null;
    private soundOn = false;
    private totalLoads = 0;
    private doneLoads = 0;

    private loadAssets(): void {
        const load = (path: string, type: any, cb: (err: any, asset: any) => void) => {
            this.pendingLoads++;
            this.totalLoads++;
            resources.load(path, type, (err: any, asset: any) => {
                if (err || !asset) {
                    const message = '[COURTYARD] load failed: ' + path + ' :: ' + (err ? err.message || err : 'null');
                    console.warn(message);
                    this.loadErrors.push(message);
                    // G07: remember the request so the retry card can re-run it.
                    if (!this.failedLoads.some((f) => f.path === path)) {
                        this.failedLoads.push({ path, type, cb });
                    }
                } else {
                    const i = this.failedLoads.findIndex((f) => f.path === path);
                    if (i >= 0) this.failedLoads.splice(i, 1);
                }
                cb(err, asset);
                this.pendingLoads--;
                this.doneLoads++;
                this.updateLoadingProgress();
                this.maybeFinish();
            });
        };

        load('models/MAP001_courtyard/MAP001_courtyard', Prefab, (_e, p) => { this.prefabs['map'] = p; });
        load('ui/paper_panel_wash/texture', Texture2D, (_e, t) => { this.paperTexture = t; });
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
        load('ui/postcard_bench/texture', Texture2D, (_e, t) => { if (t) { this.iconTextures['postcard_bench'] = t; this.ensurePostcardProp('card_bench'); } });
        load('ui/postcard_flower/texture', Texture2D, (_e, t) => { if (t) { this.iconTextures['postcard_flower'] = t; this.ensurePostcardProp('card_flower'); } });
        load('ui/postcard_pergola/texture', Texture2D, (_e, t) => { if (t) { this.iconTextures['postcard_pergola'] = t; this.ensurePostcardProp('card_pergola'); } });
        load('char/npc_gardener_slice/texture', Texture2D, (_e, t) => { this.npcTexture = t; });
        load('fx/FX002_pickup_feedback/texture', Texture2D, (_e, t) => { if (t) this.fxTextures['pickup'] = t; });
        load('fx/FX003_board_completion/texture', Texture2D, (_e, t) => { if (t) this.fxTextures['board'] = t; });
        load('char/1015_aglna2', sp.SkeletonData, (_e, data) => {
            if (data) this.buildCharacter(data);
        });

        // Portraits/icons/paper are applied when the delayed UI is built.
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
            }
        }
        // Apply the paper texture to every nine-slice panel that was built empty.
        for (const sprite of this.paperSprites) {
            const ut = sprite.node.getComponent(UITransform);
            const frame = this.makeSlicedFrame(ut ? ut.width : 320, ut ? ut.height : 160);
            if (frame) {
                sprite.spriteFrame = frame;
                sprite.type = Sprite.Type.SLICED;
            }
        }
        console.log('[COURTYARD] UI assets applied, font=' + (this.fontSans ? 'Noto Sans SC' : 'fallback'));
    }

    private paperSprites: Sprite[] = [];
    private portraitSprites: Record<string, Sprite> = {};

    private makeSlicedFrame(w = 320, h = 160): SpriteFrame | null {
        if (!this.paperTexture) return null;
        const sf = new SpriteFrame();
        sf.texture = this.paperTexture;
        // The torn border lives in the first 44 texture px. Small tags use a
        // tighter inset so the 9-slice still has a valid centre.
        const inset = Math.max(14, Math.min(44, Math.floor(Math.min(w, h) * 0.28)));
        sf.insetLeft = inset;
        sf.insetRight = inset;
        sf.insetTop = inset;
        sf.insetBottom = inset;
        return sf;
    }

    private maybeFinish(): void {
        if (this.pendingLoads > 0 || this.assetsReady) return;
        if (!this.prefabs['map'] || !this.spine) {
            // G07: a missing required asset (map / character) may never be
            // dressed up as success — show the retry card with a copyable
            // summary instead of an empty courtyard.
            console.error('[COURTYARD] required assets missing: ' + this.loadErrors.join(' | '));
            this.showRetryCard();
            return;
        }
        this.assetsReady = true;
        this.hideLoadingOverlay();
        this.buildEnvironment();
        this.buildContactShadow();
        this.buildTreeShadow();
        // Build the UI on the first stable frame. Creating labels in the same
        // tick as the font atlas initialisation left stale glyph quads, which
        // showed as an offset text shadow.
        this.scheduleOnce(() => {
            try {
                view.setCanvasSize(window.innerWidth, window.innerHeight);
                view.resizeWithBrowserSize(true);
            } catch (e) { /* headless */ }
            this.setupUI();
            this.setupPostFx();
            this.buildNpcAndFx();
            this.applyLoadedUiAssets();
            this.updateCharacterTransform();
            this.setupOrientation();
            this.scheduleOnce(() => {
                (globalThis as any).__COURTYARD_READY__ = true;
                console.log('[COURTYARD] READY spine=' + (this.spine ? 'yes' : 'no') + ' anims=Relax,Move,Interact');
            }, 0.6);
        }, 0.15);
    }

    // --------------------------------------------------------------- character

    private buildCharacter(data: sp.SkeletonData): void {
        const rt = new RenderTexture();
        rt.reset({ width: 1024, height: 1024 });
        this.charRT = rt;

        const canvasNode = new Node('CharRTCanvas');
        canvasNode.layer = Layers.Enum.UI_2D | RT_LAYER;
        canvasNode.parent = director.getScene()!;
        canvasNode.setPosition(20000, 0, 0);
        const cut = canvasNode.addComponent(UITransform);
        cut.setContentSize(1024, 1024);
        const canvas = canvasNode.addComponent(Canvas);
        const camNode = new Node('CharRTCamera');
        camNode.layer = RT_LAYER;
        camNode.parent = canvasNode;
        camNode.setPosition(0, 0, 1000);
        const cam = camNode.addComponent(Camera);
        cam.projection = Camera.ProjectionType.ORTHO;
        cam.orthoHeight = 512;
        cam.near = 0.1;
        cam.far = 2000;
        cam.clearFlags = Camera.ClearFlag.SOLID_COLOR;
        cam.clearColor = new Color(0, 0, 0, 0);
        // Only the spine canvas carries RT_LAYER; keeping this line strictly
        // RT_LAYER stops the UI camera content leaking into the character RT
        // (the offset double-render seen in candidate_n3).
        cam.visibility = RT_LAYER;
        cam.priority = -1;
        cam.targetTexture = rt;
        canvas.cameraComponent = cam;
        this.charRTCanvas = canvasNode;
        this.charRTCamera = cam;

        const node = new Node('PlayerSpineRT');
        node.layer = Layers.Enum.UI_2D | RT_LAYER;
        node.parent = canvasNode;
        // W2: at scale 2.0 / y=-500 the pose overflowed the 1024 RT (orthoHeight
        // 512, visible -512..512). The weapon was cut by a vertical line and the
        // boots by a horizontal one, so the silhouette ended in a rectangle.
        // 1.45 keeps the whole pose inside; the world quad grows by the same
        // ratio so the on-screen size is unchanged.
        node.setPosition(0, -430, 0);
        const ut = node.addComponent(UITransform);
        ut.setAnchorPoint(0.5, 0);
        ut.setContentSize(1024, 1024);
        const skel = node.addComponent(sp.Skeleton);
        skel.skeletonData = data;
        skel.defaultSkin = 'default';
        skel.premultipliedAlpha = false;
        skel.setAnimation(0, 'Relax', true);
        // Slight warm grade ties the unlit Spine art to the sunlit courtyard;
        // identity/line art stay untouched.
        skel.color = new Color(255, 245, 232, 255);
        node.setScale(1.45, 1.45, 1);
        this.spineNode = node;
        this.spine = skel;
        this.currentAnim = 'Relax';

        const quad = this.makeScreenQuad('PlayerWorldQuad', 2.41, 2.41, rt, new Vec4(1, 1, 0, 0));
        const mr = quad.getComponent(MeshRenderer)!;
        this.charQuadNode = quad;
        this.charQuadMR = mr;
        console.log('[COURTYARD] spine loaded into RenderTexture 1024x1024 + world depth quad');
        this.updateCharacterTransform();
    }

    private updateCharacterTransform(): void {
        if (!this.charQuadNode || !this.spine || !this.canvasUT) return;
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

    private buildTreeShadow(): void {
        // Fallback shade: broad radial blobs, used until the projected foliage
        // decal finishes loading.
        const size = 512;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d')!;
        const blob = (x: number, y: number, r: number, ry: number, alpha: number) => {
            ctx.save();
            ctx.translate(x, y);
            ctx.scale(1, ry / r);
            const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r);
            g.addColorStop(0, `rgba(26,22,18,${alpha})`);
            g.addColorStop(0.58, `rgba(26,22,18,${alpha * 0.62})`);
            g.addColorStop(1, 'rgba(26,22,18,0)');
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.arc(0, 0, r, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        };
        blob(size * 0.50, size * 0.52, size * 0.37, size * 0.32, 0.26);
        blob(size * 0.37, size * 0.44, size * 0.20, size * 0.17, 0.10);
        blob(size * 0.62, size * 0.48, size * 0.21, size * 0.18, 0.10);
        blob(size * 0.50, size * 0.66, size * 0.23, size * 0.17, 0.09);
        const image = new ImageAsset(canvas);
        const texture = new Texture2D();
        texture.image = image;
        texture.setFilters(Texture2D.Filter.LINEAR, Texture2D.Filter.LINEAR);
        const mat = new Material();
        mat.initialize({ effectName: 'builtin-unlit', technique: 1, defines: { USE_TEXTURE: true } });
        mat.setProperty('mainColor', C.white);
        mat.setProperty('mainTexture', texture);
        const node = this.makePrimitive('TreeContactShadow', primitives.plane({ width: 9.4, length: 8.0 }), mat, new Vec3(-3.2, PAVING_TOP + 0.004, 0.5));
        node.setRotationFromEuler(0, -26, 0);
        const mr = node.getComponent(MeshRenderer)!;
        mr.shadowCastingMode = MeshRenderer.ShadowCastingMode.OFF;
        mr.receiveShadow = false;

        // Real shape: the crown silhouette projected onto the ground along the
        // sun vector in Blender, so the shade has foliage edges instead of an
        // ellipse. Footprint and centre come from the bake metadata.
        resources.load('textures/tex_tree_shadow/texture', Texture2D, (err: any, proj: Texture2D) => {
            if (err || !proj) {
                console.warn('[COURTYARD] projected tree shadow unavailable, keeping radial fallback');
                return;
            }
            proj.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE, Texture2D.WrapMode.CLAMP_TO_EDGE);
            proj.setFilters(Texture2D.Filter.LINEAR, Texture2D.Filter.LINEAR);
            mat.setProperty('mainTexture', proj);
            node.setScale(12.384 / 9.4, 1, 12.384 / 8.0);
            node.setPosition(2.954, PAVING_TOP + 0.004, -1.419);
            node.setRotationFromEuler(0, 0, 0);
            console.log('[COURTYARD] tree shade switched to projected foliage silhouette');
        });
    }

    private setupPostFx(): void {
        if (!this.canvasNode) return;
        const size = 512;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d')!;
        const g = ctx.createRadialGradient(size * 0.5, size * 0.48, size * 0.18,
            size * 0.5, size * 0.5, size * 0.68);
        g.addColorStop(0, 'rgba(42,36,28,0)');
        g.addColorStop(0.62, 'rgba(42,36,28,0.045)');
        g.addColorStop(1, 'rgba(42,36,28,0.17)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, size, size);
        const image = new ImageAsset(canvas);
        const tex = new Texture2D();
        tex.image = image;
        tex.setFilters(Texture2D.Filter.LINEAR, Texture2D.Filter.LINEAR);
        const node = this.uiNode('Vignette', this.canvasNode, 0, 0, DESIGN_W, DESIGN_H);
        const sp = node.addComponent(Sprite);
        sp.sizeMode = Sprite.SizeMode.CUSTOM;
        sp.color = new Color(255, 255, 255, 255);
        const sf = new SpriteFrame();
        sf.texture = tex;
        sp.spriteFrame = sf;
        node.setSiblingIndex(0);
        console.log('[COURTYARD] vignette overlay ready');
    }

    private makeBlobMaterial(maxAlpha: number): Material {
        const size = 128;
        const data = new Uint8Array(size * size * 4);
        for (let y = 0; y < size; y++) {
            for (let x = 0; x < size; x++) {
                const nx = (x + 0.5) / size * 2 - 1;
                const ny = (y + 0.5) / size * 2 - 1;
                const d = Math.sqrt(nx * nx + ny * ny);
                const a = Math.max(0, 1 - d);
                const i = (y * size + x) * 4;
                data[i] = 24; data[i + 1] = 21; data[i + 2] = 18;
                data[i + 3] = Math.round(255 * Math.pow(a, 1.7) * maxAlpha);
            }
        }
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d')!;
        const imgData = ctx.createImageData(size, size);
        imgData.data.set(data);
        ctx.putImageData(imgData, 0, 0);
        const image = new ImageAsset(canvas);
        const tex = new Texture2D();
        tex.image = image;
        tex.setFilters(Texture2D.Filter.LINEAR, Texture2D.Filter.LINEAR);
        const mat = new Material();
        mat.initialize({ effectName: 'builtin-unlit', technique: 1, defines: { USE_TEXTURE: true } });
        mat.setProperty('mainColor', C.white);
        mat.setProperty('mainTexture', tex);
        return mat;
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
                const alpha = Math.round(255 * Math.pow(a, 1.45) * 0.86);
                const i = (y * size + x) * 4;
                data[i] = 0; data[i + 1] = 0; data[i + 2] = 0; data[i + 3] = alpha;
            }
        }
        // W2: the canvas -> ImageAsset -> Texture2D path produced an empty
        // texture on the web build, which is why the player had no contact
        // shadow while the tree (loaded from a PNG) did. Upload the raw pixels.
        const image = new ImageAsset({
            _data: data,
            width: size,
            height: size,
            format: Texture2D.PixelFormat.RGBA8888,
            _compressed: false,
        } as any);
        const texture = new Texture2D();
        texture.image = image;
        texture.setFilters(Texture2D.Filter.LINEAR, Texture2D.Filter.LINEAR);

        const mat = new Material();
        mat.initialize({ effectName: 'builtin-unlit', technique: 1, defines: { USE_TEXTURE: true } });
        mat.setProperty('mainColor', C.white);
        mat.setProperty('mainTexture', texture);
        this.shadowMaterial = mat;
        this.shadowTexture = texture;

        // W2: a zero-thickness plane never drew (the tree's plane does not either —
        // what reads as tree shade is the real shadow map). Give the patch a tiny
        // thickness so it has a face pointing at the camera from any pitch.
        const node = this.makePrimitive('ContactShadow', primitives.box({ width: 2.2, height: 0.02, length: 1.4, widthSegments: 1, heightSegments: 1, lengthSegments: 1 }), mat, new Vec3(this.playerPos.x, PAVING_TOP + 0.004, this.playerPos.z));
        const mr = node.getComponent(MeshRenderer)!;
        mr.shadowCastingMode = MeshRenderer.ShadowCastingMode.OFF;
        mr.receiveShadow = false;
        this.shadowNode = node;
        // Soft ambient blobs under benches and side planters; these are not a
        // replacement for the key-light shadows, only contact grounding.
        console.log('[COURTYARD] contact shadow generated (runtime radial texture, unlit alpha)');

        // The runtime-built Texture2D never reaches the GPU on the web build:
        // probing at runtime shows the mesh, bounds, layer and model all valid,
        // a hand-built material with no texture renders, and the same mesh with
        // this texture renders nothing. Ship the identical radial blob as an
        // imported PNG instead — the same route the tree shadow already uses.
        resources.load('textures/tex_contact_shadow/texture', Texture2D,
            (err: any, tex: Texture2D) => {
                if (err || !tex) {
                    console.warn('[COURTYARD] contact shadow png load failed', err);
                    return;
                }
                this.shadowTexture = tex;
                if (this.shadowMaterial) this.shadowMaterial.setProperty('mainTexture', tex);
                if (this.npcShadowMaterial) this.npcShadowMaterial.setProperty('mainTexture', tex);
                console.log('[COURTYARD] contact shadow texture loaded from png');
            });
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
            if (this.shadowTexture) {
                // The shared radial blob read as a hard dark puddle at NPC size;
                // a dimmer, tighter copy grounds the feet without the ink blot.
                // Runtime Material has no clone(), so a second material is built
                // from the same generated texture.
                const npcMat = new Material();
                npcMat.initialize({ effectName: 'builtin-unlit', technique: 1, defines: { USE_TEXTURE: true } });
                npcMat.setProperty('mainColor', new Color(255, 255, 255, 150));
                npcMat.setProperty('mainTexture', this.shadowTexture);
                this.npcShadowMaterial = npcMat;
                const npcShadow = this.makePrimitive('NpcContactShadow',
                    primitives.plane({ width: 1.02, length: 0.64 }), npcMat,
                    new Vec3(2.86, PAVING_TOP + 0.006, -5.06));
                npcShadow.setRotationFromEuler(0, -32, 0);
                const nmr = npcShadow.getComponent(MeshRenderer)!;
                nmr.shadowCastingMode = MeshRenderer.ShadowCastingMode.OFF;
                nmr.receiveShadow = false;
            }
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
        const sf = this.makeSlicedFrame(350, 510);
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
        for (const n of this.billboardExtras) {
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
        scrimG.fillColor = new Color(38, 36, 31, 40);
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
        this.buildPauseCard();
        this.buildCompleteCard();
        // G01: the HUD's first paint already comes from the derive, so the
        // hardcoded strings in buildHud can never drift from the data.
        this.refreshQuestHud();
        this.refreshActionButton();
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

    private paperPanel(parent: Node, x: number, y: number, w: number, h: number, name = 'PaperPanel', tint?: Color): Sprite {
        const node = this.uiNode(name, parent, x, y, w, h);
        const sprite = node.addComponent(Sprite);
        sprite.sizeMode = Sprite.SizeMode.CUSTOM;
        sprite.type = Sprite.Type.SLICED;
        const frame = this.makeSlicedFrame(w, h);
        if (frame) sprite.spriteFrame = frame;
        if (tint) sprite.color = tint;
        const ut = node.getComponent(UITransform)!;
        ut.setContentSize(w, h);
        this.paperSprites.push(sprite);
        return sprite;
    }

    /** Irregular second sheet, tape, ink doodles and a pressed leaf. The
     * engine UI shares one paper/doodle vocabulary instead of solid insets. */
    private paperUnder(parent: Node, x: number, y: number, w: number, h: number,
        name: string, angle: number, alpha: number): Sprite {
        const sheet = this.paperPanel(parent, x, y, w, h, name,
            new Color(247, 243, 232, alpha));
        sheet.node.angle = angle;
        return sheet;
    }

    private tape(parent: Node, x: number, y: number, w: number, h: number,
        angle = 0): Node {
        const node = this.uiNode('Tape', parent, x, y, w, h);
        node.angle = angle;
        const g = node.addComponent(Graphics);
        g.fillColor = new Color(216, 201, 166, 118);
        g.rect(-w / 2, -h / 2, w, h);
        g.fill();
        g.strokeColor = new Color(120, 105, 76, 50);
        g.lineWidth = 0.8;
        g.moveTo(-w / 2 + 2, -h / 2 + 2); g.lineTo(w / 2 - 2, -h / 2 + 2);
        g.moveTo(-w / 2 + 3, h / 2 - 3); g.lineTo(w / 2 - 3, h / 2 - 3);
        g.stroke();
        g.strokeColor = new Color(255, 250, 235, 70);
        g.moveTo(-w / 2 + 5, 0); g.lineTo(w / 2 - 7, 0.8);
        g.stroke();
        return node;
    }

    private doodle(parent: Node, kind: string, x: number, y: number, size: number,
        color: Color = C.ink, angle = 0, alpha = 150): Node {
        const node = this.uiNode('Doodle_' + kind, parent, x, y, size, size);
        node.angle = angle;
        const g = node.addComponent(Graphics);
        g.strokeColor = new Color(color.r, color.g, color.b, alpha);
        g.lineWidth = 1.35;
        const s = size / 2;
        if (kind === 'leaf') {
            g.moveTo(-s * 0.55, -s); g.bezierCurveTo(-s * 0.1, -s * 0.2, s * 0.1, s * 0.35, s * 0.62, s * 0.9);
            g.stroke();
            g.moveTo(-s * 0.02, -s * 0.25); g.bezierCurveTo(-s * 0.55, -s * 0.15, -s * 0.7, s * 0.25, -s * 0.35, s * 0.55);
            g.bezierCurveTo(-s * 0.05, s * 0.7, s * 0.3, s * 0.35, -s * 0.02, -s * 0.25); g.stroke();
            g.moveTo(s * 0.15, s * 0.05); g.bezierCurveTo(s * 0.55, s * 0.05, s * 0.76, s * 0.38, s * 0.5, s * 0.62);
            g.bezierCurveTo(s * 0.3, s * 0.78, s * 0.02, s * 0.5, s * 0.15, s * 0.05); g.stroke();
        } else if (kind === 'star') {
            g.moveTo(0, -s); g.lineTo(0, s);
            g.moveTo(-s, 0); g.lineTo(s, 0);
            g.moveTo(-s * 0.48, -s * 0.48); g.lineTo(s * 0.48, s * 0.48);
            g.moveTo(s * 0.48, -s * 0.48); g.lineTo(-s * 0.48, s * 0.48);
            g.stroke();
            g.circle(0, 0, s * 0.24); g.stroke();
        } else if (kind === 'cloud') {
            g.circle(-s * 0.46, -s * 0.12, s * 0.30);
            g.circle(-s * 0.12, s * 0.12, s * 0.36);
            g.circle(s * 0.28, -s * 0.02, s * 0.32);
            g.circle(s * 0.55, -s * 0.18, s * 0.20);
            g.stroke();
            g.moveTo(-s * 0.75, -s * 0.42); g.lineTo(s * 0.72, -s * 0.42); g.stroke();
        } else if (kind === 'flower') {
            for (let i = 0; i < 5; i++) {
                const a = i * Math.PI * 2 / 5 - Math.PI / 2;
                g.circle(Math.cos(a) * s * 0.42, Math.sin(a) * s * 0.42, s * 0.28);
            }
            g.stroke();
            g.circle(0, 0, s * 0.16); g.stroke();
        } else if (kind === 'grass') {
            g.moveTo(-s * 0.4, -s); g.bezierCurveTo(-s * 0.2, -s * 0.2, -s * 0.35, s * 0.4, -s * 0.5, s * 0.85);
            g.moveTo(0, -s); g.bezierCurveTo(-s * 0.05, -s * 0.25, s * 0.2, s * 0.3, s * 0.15, s * 0.95);
            g.moveTo(s * 0.35, -s); g.bezierCurveTo(s * 0.4, -s * 0.2, s * 0.55, s * 0.35, s * 0.7, s * 0.7);
            g.stroke();
        } else if (kind === 'stitch') {
            for (let i = -2; i <= 2; i++) {
                g.moveTo(i * s * 0.4 - s * 0.14, s * 0.18);
                g.lineTo(i * s * 0.4 + s * 0.14, -s * 0.18);
            }
            g.stroke();
        } else {
            g.moveTo(-s, 0); g.lineTo(s, 0); g.stroke();
        }
        return node;
    }

    private deckleOutline(parent: Node, w: number, h: number, alpha = 46): Node {
        const node = this.uiNode('DeckleInk', parent, 0, 0, w, h);
        const g = node.addComponent(Graphics);
        g.strokeColor = new Color(74, 64, 49, alpha);
        g.lineWidth = 1.0;
        const pts: Vec2[] = [];
        const segs = 18;
        for (let i = 0; i <= segs; i++) {
            const t = i / segs;
            pts.push(new Vec2(-w / 2 + 5 + t * (w - 10), h / 2 - 4 - Math.sin(t * 19.0) * 1.8 - (i % 3) * 0.6));
        }
        for (let i = 0; i <= 6; i++) {
            const t = i / 6;
            pts.push(new Vec2(w / 2 - 4 - Math.sin(t * 11.0) * 1.4, h / 2 - 8 - t * (h - 16)));
        }
        for (let i = 0; i <= segs; i++) {
            const t = i / segs;
            pts.push(new Vec2(w / 2 - 5 - t * (w - 10), -h / 2 + 4 + Math.sin(t * 17.0 + 1.2) * 1.7));
        }
        for (let i = 0; i <= 6; i++) {
            const t = i / 6;
            pts.push(new Vec2(-w / 2 + 4 + Math.sin(t * 9.0) * 1.4, -h / 2 + 8 + t * (h - 16)));
        }
        for (let i = 1; i < pts.length; i++) {
            if (i % 7 === 0) g.moveTo(pts[i].x, pts[i].y);
            else g.lineTo(pts[i].x, pts[i].y);
        }
        g.stroke();
        return node;
    }

    private label(parent: Node, text: string, size: number, color: Color, x: number, y: number, w: number, h: number,
        align: number = Label.HorizontalAlign.LEFT,
        valign: number = Label.VerticalAlign.CENTER,
        serif = false): Label {
        const node = this.uiNode('Label', parent, x, y, w, h);
        const label = node.addComponent(Label);
        label.fontSize = size;
        label.lineHeight = Math.round(size * 1.4);
        label.color = color;
        label.horizontalAlign = align;
        label.verticalAlign = valign;
        label.overflow = Label.Overflow.CLAMP;
        label.enableWrapText = true;
        label.useSystemFont = true;
        label.fontFamily = serif ? 'KaiTi, STKaiti, serif' : 'Microsoft YaHei, sans-serif';
        if (serif) this.labelsSerif.push(label); else this.labelsSans.push(label);
        label.string = text;
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
        // Quest card, top left: two loose sheets, tape and ink doodles.
        this.paperUnder(this.hudRoot, -430, 273, 370, 121, 'QuestCardUnder', 0.8, 46);
        const card = this.paperPanel(this.hudRoot, -428, 272, 368, 118, 'QuestCard', new Color(249, 245, 234, 200));
        this.decoratePaper(card.node, 368, 118);
        this.tape(card.node, -156, 54, 62, 17, -13);
        this.tape(card.node, 152, -48, 52, 15, 7);
        this.doodle(card.node, 'leaf', -166, -38, 30, C.goldDeep, 22, 128);
        this.doodle(card.node, 'star', 150, 36, 20, C.mintDeep, 0, 135);
        this.doodle(card.node, 'stitch', 72, -42, 26, C.ink, -4, 82);
        this.deckleOutline(card.node, 368, 118, 38);
        const badgeNode = this.uiNode('QuestBadge', card.node, 138, 12, 80, 26);
        const badgeG = badgeNode.addComponent(Graphics);
        badgeG.fillColor = new Color(159, 216, 200, 90);
        badgeG.strokeColor = new Color(79, 138, 121, 120);
        badgeG.lineWidth = 1.5;
        badgeG.roundRect(-40, -13, 80, 26, 13);
        badgeG.fill();
        badgeG.stroke();
        this.questBadge = this.label(badgeNode, '待接取', 13, C.meta, 0, 0, 76, 24, Label.HorizontalAlign.CENTER);

        this.icon(card.node, 'icon_pin', 146, 40, 18, C.goldDeep);
        this.icon(card.node, 'icon_talk', -146, 2, 24, C.mintDeep);

        this.label(card.node, '当前任务', 13, C.muted, -33, 38, 190, 20);
        this.questTitle = this.label(card.node, '和园丁聊聊', 24, C.ink, -13, 12, 230, 32, Label.HorizontalAlign.LEFT,
            Label.VerticalAlign.CENTER, true);
        this.questSub = this.label(card.node, '园丁就在南入口的路石旁', 15, C.muted, -3, -23, 250, 24);

        // Menu button, top right.
        this.paperUnder(this.hudRoot, 584, 248, 62, 62, 'MenuUnder', -2.4, 62);
        const menu = this.paperPanel(this.hudRoot, 582, 250, 58, 58, 'MenuButton',
            new Color(251, 247, 236, 214));
        menu.node.angle = 1.4;
        this.icon(menu.node, 'icon_menu', 0, 0, 26, C.ink);
        this.tape(menu.node, 0, 31, 38, 11, -3);
        this.doodle(menu.node, 'grass', 21, -20, 18, C.mintDeep, 12, 118);

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
        actionPaper.color = new Color(255, 255, 255, 220);
        const actionFrame = this.makeSlicedFrame(126, 126);
        if (actionFrame) actionPaper.spriteFrame = actionFrame;
        this.paperSprites.push(actionPaper);
        this.actionPaper = actionPaper;
        // Same tape / deckle / doodle language as the quest card and dialogue,
        // so the three components read as one material family.
        this.tape(this.actionRoot, 0, 58, 46, 13, -6);
        this.deckleOutline(this.actionRoot, 126, 126, 40);
        this.doodle(this.actionRoot, 'leaf', -44, -44, 20, C.goldDeep, 24, 120);
        this.actionIconSprite = this.icon(this.actionRoot, 'icon_talk', 0, 30, 34, C.mintDeep);
        this.actionLabel = this.label(this.actionRoot, '交谈', 21, C.ink, 0, -8, 110, 30, Label.HorizontalAlign.CENTER);
        // W5: C.muted on an almost-white action paper measured ~2:1, the sub-label
        // was effectively unreadable over bright paving. body ink keeps the tertiary
        // step while staying legible on the paper.
        this.actionSub = this.label(this.actionRoot, '园丁', 15, C.inkBody, 0, -34, 100, 22, Label.HorizontalAlign.CENTER);
        this.actionRoot.on(Node.EventType.TOUCH_END, () => this.onActionPressed());

        console.log('[COURTYARD] HUD built (real Labels + nine-slice + Graphics joystick)');
    }

    private buildDialogue(): void {
        const DIALOGUE_W = 1060;
        const DIALOGUE_H = 176;
        this.paperUnder(this.dialogueRoot, 5, -265, 1068, 184, 'DialogueUnder', -0.4, 40);
        // W1 paper_shape: the sheet read as a card because it sat at 96% opacity
        // and buried the paving behind it. Drop the sheet to 80% so the courtyard
        // shows through, and keep the text column opaque enough to stay legible.
        const panel = this.paperPanel(this.dialogueRoot, 0, -262, DIALOGUE_W, DIALOGUE_H, 'DialoguePaper',
            new Color(250, 247, 238, 205));
        // Opaque inner sheet only under the text column: the full-width panel
        // stayed too translucent for the pale paving to stop showing through.
        this.paperUnder(panel.node, 60, -4, 690, 124, 'DialogueTextSheet', 0.5, 236);
        this.decorateDialoguePaper(panel.node, DIALOGUE_W, DIALOGUE_H);
        this.tape(panel.node, -470, 84, 72, 18, -9);
        this.tape(panel.node, 476, 82, 62, 16, 7);
        this.tape(panel.node, 462, -76, 48, 13, -7);
        this.deckleOutline(panel.node, DIALOGUE_W, DIALOGUE_H, 42);
        this.doodle(panel.node, 'cloud', 312, -38, 94, C.mintDeep, 0, 108);
        this.doodle(panel.node, 'flower', 448, 22, 46, C.mintDeep, -8, 120);
        this.doodle(panel.node, 'leaf', 256, 54, 26, C.goldDeep, 18, 126);
        this.doodle(panel.node, 'star', 118, 52, 18, C.goldDeep, 0, 112);
        this.doodle(panel.node, 'stitch', -392, -68, 26, C.ink, -3, 74);

        const portraitBg = this.paperPanel(panel.node, -460, 0, 136, 136, 'PortraitPaper',
            new Color(255, 255, 255, 244));
        portraitBg.node.angle = -1.2;
        this.tape(portraitBg.node, 0, 69, 46, 12, -3);
        const portraitNode = this.uiNode('Portrait', portraitBg.node, 0, 0, 120, 120);
        const portrait = portraitNode.addComponent(Sprite);
        portrait.sizeMode = Sprite.SizeMode.CUSTOM;
        portrait.color = new Color(255, 255, 255, 0);
        portraitNode.getComponent(UITransform)!.setContentSize(120, 120);
        this.portraitSprite = portrait;
        this.portraitSprites['npc'] = portrait;

        const playerNode = this.uiNode('PortraitPlayer', portraitBg.node, 0, 0, 120, 120);
        const playerSprite = playerNode.addComponent(Sprite);
        playerSprite.sizeMode = Sprite.SizeMode.CUSTOM;
        playerSprite.color = new Color(255, 255, 255, 0);
        playerNode.getComponent(UITransform)!.setContentSize(120, 120);
        playerNode.active = false;
        this.portraitSprites['player'] = playerSprite;
        this.playerPortraitNode = playerNode;

        // P1 t044 clusters hand marks around the portrait rather than scattering
        // one doodle per panel; keep them tight and low-contrast.
        this.doodle(panel.node, 'star', -534, 62, 20, C.goldDeep, -12, 150);
        this.doodle(panel.node, 'star', -386, 66, 14, C.ink, 14, 96);
        this.doodle(panel.node, 'leaf', -540, -58, 24, C.mintDeep, -24, 132);
        this.doodle(panel.node, 'flower', -380, -62, 20, C.goldDeep, 10, 126);
        this.doodle(panel.node, 'stitch', -520, 4, 22, C.ink, 90, 66);
        this.doodle(panel.node, 'grass', -404, 12, 18, C.mintDeep, 6, 108);

        this.speakerLabel = this.label(panel.node, '园丁', 34, C.ink, -275, 42, 190, 40, Label.HorizontalAlign.LEFT,
            Label.VerticalAlign.CENTER, true);
        this.pageLabel = this.label(panel.node, '第 1 页 / 共 2 页', 16, C.meta, 250, 44, 200, 26);
        this.bodyLabel = this.label(panel.node, '风把留言板上的三张明信片吹散了，能帮我找回来吗？', 24, C.inkBody,
            -60, -2, 640, 62, Label.HorizontalAlign.LEFT, Label.VerticalAlign.TOP);
        this.hintLabel = this.label(panel.node, '点击「下一页」继续', 17, C.meta, -205, -54, 330, 26);
        this.icon(panel.node, 'icon_sparkle', -350, -52, 12, C.mintDeep);
        this.icon(panel.node, 'icon_postcard', 300, 44, 30, C.goldDeep);
        this.icon(panel.node, 'icon_sparkle', -352, 32, 13, C.mintDeep);
        this.icon(panel.node, 'icon_leaf', 300, -52, 13, C.mintDeep);
        const accent = this.uiNode('DialogueAccent', panel.node, -268, 30, 124, 5);
        const ag = accent.addComponent(Graphics);
        ag.fillColor = new Color(159, 216, 200, 150);
        ag.roundRect(-62, -1.5, 124, 3, 1.5);
        ag.fill();
        const underline = this.uiNode('SpeakerUnderline', panel.node, -274, 38, 118, 4);
        const ug = underline.addComponent(Graphics);
        ug.strokeColor = new Color(138, 100, 37, 100);
        ug.lineWidth = 1;
        ug.moveTo(-57, 0); ug.lineTo(57, 1.5);
        ug.stroke();

        this.dialogueActionNode = this.uiNode('DialogueNext', panel.node, 430, -26, 160, 48);
        const nextPaper = this.dialogueActionNode.addComponent(Sprite);
        this.dialogueNextSprite = nextPaper;
        nextPaper.sizeMode = Sprite.SizeMode.CUSTOM;
        nextPaper.type = Sprite.Type.SLICED;
        nextPaper.color = new Color(255, 255, 255, 248);
        const nf = this.makeSlicedFrame(160, 48);
        if (nf) nextPaper.spriteFrame = nf;
        this.paperSprites.push(nextPaper);
        this.nextLabel = this.label(this.dialogueActionNode, '下一页', 19, C.ink, -12, 0, 112, 28, Label.HorizontalAlign.CENTER);
        this.dialogueNextLabel = this.nextLabel;
        this.icon(this.dialogueActionNode, 'icon_arrow', 58, 0, 18, C.ink);
        this.dialogueActionNode.on(Node.EventType.TOUCH_END, () => this.advanceDialogue());

        const pageNote = this.label(panel.node, '共 2 页', 13, C.muted, 430, -58, 120, 20, Label.HorizontalAlign.CENTER);
        pageNote.name = 'PageNote';

        const closeNode = this.uiNode('DialogueClose', panel.node, 505, 54, 36, 36);
        const closePaper = closeNode.addComponent(Sprite);
        closePaper.sizeMode = Sprite.SizeMode.CUSTOM;
        closePaper.type = Sprite.Type.SLICED;
        closePaper.color = new Color(255, 255, 255, 225);
        const cf = this.makeSlicedFrame(36, 36);
        if (cf) closePaper.spriteFrame = cf;
        this.paperSprites.push(closePaper);
        this.icon(closeNode, 'icon_close', 0, 0, 16, C.ink);
        closeNode.on(Node.EventType.TOUCH_END, () => this.closeDialogue());

        console.log('[COURTYARD] dialogue built (compact translucent paper, real copy, doodles)');
    }

    /** In-game pause used to have no on-screen feedback at all. This card is
     * built from the same torn-paper/tape/doodle vocabulary as the dialogue. */
    private buildPauseCard(): void {
        const root = this.uiNode('PauseRoot', this.canvasNode, 0, 0, DESIGN_W, DESIGN_H);
        root.setPosition(0, 0, 0);
        const dim = root.addComponent(Graphics);
        dim.fillColor = new Color(30, 27, 22, 96);
        dim.rect(-DESIGN_W / 2, -DESIGN_H / 2, DESIGN_W, DESIGN_H);
        dim.fill();
        root.setSiblingIndex(this.dialogueRoot.getSiblingIndex() + 1);

        const W = 380, H = 340;
        this.paperUnder(root, 4, -6, W + 16, H + 14, 'PauseUnder', -0.8, 150);
        const card = this.paperPanel(root, 0, 0, W, H, 'PausePaper',
            new Color(250, 247, 238, 246));
        this.tape(card.node, -150, 142, 74, 18, -8);
        this.tape(card.node, 152, 140, 60, 16, 6);
        this.deckleOutline(card.node, W, H, 44);
        this.doodle(card.node, 'leaf', -150, -112, 30, C.mintDeep, -18, 132);
        this.doodle(card.node, 'star', 150, -116, 20, C.goldDeep, 12, 140);
        this.doodle(card.node, 'flower', 128, 116, 26, C.mintDeep, -10, 120);
        this.doodle(card.node, 'stitch', -128, 96, 24, C.ink, 6, 70);

        this.label(card.node, '已暂停', 34, C.ink, 0, 96, 260, 44,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        const rule = this.uiNode('PauseRule', card.node, 0, 66, 200, 6);
        const rg = rule.addComponent(Graphics);
        rg.fillColor = new Color(159, 216, 200, 160);
        rg.roundRect(-100, -2, 200, 4, 2);
        rg.fill();
        this.label(card.node, '秋庭安静下来了', 15, C.muted, 0, 40, 260, 24,
            Label.HorizontalAlign.CENTER);

        const btn = this.uiNode('PauseResume', card.node, 0, -6, 300, 50);
        const btnSprite = btn.addComponent(Sprite);
        btnSprite.sizeMode = Sprite.SizeMode.CUSTOM;
        btnSprite.type = Sprite.Type.SLICED;
        btnSprite.color = new Color(255, 255, 255, 250);
        const bf = this.makeSlicedFrame(300, 50);
        if (bf) btnSprite.spriteFrame = bf;
        this.paperSprites.push(btnSprite);
        this.label(btn, '继续游戏', 20, C.ink, -22, 0, 200, 28,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        if (this.iconTextures['icon_continue']) {
            this.icon(btn, 'icon_continue', 108, 0, 24, C.ink);
        }
        btn.on(Node.EventType.TOUCH_END, () => this.setPause(false));

        // G06: sound toggle (default muted per spec) and a real restart.
        const soundBtn = this.uiNode('PauseSound', card.node, 0, -64, 300, 50);
        const soundSprite = soundBtn.addComponent(Sprite);
        soundSprite.sizeMode = Sprite.SizeMode.CUSTOM;
        soundSprite.type = Sprite.Type.SLICED;
        soundSprite.color = new Color(255, 255, 255, 244);
        const sf = this.makeSlicedFrame(300, 50);
        if (sf) soundSprite.spriteFrame = sf;
        this.paperSprites.push(soundSprite);
        this.pauseSoundLabel = this.label(soundBtn, '声音  关', 19, C.ink, -22, 0, 200, 26,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        this.pauseSoundIcon = this.icon(soundBtn, 'icon_sound_off', 108, 0, 24, C.ink);
        soundBtn.on(Node.EventType.TOUCH_END, () => this.toggleSound());

        const restartBtn = this.uiNode('PauseRestart', card.node, 0, -122, 300, 50);
        const restartSprite = restartBtn.addComponent(Sprite);
        restartSprite.sizeMode = Sprite.SizeMode.CUSTOM;
        restartSprite.type = Sprite.Type.SLICED;
        restartSprite.color = new Color(248, 235, 210, 250);
        const rf2 = this.makeSlicedFrame(300, 50);
        if (rf2) restartSprite.spriteFrame = rf2;
        this.paperSprites.push(restartSprite);
        this.label(restartBtn, '重新开始', 19, C.ink, -22, 0, 200, 26,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        if (this.iconTextures['icon_restart']) {
            this.icon(restartBtn, 'icon_restart', 108, 0, 24, C.ink);
        }
        restartBtn.on(Node.EventType.TOUCH_END, () => {
            this.fullRestart();
            console.log('[COURTYARD] restart from pause menu');
        });

        this.label(card.node, 'P 或点击按钮继续 · 声音默认关闭', 13, C.muted,
            0, -158, 320, 22, Label.HorizontalAlign.CENTER);
        root.active = false;
        this.pauseRoot = root;
        console.log('[COURTYARD] pause card built (resume + sound + restart)');
    }

    /** G06: spec — 默认静音，菜单可开启声音；音频缺失不能阻止 Demo 运行。
     * The demo ships no audio clips, so the toggle owns the preference and
     * any clip added later must respect it (play only when soundOn). */
    private toggleSound(): void {
        this.soundOn = !this.soundOn;
        if (this.pauseSoundLabel) {
            this.pauseSoundLabel.string = this.soundOn ? '声音  开' : '声音  关';
        }
        if (this.pauseSoundIcon) {
            const tex = this.iconTextures[this.soundOn ? 'icon_sound_on' : 'icon_sound_off'];
            if (tex) {
                const frame = new SpriteFrame();
                frame.texture = tex;
                this.pauseSoundIcon.spriteFrame = frame;
            }
        }
        console.log('[COURTYARD] sound=' + this.soundOn);
    }

    /** G06: 重新开始 — clear data and every overlay, back to the spawn, PLAYING. */
    private fullRestart(): void {
        this.resetQuest();
        this.gardenerLine = null;
        this.closeDialogue();
        if (this.completeRoot) this.completeRoot.active = false;
        if (this.toastNode) this.toastNode.active = false;
        this.joy.set(0, 0);
        this.keys.clear();
        this.manualMoving = false;
        this.moving = false;
        this.resetJoystick();
        this.playerPos.set(0, PAVING_TOP, -5.2);
        this.setPause(false);
        this.setUiVisible(true);
        this.cameraMode = 'game';
        this.lastFocusKey = '';
        this.refreshActionButton();
        console.log('[COURTYARD] full restart -> spawn, NOT_STARTED, no overlays');
    }

    /** COMPLETE_PANEL overlay for the DONE transition. Same paper vocabulary as
     * the pause card; the three postcards are data-driven from collectedIds so
     * the panel cannot disagree with the board. */
    private buildCompleteCard(): void {
        const root = this.uiNode('CompleteRoot', this.canvasNode, 0, 0, DESIGN_W, DESIGN_H);
        root.setPosition(0, 0, 0);
        const dim = root.addComponent(Graphics);
        dim.fillColor = new Color(30, 27, 22, 110);
        dim.rect(-DESIGN_W / 2, -DESIGN_H / 2, DESIGN_W, DESIGN_H);
        dim.fill();

        const W = 560, H = 340;
        this.paperUnder(root, 4, -4, W + 16, H + 14, 'CompleteUnder', -0.8, 160);
        const card = this.paperPanel(root, 0, 0, W, H, 'CompletePaper',
            new Color(250, 247, 238, 248));
        this.tape(card.node, -168, 158, 78, 18, -7);
        this.tape(card.node, 170, 156, 62, 16, 6);
        this.deckleOutline(card.node, W, H, 46);
        this.doodle(card.node, 'star', -216, 116, 22, C.goldDeep, 10, 130);
        this.doodle(card.node, 'leaf', 218, -120, 26, C.mintDeep, -14, 120);

        this.label(card.node, '秋庭来信 · 完成', 32, C.ink, 0, 104, 420, 42,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        this.label(card.node, '三张明信片都挂回了留言板。', 17, C.inkBody, 0, 58, 460, 26,
            Label.HorizontalAlign.CENTER);
        for (let i = 0; i < this.questTargets.length; i++) {
            const t = this.questTargets[i];
            if (t.kind !== 'postcard' || !t.tex) continue;
            if (this.iconTextures[t.tex]) {
                this.icon(card.node, t.tex, -150 + i * 150, -8, 104, C.white);
            }
        }
        const walk = this.uiNode('CompleteWalk', card.node, -118, -108, 208, 54);
        const walkSprite = walk.addComponent(Sprite);
        walkSprite.sizeMode = Sprite.SizeMode.CUSTOM;
        walkSprite.type = Sprite.Type.SLICED;
        walkSprite.color = new Color(255, 255, 255, 250);
        const wf = this.makeSlicedFrame(208, 54);
        if (wf) walkSprite.spriteFrame = wf;
        this.paperSprites.push(walkSprite);
        this.label(walk, '继续漫步', 20, C.ink, -16, 0, 150, 28,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        if (this.iconTextures['icon_continue']) this.icon(walk, 'icon_continue', 76, 0, 22, C.ink);
        walk.on(Node.EventType.TOUCH_END, () => this.setCompletePanel(false));

        const again = this.uiNode('CompleteAgain', card.node, 118, -108, 208, 54);
        const againSprite = again.addComponent(Sprite);
        againSprite.sizeMode = Sprite.SizeMode.CUSTOM;
        againSprite.type = Sprite.Type.SLICED;
        againSprite.color = new Color(248, 235, 210, 250);
        const af = this.makeSlicedFrame(208, 54);
        if (af) againSprite.spriteFrame = af;
        this.paperSprites.push(againSprite);
        this.label(again, '重新开始', 20, C.ink, -16, 0, 150, 28,
            Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER, true);
        if (this.iconTextures['icon_restart']) this.icon(again, 'icon_restart', 76, 0, 22, C.ink);
        again.on(Node.EventType.TOUCH_END, () => {
            this.resetQuest();
            this.playerPos.set(0, PAVING_TOP, -5.2);
            this.closeDialogue();
            this.setCompletePanel(false);
            this.showToast('任务已重新开始');
            console.log('[COURTYARD] restart from complete panel');
        });

        root.active = false;
        this.completeRoot = root;
        console.log('[COURTYARD] complete card built');
    }

    private setCompletePanel(visible: boolean): void {
        if (!this.completeRoot) this.buildCompleteCard();
        if (!this.completeRoot) return;
        this.completeRoot.active = visible;
        if (visible) {
            this.lockInput();
            this.actionRoot.active = false;
            this.joystickRoot.active = false;
        } else {
            this.actionRoot.active = true;
            this.joystickRoot.active = true;
            if (!this.paused && !this.dialogueVisible) this.unlockInput();
        }
        console.log('[COURTYARD] complete panel=' + visible);
    }

    private decorateDialoguePaper(node: Node, w: number, h: number): void {
        const doodle = this.uiNode('DialogueDoodle', node, 0, 0, w, h);
        const g = doodle.addComponent(Graphics);
        g.strokeColor = new Color(74, 64, 49, 52);
        g.lineWidth = 1;
        // Loose corner marks.
        g.moveTo(-w / 2 + 12, h / 2 - 18);
        g.lineTo(-w / 2 + 30, h / 2 - 24);
        g.lineTo(-w / 2 + 43, h / 2 - 19);
        g.moveTo(w / 2 - 54, h / 2 - 15);
        g.lineTo(w / 2 - 30, h / 2 - 20);
        g.moveTo(w / 2 - 40, -h / 2 + 16);
        g.lineTo(w / 2 - 22, -h / 2 + 21);
        g.lineTo(w / 2 - 8, -h / 2 + 17);
        // A small leaf sprig and a few ink dots at the left edge.
        g.moveTo(-w / 2 + 26, -h / 2 + 30);
        g.lineTo(-w / 2 + 41, -h / 2 + 44);
        g.lineTo(-w / 2 + 47, -h / 2 + 60);
        g.moveTo(-w / 2 + 41, -h / 2 + 44);
        g.lineTo(-w / 2 + 53, -h / 2 + 40);
        g.stroke();
        g.fillColor = new Color(79, 138, 121, 85);
        g.circle(-w / 2 + 53, -h / 2 + 40, 2.1);
        g.fill();
        g.fillColor = new Color(138, 100, 37, 70);
        g.circle(-w / 2 + 58, -h / 2 + 47, 1.4);
        g.fill();
        // Tape strip across the top edge.
        const tape = this.uiNode('PaperTape', node, 0, h / 2 - 5, 96, 20);
        tape.setRotationFromEuler(0, 0, -2.4);
        const tg = tape.addComponent(Graphics);
        tg.fillColor = new Color(246, 239, 220, 70);
        tg.rect(-48, -10, 96, 20);
        tg.fill();
        tg.strokeColor = new Color(138, 100, 37, 40);
        tg.lineWidth = 1;
        tg.moveTo(-44, 6); tg.lineTo(44, 6);
        tg.moveTo(-38, -5); tg.lineTo(38, -5);
        tg.stroke();
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
            // Spec §4: E interacts with whatever the quest focus is, not only
            // the gardener's two-page dialogue.
            this.onActionPressed();
        } else if (code === KeyCode.KEY_H) {
            this.setUiVisible(!this.uiVisible);
        } else if (code === KeyCode.ESCAPE) {
            this.closeDialogue();
        } else if (code === KeyCode.KEY_P) {
            this.setPause(!this.paused);
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
        if (this.pauseRoot) this.pauseRoot.active = paused && !this.dialogueVisible && !this.studioActive;
        console.log('[COURTYARD] paused=' + paused);
    }

    private openDialogue(page = 1): void {
        if (!this.uiVisible) this.setUiVisible(true);
        this.lockInput();
        this.dialogueVisible = true;
        this.dialogueCamera = true;
        // G03: one-line replies never touch the two-page accept flow.
        if (!this.gardenerLine) this.dialoguePage = page;
        this.applyDialoguePage();
        this.dialogueRoot.active = true;
        this.scrim.active = true;
        this.actionRoot.active = false;
        this.joystickRoot.active = false;
        if (this.npcNode) this.npcNode.active = false;
        this.resetJoystick();
        console.log('[COURTYARD] dialogue open page=' + page);
    }

    private applyDialoguePage(): void {
        // G03: a single-line gardener reply reuses the dialogue chrome but reads
        // as one page with no page counter and no accept step.
        if (this.gardenerLine) {
            this.speakerLabel.string = '园丁';
            this.bodyLabel.string = this.gardenerLine;
            this.pageLabel.string = '';
            this.nextLabel.string = '知道了';
            this.hintLabel.string = '';
            if (this.portraitSprite) this.portraitSprite.node.active = true;
            if (this.playerPortraitNode) this.playerPortraitNode.active = false;
            return;
        }
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
        // G03: a one-line gardener reply (reminder / hint / thanks) closes itself.
        if (this.gardenerLine) {
            this.gardenerLine = null;
            this.closeDialogue();
            console.log('[COURTYARD] gardener line closed');
            return;
        }
        if (this.dialoguePage === 1) {
            this.dialoguePage = 2;
            this.applyDialoguePage();
            console.log('[COURTYARD] dialogue page 2');
            return;
        }
        // G01: the dialogue only writes the state; the HUD derives from it.
        this.setQuestState('COLLECTING');
        this.closeDialogue();
        console.log('[COURTYARD] dialogue accepted; quest = COLLECTING');
    }

    private closeDialogue(): void {
        if (!this.dialogueVisible) {
            this.dialogueRoot.active = false;
            this.scrim.active = false;
            return;
        }
        this.dialogueVisible = false;
        this.dialogueCamera = false;
        this.dialogueRoot.active = false;
        this.scrim.active = false;
        if (this.pauseRoot) this.pauseRoot.active = this.paused && !this.studioActive;
        this.actionRoot.active = true;
        this.joystickRoot.active = true;
        if (this.npcNode) this.npcNode.active = true;
        if (!this.paused) this.unlockInput();
        console.log('[COURTYARD] dialogue closed');
    }

    // --------------------------------------------------------- quest machine
    // G01: one data source (questState / collectedIds / playerPos). Every visual
    // — HUD lines, action button, board cards, world postcards — derives from it
    // in refreshQuestHud(); no other code path may write the HUD directly.

    private setQuestState(state: QuestState): void {
        if (this.questState === state) return;
        this.questState = state;
        this.refreshQuestHud();
    }

    /** count of the three collectibles, used by the HUD and by submit gating */
    private collectedCount(): number {
        return this.collectedIds.size;
    }

    private refreshQuestHud(): void {
        const n = this.collectedCount();
        // The map can finish instantiating before the HUD exists; the derive
        // simply runs again the moment setupUI calls it.
        if (this.questTitle && this.questSub && this.questBadge) {
            if (this.questState === 'NOT_STARTED') {
                this.questTitle.string = '和园丁聊聊';
                this.questSub.string = '园丁就在南入口的路石旁';
                this.questBadge.string = '待接取';
            } else if (this.questState === 'COLLECTING') {
                this.questTitle.string = '找回明信片 ' + n + '/3';
                this.questSub.string = n === 0 ? '长椅、花坛、廊架附近找找'
                    : n < 3 ? '还差 ' + (3 - n) + ' 张' : '三张已找齐，去中央广场';
                this.questBadge.string = '任务中';
            } else if (this.questState === 'READY') {
                this.questTitle.string = '将明信片挂回留言板';
                this.questSub.string = '三张已找齐，去中央广场';
                this.questBadge.string = '可提交';
            } else {
                this.questTitle.string = '留言板已布置完成';
                this.questSub.string = '可继续漫步，或从菜单重新开始';
                this.questBadge.string = '完成';
            }
        }
        // Board card visibility is derived from DONE, never from an animation
        // callback. setBoardState stays callable for evidence shots; a manual
        // override wins until the quest resets.
        if (!this.boardManual) {
            this.boardState = this.questState === 'DONE' ? 'full' : 'empty';
            this.applyBoardCards(this.questState === 'DONE' ? 3 : 0);
        }
        for (const [id, node] of this.postcardNodes) {
            node.active = !this.collectedIds.has(id) &&
                (this.questState === 'COLLECTING' || this.questState === 'READY');
        }
        console.log('[COURTYARD] quest=' + this.questState + ' collected=' + n);
    }

    /** candidates the current state allows, nearest first, stable tie-break */
    private questCandidates(): QuestTarget[] {
        return this.questTargets.filter((t) => {
            if (t.kind === 'postcard') {
                return this.questState === 'COLLECTING' && !this.collectedIds.has(t.id);
            }
            return true;
        });
    }

    private questFocus(): QuestTarget | null {
        if (!this.questFocusId) return null;
        return this.questTargets.find((t) => t.id === this.questFocusId) || null;
    }

    /** Runs every frame after movement: pick the nearest in-range candidate and
     * refresh the action button only when the answer actually changed. */
    private updateQuestFocus(): void {
        if (!this.uiVisible || this.dialogueVisible || this.studioActive) return;
        let best: QuestTarget | null = null;
        let bestD2 = QUEST_INTERACT_DIST * QUEST_INTERACT_DIST;
        for (const t of this.questCandidates()) {
            const dx = this.playerPos.x - t.x;
            const dz = this.playerPos.z - t.z;
            const d2 = dx * dx + dz * dz;
            if (d2 <= bestD2) {
                best = t;
                bestD2 = d2;
            }
        }
        this.questFocusId = best ? best.id : null;
        const key = best ? best.id + ':' + this.questState : '';
        if (key !== this.lastFocusKey) {
            this.lastFocusKey = key;
            this.refreshActionButton();
        }
    }

    private refreshActionButton(): void {
        const t = this.questFocus();
        if (!t) {
            this.setAction('', '', 'icon_pickup', { hidden: true });
            return;
        }
        if (t.kind === 'gardener') {
            this.setAction('交谈', '园丁', 'icon_talk');
        } else if (t.kind === 'postcard') {
            this.setAction('拾取', '明信片', 'icon_pickup');
        } else if (this.questState === 'READY') {
            this.setAction('布置留言板', '留言板', 'icon_place', { gold: true });
        } else {
            this.setAction('查看', '留言板', 'icon_view');
        }
    }

    private onActionPressed(): void {
        if (this.dialogueVisible) {
            this.advanceDialogue();
            return;
        }
        const t = this.questFocus();
        if (!t) return;
        if (t.kind === 'gardener') this.talkToGardener();
        else if (t.kind === 'postcard') this.collectPostcard(t);
        else this.useBoard();
    }

    private talkToGardener(): void {
        switch (this.questState) {
            case 'NOT_STARTED':
                this.openDialogue(1);
                return;
            case 'COLLECTING':
                this.gardenerLine = this.collectedCount() === 0
                    ? '长椅、花坛、廊架附近都找找，卡片被风吹得不远。'
                    : '已找回 ' + this.collectedCount() + ' 张，剩下的应该也在附近。';
                break;
            case 'READY':
                this.gardenerLine = '三张都齐了？去中央广场的留言板挂上吧。';
                break;
            case 'DONE':
                this.gardenerLine = '谢谢你，花园又热闹起来了。想再走一遍就说“重新开始”。';
                break;
        }
        this.openDialogue(1);
    }

    /** G04: dedup on the id set first, visuals second. */
    private collectPostcard(t: QuestTarget): void {
        if (this.questState !== 'COLLECTING') {
            this.showToast('先问问园丁吧');
            return;
        }
        if (this.collectedIds.has(t.id)) return;
        this.collectedIds.add(t.id);
        const node = this.postcardNodes.get(t.id);
        if (node) node.active = false;
        if (this.collectedCount() === 3) this.setQuestState('READY');
        else this.refreshQuestHud();
        this.showToast('已找到 ' + this.collectedCount() + '/3 张');
        console.log('[COURTYARD] collect ' + t.id + ' -> ' + this.collectedCount() + '/3');
    }

    /** G05: submit checks the set and runs once; an early visit consumes nothing. */
    private useBoard(): void {
        if (this.questState === 'COLLECTING') {
            this.showToast('这里少了三张明信片');
            return;
        }
        if (this.questState === 'READY') {
            if (this.submittedOnce) return;
            this.submittedOnce = true;
            this.setQuestState('DONE');
            if (this.fxBoardNode) {
                this.fxBoardNode.active = true;
                this.scheduleOnce(() => { if (this.fxBoardNode) this.fxBoardNode.active = false; }, 1.2);
            }
            this.scheduleOnce(() => this.setCompletePanel(true), 0.9);
            console.log('[COURTYARD] submit -> DONE');
            return;
        }
        // DONE
        this.showToast('留言板已布置完成，继续漫步吧');
    }

    private showToast(text: string): void {
        if (!this.toastLabel) {
            const root = this.uiNode('QuestToast', this.hudRoot, 0, -196, 560, 40);
            const paper = root.addComponent(Sprite);
            paper.sizeMode = Sprite.SizeMode.CUSTOM;
            paper.type = Sprite.Type.SLICED;
            paper.color = new Color(250, 247, 238, 235);
            const frame = this.makeSlicedFrame(560, 40);
            if (frame) paper.spriteFrame = frame;
            this.paperSprites.push(paper);
            this.toastNode = root;
            this.toastLabel = this.label(root, text, 17, C.inkBody, 0, 0, 520, 26,
                Label.HorizontalAlign.CENTER, Label.VerticalAlign.CENTER);
        }
        this.toastLabel.string = text;
        if (this.toastNode) this.toastNode.active = true;
        this.toastUntil = Date.now() + 2200;
        this.scheduleOnce(() => {
            if (this.toastNode && Date.now() >= this.toastUntil) this.toastNode.active = false;
        }, 2.3);
    }

    /** Full reset used by “重新开始”: clear data, then let the HUD derive. */
    private resetQuest(): void {
        this.questState = 'NOT_STARTED';
        this.collectedIds.clear();
        this.submittedOnce = false;
        this.gardenerLine = null;
        this.boardManual = false;
        this.lastFocusKey = '';
        if (this.completeRoot) this.completeRoot.active = false;
        this.refreshQuestHud();
        this.refreshActionButton();
        console.log('[COURTYARD] quest reset');
    }

    /** G04: the three collectibles live in the world, billboarded like the NPC. */
    private ensurePostcardProp(targetId: string): void {
        if (this.postcardNodes.has(targetId)) return;
        const t = this.questTargets.find((q) => q.id === targetId);
        if (!t || !t.tex || !this.iconTextures[t.tex]) return;
        const node = this.makeScreenQuad('Postcard_' + targetId, 0.62, 0.44,
            this.iconTextures[t.tex], new Vec4(1, -1, 0, 1));
        node.setPosition(t.x, 0.55, t.z);
        node.setRotation(this.mainCamera.node.rotation);
        // Hidden until the quest is accepted; refreshQuestHud owns visibility.
        node.active = false;
        this.postcardNodes.set(targetId, node);
        if (!this.billboardExtras.includes(node)) this.billboardExtras.push(node);
        console.log('[COURTYARD] postcard prop ' + targetId + ' at ' + t.x + ',' + t.z);
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
        this.frameTick++;
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
            // n5 P1-2: during dialogue the camera pitches down so the whole
            // player pose clears the 176px panel top. The per-frame follow
            // must own this, otherwise a setPosition in openDialogue is
            // overwritten on the next frame.
            const lookY = this.dialogueCamera
                ? CourtyardBootstrap.DIALOGUE_LOOK_Y : 3.5;
            cam.lookAt(new Vec3(this.playerPos.x - 2.5, lookY, this.playerPos.z + 1.5));
        }
        this.updateAnimation();
        this.updateQuestFocus();
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
        this.dialogueCamera = false;
        // The viewer owns the whole screen while a state is on display, so the
        // in-game pause card must not double up with the viewer's own card.
        if (this.pauseRoot) this.pauseRoot.active = false;
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

    private viewerPanel(x: number, y: number, w: number, h: number, tone: Color = new Color(255, 255, 255, 210)): Sprite {
        const p = this.paperPanel(this.studioRoot, x, y, w, h, 'ViewerPanel');
        p.color = tone;
        return p;
    }

    private decoratePaper(node: Node, w: number, h: number): void {
        const doodle = this.uiNode('PaperDoodle', node, 0, 0, w, h);
        const g = doodle.addComponent(Graphics);
        g.strokeColor = new Color(74, 64, 49, 64);
        g.lineWidth = 1;
        g.moveTo(-w / 2 + 18, h / 2 - 22);
        g.lineTo(-w / 2 + 34, h / 2 - 27);
        g.lineTo(-w / 2 + 46, h / 2 - 23);
        g.moveTo(w / 2 - 48, h / 2 - 18);
        g.lineTo(w / 2 - 28, h / 2 - 22);
        g.stroke();
        g.fillColor = new Color(159, 216, 200, 90);
        g.circle(w / 2 - 30, -h / 2 + 22, 2.4);
        g.fill();
        g.fillColor = new Color(138, 100, 37, 75);
        g.circle(w / 2 - 44, -h / 2 + 29, 1.6);
        g.fill();
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
        if (this.actionSub) this.actionSub.color = opts.disabled ? C.faint : C.inkBody;
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
            const titlePanel = this.viewerPanel(0, 15, 880, 430, new Color(250, 247, 239, 215));
            this.decoratePaper(titlePanel.node, 880, 430);
            this.icon(this.studioRoot, 'icon_leaf', 340, 155, 26, C.goldDeep);
            this.icon(this.studioRoot, 'icon_sparkle', -340, -160, 18, C.mintDeep);
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
            this.decoratePaper(p.node, 480, 420);
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

    private resumeFromPause(): void {
        this.clearViewer();
        this.viewerId = '';
        this.cameraMode = 'game';
        this.paused = false;
        this.setUiVisible(true);
        this.unlockInput();
        this.keys.clear();
        this.joy.set(0, 0);
        this.manualMoving = false;
        this.moving = false;
        this.resetJoystick();
        console.log('[COURTYARD] resume from pause player=' + JSON.stringify([this.playerPos.x, this.playerPos.z]));
    }

    private restoreFromPortrait(saved: any): void {
        this.portraitBlocked = false;
        this.viewerId = '';
        this.clearViewer();
        this.setUiVisible(true);
        this.cameraMode = 'game';
        if (saved) {
            this.questState = typeof saved.questState === 'string' && saved.questState !== ''
                ? saved.questState : (saved.accepted ? 'COLLECTING' : 'NOT_STARTED');
            if (Array.isArray(saved.collected)) this.collectedIds = new Set(saved.collected);
            this.gardenerLine = saved.gardenerLine || null;
            this.boardState = saved.boardState;
            this.boardManual = !!saved.boardManual;
            this.refreshQuestHud();
            if (saved.dialogueVisible) {
                this.dialogueVisible = true;
                this.dialoguePage = saved.dialoguePage;
                this.applyDialoguePage();
                this.dialogueRoot.active = true;
                this.scrim.active = true;
                this.lockInput();
            } else if (saved.paused) {
                this.setUiState('pause_default');
                return;
            }
        }
        this.unlockInput();
        this.keys.clear();
        this.joy.set(0, 0);
        this.manualMoving = false;
        this.moving = false;
        console.log('[COURTYARD] restore from portrait player=' + JSON.stringify([this.playerPos.x, this.playerPos.z]));
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
        this.applyCameraPreset(this.cameraPreset);
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
                accepted: this.questState !== 'NOT_STARTED',
                questState: this.questState,
                questFocus: this.questFocusId,
                collected: Array.from(this.collectedIds),
                questTitle: this.questTitle.string,
                soundOn: this.soundOn,
                frameTick: this.frameTick,
                loadErrorCount: this.loadErrors.length,
                failedLoads: this.failedLoads.length,
                moving: this.moving,
                paused: this.paused,
                inputLocked: this.inputLocked,
                boardState: this.boardState,
                cameraMode: this.cameraMode,
                anim: this.currentAnim,
                animNames: this.spine && this.spine.skeletonData ? this.getAnimNames() : [],
                player: [this.playerPos.x, this.playerPos.y, this.playerPos.z],
                camera: this.mainCamera ? [this.mainCamera.node.position.x, this.mainCamera.node.position.y, this.mainCamera.node.position.z] : null,
                viewer: this.viewerId,
                portraitBlocked: this.portraitBlocked,
                loadErrors: this.loadErrors,
                boneBounds: this.spineNativeHeight(),
                metrics: (globalThis as any).__COURTYARD_METRICS__ || null,
                spine: this.spine ? (() => { const u = this.spineNode!.getComponent(UITransform)!; return { width: u.width, height: u.height, premultipliedAlpha: this.spine!.premultipliedAlpha }; })() : null,
            }),
            setUi: (v: boolean) => this.setUiVisible(v),
            setUiState: (id: string) => { this.viewerId = id; this.setUiState(id); },
            focusAsset: (id: string) => { this.focusAsset(id); },
            resetView: () => this.resetView(),
            setCameraPreset: (name: string) => this.applyCameraPreset(name),
            getCameraPreset: () => this.cameraPreset,
            setPause: (v: boolean) => { if (v) { this.setUiState('pause_default'); } else { this.resumeFromPause(); } },
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
            /** harness hook: triggers whatever the current quest focus is */
            interact: () => this.onActionPressed(),
            /** G-harness: resolves once the per-frame focus update actually
             * produced `id` (rAF = real frames), or times out with whatever
             * the current focus is. Null-safe: pass the string 'null'. */
            waitForFocus: (id: string, timeoutMs = 8000) => new Promise<string | null>((resolve) => {
                const want: string | null = id === 'null' ? null : id;
                const t0 = performance.now();
                const tick = () => {
                    if (this.questFocusId === want) { resolve(this.questFocusId); return; }
                    if (performance.now() - t0 > timeoutMs) { resolve(this.questFocusId); return; }
                    requestAnimationFrame(tick);
                };
                requestAnimationFrame(tick);
            }),
            /** G06 harness hooks */
            toggleSound: () => this.toggleSound(),
            fullRestart: () => this.fullRestart(),
            /** G07 harness hook: renders the same failure card maybeFinish uses */
            showRetryCard: () => this.showRetryCard(),
            /** harness hook: walk a straight line until blocked or arrived */
            walkTo: (x: number, z: number, step = 0.25) => {
                const dx = x - this.playerPos.x;
                const dz = z - this.playerPos.z;
                const len = Math.sqrt(dx * dx + dz * dz);
                const n = Math.ceil(len / step);
                for (let i = 0; i < n; i++) {
                    const t0x = this.playerPos.x + dx / n;
                    const t0z = this.playerPos.z + dz / n;
                    this.tryMove(t0x - this.playerPos.x, t0z - this.playerPos.z);
                }
                this.playerAnchor.setPosition(this.playerPos);
                return [this.playerPos.x, this.playerPos.z];
            },
            setPlayer: (x: number, z: number) => { this.playerPos.x = x; this.playerPos.z = z; },
            setMoving: (v: boolean) => { this.manualMoving = v; this.moving = v; },
            reset: () => {
                this.resetQuest();
                this.gardenerLine = null;
                this.closeDialogue();
                this.setUiVisible(true);
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

    private setupOrientation(): void {
        if (typeof window === 'undefined' || !window.addEventListener) return;
        const apply = () => {
            const width = Math.max(1, window.innerWidth);
            const height = Math.max(1, window.innerHeight);
            try { view.setCanvasSize(width, height); } catch (e) { /* headless */ }
            try { view.resizeWithBrowserSize(true); } catch (e) { /* headless */ }
            const portrait = height > width;
            if (portrait && !this.portraitBlocked) {
                this.prePortraitState = {
                    dialogueVisible: this.dialogueVisible,
                    dialoguePage: this.dialoguePage,
                    gardenerLine: this.gardenerLine,
                    paused: this.paused,
                    cameraMode: this.cameraMode,
                    accepted: this.questState !== 'NOT_STARTED',
                    questState: this.questState,
                    collected: Array.from(this.collectedIds),
                    boardState: this.boardState,
                    boardManual: this.boardManual,
                    questTitle: this.questTitle.string,
                    questSub: this.questSub.string,
                    questBadge: this.questBadge.string,
                };
                try {
                    this.viewerId = 'rotate_notice';
                    this.setUiState('rotate_notice');
                    this.portraitBlocked = true;
                } catch (e) {
                    console.error('[COURTYARD] rotate notice failed: ' + String(e));
                }
                return;
            }
            if (!portrait && this.portraitBlocked) {
                const saved = this.prePortraitState;
                this.prePortraitState = null;
                this.restoreFromPortrait(saved);
            }
        };
        window.addEventListener('resize', apply);
        window.addEventListener('orientationchange', apply);
        this.scheduleOnce(apply, 0.1);
    }
}
