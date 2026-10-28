import bpy, math, random, os, json, hashlib, time
from mathutils import Vector

random.seed(841028)
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'renders')
PBR_DIR = os.path.join(ROOT,'assets','textures','pavement_05')
os.makedirs(OUT, exist_ok=True)

def mat(name, color, rough=.78, metallic=0.0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metallic
    if name.startswith(('Warm limestone','Limestone variation','Stone worn','Pale cast','Planter aged')):
        nt=m.node_tree; tc=nt.nodes.new('ShaderNodeTexCoord'); noise=nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=4.2; noise.inputs['Detail'].default_value=5; noise.inputs['Roughness'].default_value=.78
        nt.links.new(tc.outputs['Object'],noise.inputs['Vector'])
        fine=nt.nodes.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value=38; fine.inputs['Detail'].default_value=2.5; nt.links.new(tc.outputs['Object'],fine.inputs['Vector'])
        ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.22; ramp.color_ramp.elements[0].color=(*[v*.66 for v in color],1); ramp.color_ramp.elements[1].position=.78; ramp.color_ramp.elements[1].color=(*[min(1,v*1.27) for v in color],1)
        bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.20; bump.inputs['Distance'].default_value=.05
        bump2=nt.nodes.new('ShaderNodeBump'); bump2.inputs['Strength'].default_value=.12; bump2.inputs['Distance'].default_value=.012
        nt.links.new(noise.outputs['Fac'],ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'],p.inputs['Base Color']); nt.links.new(noise.outputs['Fac'],bump.inputs['Height']); nt.links.new(fine.outputs['Fac'],bump2.inputs['Height']); nt.links.new(bump.outputs['Normal'],bump2.inputs['Normal']); nt.links.new(bump2.outputs['Normal'],p.inputs['Normal'])
        diffuse_path=os.path.join(PBR_DIR,'diffuse.jpg'); normal_path=os.path.join(PBR_DIR,'normal_gl.png'); rough_path=os.path.join(PBR_DIR,'roughness.jpg')
        if all(os.path.isfile(path) for path in [diffuse_path,normal_path,rough_path]):
            mapping=nt.nodes.new('ShaderNodeMapping'); mapping.inputs['Scale'].default_value=(2.4,2.4,1.0); nt.links.new(tc.outputs['Object'],mapping.inputs['Vector'])
            diff=nt.nodes.new('ShaderNodeTexImage'); diff.image=bpy.data.images.load(diffuse_path,check_existing=True); diff.image.filepath='//assets/textures/pavement_05/diffuse.jpg'; nt.links.new(mapping.outputs['Vector'],diff.inputs['Vector'])
            mix=nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type='MIX'; mix.inputs['Fac'].default_value=.035; nt.links.new(ramp.outputs['Color'],mix.inputs['Color1']); nt.links.new(diff.outputs['Color'],mix.inputs['Color2']); nt.links.new(mix.outputs['Color'],p.inputs['Base Color'])
            nr=nt.nodes.new('ShaderNodeTexImage'); nr.image=bpy.data.images.load(normal_path,check_existing=True); nr.image.filepath='//assets/textures/pavement_05/normal_gl.png'; nr.image.colorspace_settings.name='Non-Color'; nt.links.new(mapping.outputs['Vector'],nr.inputs['Vector'])
            normal=nt.nodes.new('ShaderNodeNormalMap'); normal.inputs['Strength'].default_value=.07; nt.links.new(nr.outputs['Color'],normal.inputs['Color']); nt.links.new(normal.outputs['Normal'],bump.inputs['Normal'])
            rough_img=nt.nodes.new('ShaderNodeTexImage'); rough_img.image=bpy.data.images.load(rough_path,check_existing=True); rough_img.image.filepath='//assets/textures/pavement_05/roughness.jpg'; rough_img.image.colorspace_settings.name='Non-Color'; nt.links.new(mapping.outputs['Vector'],rough_img.inputs['Vector'])
            rm=nt.nodes.new('ShaderNodeMapRange'); rm.inputs['From Min'].default_value=.15; rm.inputs['From Max'].default_value=.92; rm.inputs['To Min'].default_value=max(.55,rough*.90); rm.inputs['To Max'].default_value=min(.98,rough*1.10); nt.links.new(rough_img.outputs['Color'],rm.inputs['Value']); nt.links.new(rm.outputs['Result'],p.inputs['Roughness'])
        if not os.path.isfile(os.path.join(PBR_DIR,'roughness.jpg')): p.inputs['Roughness'].default_value=rough
    return m

stone=mat('Warm limestone | cut slabs',(.49,.445,.375),.92)
stone2=mat('Limestone variation',(.56,.515,.445),.90)
stone_edge=mat('Stone worn edges',(.62,.565,.485),.89)
joint=mat('Recessed warm joints',(.37,.315,.25),.96)
dark=mat('Oxidized iron',(.10,.095,.083),.58,.72)
dark2=mat('Iron edge highlights',(.24,.21,.17),.5,.62)
wood=mat('Old stained wood',(.25,.14,.075),.84)
trunkmat=mat('Tree bark warm umber',(.20,.105,.052),.93)
leafm=[mat('Amber leaf %02d'%i,c,.94) for i,c in enumerate([(.035,.020,.012),(.075,.036,.016),(.13,.055,.019),(.20,.083,.026),(.28,.12,.040)])]
leaf_core_m=[mat('Foliage mass shadow',(.16,.068,.024),.96),mat('Foliage mass umber',(.23,.095,.028),.94),mat('Foliage mass amber',(.31,.14,.040),.94)]
grassm=[mat('Dry grass %02d'%i,c,.92) for i,c in enumerate([(.46,.32,.16),(.63,.47,.25),(.74,.61,.39),(.34,.25,.14),(.56,.39,.21)])]
grass_base=mat('Dry grass shaded root mass',(.30,.19,.075),.98)
concrete=mat('Planter aged pale concrete',(.47,.43,.37),.92)
water=mat('Distant blue green water',(.22,.43,.49),.58)
background=mat('Far warm terrain',(.49,.40,.31),1)
earth=mat('Autumn soil beyond platform',(.24,.18,.12),.96)
orange=mat('Safety ochre paint',(.48,.205,.075),.78)

def assign(o,m): o.data.materials.append(m); return o
def cube(name, loc, scale, m, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); assign(o,m)
    if bevel:
        mod=o.modifiers.new('Soft worn arris','BEVEL'); mod.width=bevel; mod.segments=2
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o
def cyl(name, loc, radius, depth, m, verts=48, bevel=.03):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc); o=bpy.context.object; o.name=name; assign(o,m)
    if bevel:
        b=o.modifiers.new('Rounded rim edges','BEVEL'); b.width=bevel; b.segments=2; o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def curve(name, pts, radius, m, res=2, tapered=False):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=12; cu.bevel_depth=radius; cu.bevel_resolution=res
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
    for i,(bp,co) in enumerate(zip(sp.bezier_points,pts)):
        bp.co=co; bp.handle_left_type='AUTO'; bp.handle_right_type='AUTO'
        if tapered: bp.radius=max(.035,1.15-i*.36)
    ob=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(ob); assign(ob,m); return ob
leaf_mesh_cache={}
def leaf(name, loc, size, rot, material):
    # Shared smooth oval leaves read as soft foliage at the fixed camera distance.
    key=material.name
    if key not in leaf_mesh_cache:
        verts=[]; faces=[]; nx=13; ny=7
        for i in range(nx):
            t=i/(nx-1); x=-.86+1.72*t; halfw=.54*(math.sin(math.pi*t)**.70)
            for j in range(ny):
                v=(j/(ny-1))*2-1; verts.append((x,halfw*v,.11*math.sin(math.pi*t)*(1-v*v)))
        for i in range(nx-1):
            for j in range(ny-1):
                a=i*ny+j; faces.append((a,a+ny,a+ny+1,a+1))
        me=bpy.data.meshes.new('Soft tapered autumn leaf mesh'); me.from_pydata(verts,[],faces); me.materials.append(material); me.update(); leaf_mesh_cache[key]=me
    ob=bpy.data.objects.new(name,leaf_mesh_cache[key]); bpy.context.collection.objects.link(ob); ob.location=loc; ob.scale=size; ob.rotation_euler=rot
    for poly in ob.data.polygons: poly.use_smooth=True
    return ob

# scene reset
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.resolution_x=1280; scene.render.resolution_y=719; scene.render.resolution_percentage=50
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=0; scene.view_settings.gamma=1
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.25,.34,.42,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.52

# contiguous stone deck and a single family of large paving slabs
cube('Deep platform plinth left',(-7.10,.40,-.48),(1.30,14.4,.75),joint,.14)
cube('Deep platform plinth right',(2.975,.40,-.48),(9.55,14.4,.75),joint,.14)
cube('Ground plane beneath courtyard',(0,1,-1.36),(24,22,.18),earth,.03)
# Shallow warm bedding fills tile joints while a deliberate notch leaves the stair flight open.
bed_outline=[(-12.5,-10.5),(-6.45,-10.5),(-6.45,-3.45),(-1.85,-3.45),(-1.85,-10.5),(12.5,-10.5),(12.5,12.5),(-12.5,12.5)]
bed_mesh=bpy.data.meshes.new('Shallow warm joint bed mesh'); bed_mesh.from_pydata([(x,y,-.105) for x,y in bed_outline],[],[tuple(range(len(bed_outline)))]); bed_mesh.materials.append(joint); bed_mesh.update()
bed_obj=bpy.data.objects.new('Continuous warm bed below paving',bed_mesh); bpy.context.collection.objects.link(bed_obj)
for iy in range(12):
  y=-8.78+iy*1.48
  row_shift=[-.16,.28,-.05,.18,-.22,.10][iy%6]
  for ix in range(13):
    x=-10.85+ix*1.73+row_shift
    if y < -3.45 and -6.45 < x < -1.80: continue
    w=1.69+random.uniform(-.055,.025); d=1.435+random.uniform(-.035,.025)
    o=cube('Cut limestone slab %02d_%02d'%(iy,ix),(x,y,-.055),(w,d,.18),random.choices([stone,stone2,stone_edge],[.72,.24,.04])[0],.022)
    o.rotation_euler[2]=random.uniform(-.006,.006)
    # A few worn fracture lines interrupt the perfect grid; most slabs stay intact.
    if (ix*7+iy*11)%9==4:
      curve('Fine repaired stone crack',[(x-w*.25,y-d*.38,.039),(x-w*.03,y-d*.08,.040),(x+w*.02,y+d*.16,.040),(x+w*.30,y+d*.34,.039)],.008,joint,1)
# soft edge/bead around landing
cube('Landing front fascia left',(-10.25,-9.42,-.40),(1.25,.22,.65),stone_edge,.07)
cube('Landing front fascia right',(4.65,-9.42,-.40),(13.0,.22,.65),stone_edge,.07)

# broad lower-left stair flight, visibly thick treads and cheeks
for i in range(9):
    z=-.19-i*.14; y=-3.50-i*.36
    cube('Broad worn stair tread %02d'%i,(-4.15,y,z),(4.25,.70,.23),stone_edge if i in (0,6) else stone,.055)
    cube('Step shadow nosing %02d'%i,(-4.15,y-.33,z-.055),(4.22,.055,.055),joint,.018)
cube('Left stair cheek',(-6.36,-5.12,-.96),(.36,3.70,1.15),concrete,.09)
cube('Right stair cheek',(-1.94,-5.12,-.96),(.32,3.70,1.15),concrete,.08)
# railings with uprights, top rails and secondary rail
for side in (-1,1):
    x=-4.15+side*1.75
    for j in range(7):
        y=-3.35-j*.38; z=-.05-j*.14
        curve('Stair iron newel',[(x,y,-.12),(x,y,z+.96)],.035,dark,2)
    curve('Stair handrail',[(x,-3.30,.93),(x,-6.65,-.23)],.07,dark,3)
    curve('Stair lower rail',[(x,-3.30,.35),(x,-6.65,-.80)],.035,dark2,2)
# front edge rails
for x0,x1 in [(-10.6,-8.0),(-1.70,1.5),(4.1,9.8)]:
  for x in [x0,(x0+x1)/2,x1]: curve('Landing rail post',[(x,-9.28,-.24),(x,-9.28,.62)],.035,dark,2)
  curve('Landing iron rail',[(x0,-9.28,.62),(x1,-9.28,.62)],.065,dark,2)

# tree: branching tapered curves with intentionally open, asymmetrical crown
tx,ty=-5.05,2.55
curve('Main old tree trunk',[(tx,ty,.05),(tx+.10,ty,1.05),(tx-.12,ty,2.15),(tx+.18,ty,3.05),(tx+.50,ty,3.9)],.27,trunkmat,3,True)
branches=[((tx,ty,1.45),(tx-1.0,ty-.12,2.0),(tx-1.72,ty+.02,2.55)),((tx-.02,ty,1.85),(tx-.55,ty+.15,2.55),(tx-.72,ty+.25,3.15)),((tx+.05,ty,2.0),(tx+.90,ty+.05,2.5),(tx+1.35,ty+.15,3.1)),((tx+.18,ty,2.45),(tx+.15,ty-.20,3.05),(tx-.08,ty-.25,3.55)),((tx+.2,ty,2.25),(tx+1.18,ty-.18,2.5),(tx+1.85,ty-.25,2.8)),((tx-.05,ty,1.75),(tx-1.22,ty-.2,1.95),(tx-1.95,ty-.3,2.25)),((tx,ty,2.15),(tx-.95,ty-.15,2.75),(tx-1.50,ty-.25,3.15)),((tx+.05,ty,1.95),(tx+.68,ty-.2,3.0),(tx+1.12,ty-.28,3.35)),((tx+.2,ty,2.35),(tx+1.35,ty+.12,2.85),(tx+2.0,ty+.18,3.15))]
for n,b in enumerate(branches): curve('Tree primary branch %02d'%n,b,.125,trunkmat,3,True)
# Build a second twig tier so the visible leaf mass follows branching paths instead of one flat fan.
twigs=[]
for bi,b in enumerate(branches):
    start=Vector(b[1]); end=Vector(b[2]); axis=end-start
    for k in range(3):
        t=.26+k*.22; root=start+axis*t
        side=random.choice([-1,1]); tip=root+Vector((side*random.uniform(.24,.62),random.uniform(-.25,.25),random.uniform(.28,.72)))
        mid=(root+tip)*.5+Vector((random.uniform(-.12,.12),0,random.uniform(.06,.18)))
        curve('Fine branching twig', [root,mid,tip],.045,trunkmat,2,True)
        twigs.append((root,tip,bi,k))
# Each twig gets several compact, rounded leaf sprays with varied orientation and open gaps.
for root,tip,bi,k in twigs:
    axis=tip-root
    for j in range(9):
        t=(j+.4)/9; center=root+axis*t
        if (bi in (0,5) and j in (4,)) or (bi==2 and k==1 and j==4): continue
        for q in range(10):
            p=center+Vector((random.uniform(-.10,.10),random.uniform(-.16,.16),random.uniform(-.09,.14)))
            rot=(random.uniform(-.9,.9),random.uniform(-.9,.9),random.uniform(-math.pi,math.pi))
            size=(random.uniform(.16,.25),random.uniform(.070,.12),random.uniform(.06,.10))
            leaf('Natural rounded amber leaf',p,size,rot,random.choices(leafm,[.28,.30,.22,.13,.07])[0])
# Low-volume overlapping foliage masses knit the fine leaves into a readable canopy.
core_mesh_cache={}
def foliage_mass(name,loc,scale,material):
    key=material.name
    if key not in core_mesh_cache:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1)
        temp=bpy.context.object; core_mesh_cache[key]=temp.data; core_mesh_cache[key].name='Smooth foliage mass mesh'; core_mesh_cache[key].materials.append(material); bpy.data.objects.remove(temp,do_unlink=True)
    ob=bpy.data.objects.new(name,core_mesh_cache[key]); bpy.context.collection.objects.link(ob); ob.location=loc; ob.scale=scale
    for poly in ob.data.polygons: poly.use_smooth=True
    return ob
for bi,b in enumerate(branches):
    start=Vector(b[1]); end=Vector(b[2]); axis=end-start
    for t in (.48,.78):
        c=start+axis*t+Vector((random.uniform(-.12,.12),random.uniform(-.12,.12),random.uniform(-.08,.12)))
        foliage_mass('Joined autumn leaf cluster',c,(random.uniform(.14,.21),random.uniform(.11,.16),random.uniform(.12,.19)),leaf_core_m[bi%3])
# planter at base
cyl('Tree square planter base',(tx,ty,.12),.86,.28,concrete,4,.05)

# midground industrial assembly, pipework, grated cage and service platforms
cube('Service platform base',(-.15,2.35,.18),(4.1,2.25,.34),dark,.08)
cube('Service platform pale top',(-.15,2.35,.37),(3.9,2.08,.10),stone_edge,.035)
for i in range(5): cube('Open metal deck grate',(-1.55+i*.68,2.33,.44),(.49,1.85,.045),dark2,.012)
# equipment cage / gantry
for x in [-1.65,-.45,.65,1.50]:
  curve('Gantry upright',[(x,2.9,.48),(x,2.9,2.55)],.055,dark,2)
for z in [.72,2.48]: curve('Gantry crossbeam',[(-1.65,2.9,z),(1.5,2.9,z)],.06,dark2,2)
for i in range(7): curve('Gantry diagonal brace',[(-1.6+i*.50,2.9,.75),(-1.15+i*.50,2.9,2.45)],.025,dark,1)
# pipe runs and valves
curve('Large service pipe',[(.5,1.1,.62),(.5,1.45,1.0),(.5,2.15,1.0),(1.95,2.15,1.0),(1.95,3.45,1.0)],.18,concrete,3)
curve('Dark pressure pipe',[(1.25,.85,.70),(1.25,1.35,1.55),(1.25,2.1,1.55),(2.12,2.1,1.55)],.085,dark2,2)
for x in [1.25,1.85]: cyl('Pipe flange',(x,2.1,1.55),.17,.09,orange,24,.015)
cube('Electrical cabinet',(-1.1,1.3,.98),(.64,.68,1.05),dark2,.055)
for z in [.85,1.05,1.25]: cube('Cabinet vent',(-1.1,.946,z),(.4,.025,.045),dark,.008)
cyl('Pressure vessel',(2.05,1.28,1.08),.42,1.1,concrete,32,.07)
for z in [.58,1.55]: cyl('Tank iron band',(2.05,1.28,z),.44,.08,dark,32,.015)
for x in [-.7,.5,1.75]:
  curve('Fence support',[(x,3.47,.47),(x,3.47,1.85)],.04,dark,2)
for z in [.68,1.12,1.56]: curve('Fence rail',[(-.72,3.47,z),(1.8,3.47,z)],.025,dark2,1)
# Industrial ventilation wheel and its support are a readable silhouette behind the pipe group.
fan_center=(.35,4.05,2.55)
bpy.ops.mesh.primitive_torus_add(major_radius=.78,minor_radius=.075,major_segments=48,minor_segments=12,location=fan_center,rotation=(math.pi/2,0,0))
fan_ring=bpy.context.object; fan_ring.name='Ventilator outer iron ring'; assign(fan_ring,dark)
cyl('Ventilator axle',fan_center,.15,.35,dark2,32,.025).rotation_euler[0]=math.pi/2
for i in range(12):
    a=i*math.tau/12
    curve('Ventilator radial spoke',[(fan_center[0]+.13*math.cos(a),fan_center[1]-.02,fan_center[2]+.13*math.sin(a)),(fan_center[0]+.72*math.cos(a),fan_center[1]-.02,fan_center[2]+.72*math.sin(a))],.025,dark2,1)
for i in range(6):
    a=i*math.tau/6+.2
    p1=(fan_center[0]+.22*math.cos(a),fan_center[1]-.045,fan_center[2]+.22*math.sin(a))
    p2=(fan_center[0]+.60*math.cos(a+.6),fan_center[1]-.045,fan_center[2]+.60*math.sin(a+.6))
    curve('Ventilator curved blade', [p1,((p1[0]+p2[0])*.5,fan_center[1]-.07,(p1[2]+p2[2])*.5),p2],.055,dark2,2)
cube('Ventilator mounting bracket',(.35,4.05,1.65),(1.45,.28,.18),dark,.04)
# A high retaining face on the right frames the courtyard and anchors the industrial setting.
cube('Right garden retaining wall',(9.1,2.85,1.25),(1.65,9.2,2.75),concrete,.16)
cube('Retaining wall cap',(8.65,2.85,2.68),(2.65,9.35,.22),stone_edge,.07)
for x,z,r in [(8.20,.55,.09),(8.38,.84,.065)]:
    curve('Wall service conduit',[(x,-1.6,z),(x,1.6,z+.04),(x,5.4,z+.05),(x,7.0,z+.02)],r,dark2,2)
# Service ladder, conduit clamps and a pair of readable access panels.
for x in [-2.0,-1.48]: curve('Service ladder stile',[(x,3.75,.42),(x,3.75,2.35)],.045,dark2,2)
for z in [.58,.88,1.18,1.48,1.78,2.08]: curve('Service ladder rung',[(-2.0,3.73,z),(-1.48,3.73,z)],.025,dark,1)
cube('Pump access housing',(-2.15,1.58,.80),(.78,.82,.72),wood,.08)
for z in [.62,.80,.98]: cube('Pump housing vent',(-2.15,1.15,z),(.46,.025,.035),dark,.008)
for x in [-2.40,-1.92]:
  for z in [.52,1.08]: cyl('Pump panel bolt',(x,1.12,z),.035,.025,dark2,12,.005).rotation_euler[0]=math.pi/2

# cylindrical raised planters with concrete shafts, heavy dark vertical ribs and dense sculptural grass
def planter(cx,cy,r,h,top):
    base=.03
    cyl('Circular footing',(cx,cy,base+.08),r+.12,.16,dark,64,.025)
    cyl('Pale cast planter wall',(cx,cy,base+h/2),r,h,concrete,64,.055)
    cyl('Dark continuous crown ring',(cx,cy,base+h-.04),r+.065,.22,dark,64,.025)
    cyl('Inner soil',(cx,cy,base+h+.045),r-.12,.11,joint,48,.02)
    for k in range(24):
      a=2*math.pi*k/24
      rr=r+.028
      ob=cube('Vertical iron planter rib',(cx+rr*math.cos(a),cy+rr*math.sin(a),base+h/2),(0.075,.075,h-.22),dark2,.018)
      ob.rotation_euler[2]=a
    # A low irregular root mound unifies the bases; the grass clumps conceal it in the final view.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=(cx,cy,base+h+.12))
    mound=bpy.context.object; mound.name='Continuous shaded grass root mound'; mound.scale=(r*.76,r*.70,.24); assign(mound,grass_base)
    # Wind-shaped clumps: each tuft has a shared direction and height profile, with fine tapered strands.
    for cluster in range(26):
      ca=random.random()*math.tau; cr=random.uniform(0,r*.52)
      ccx=cx+cr*math.cos(ca); ccy=cy+cr*math.sin(ca)
      wind=ca+random.uniform(-.72,.72)
      for k in range(32):
        a=random.random()*math.tau; rr=random.uniform(0,r*.18); hh=random.uniform(.38,.92)
        x=ccx+rr*math.cos(a); y=ccy+rr*math.sin(a)
        lean=random.uniform(.72,1.48); phi=wind+random.uniform(-.48,.48)
        pts=[(x,y,base+h+.14),(x+lean*.18*math.cos(phi),y+lean*.18*math.sin(phi),base+h+.14+hh*.28),(x+lean*.58*math.cos(phi),y+lean*.58*math.sin(phi),base+h+.14+hh*.72),(x+lean*math.cos(phi),y+lean*math.sin(phi),base+h+.14+hh)]
        cu=bpy.data.curves.new('Arcing tapered dry grass strand','CURVE'); cu.dimensions='3D'; cu.resolution_u=6; cu.bevel_depth=random.uniform(.010,.016); cu.bevel_resolution=2
        sp=cu.splines.new('BEZIER'); sp.bezier_points.add(3)
        for bp,p,rad in zip(sp.bezier_points,pts,[.72,1.0,.55,.015]): bp.co=p; bp.radius=rad; bp.handle_left_type='AUTO'; bp.handle_right_type='AUTO'
        ob=bpy.data.objects.new('Wind swept grass strand',cu); bpy.context.collection.objects.link(ob); assign(ob,random.choices(grassm,[.25,.27,.20,.12,.16])[0])
        if k%4==0:
          tip=Vector(pts[-1])
          for seed in range(4):
            ang=phi+random.uniform(-1.3,1.3); length=random.uniform(.12,.28)
            end=tip+Vector((length*math.cos(ang),length*math.sin(ang),random.uniform(-.02,.16)))
            mid=(tip+end)*.5+Vector((0,0,random.uniform(.035,.10)))
            curve('Feathery grass seed plume',[tip,mid,end],.004,random.choice(grassm),1,True)
    # The fringe has shorter outward-curving blades so the top does not read as a clipped cylinder.
    for k in range(110):
      a=random.random()*math.tau; rr=r*random.uniform(.40,.65); x=cx+rr*math.cos(a); y=cy+rr*math.sin(a); h=random.uniform(.34,.70)
      curve('Splayed short grass fringe',[(x,y,base+h+.10),(x+.18*math.cos(a),y+.18*math.sin(a),base+h+.10+h*.36),(x+.48*math.cos(a),y+.48*math.sin(a),base+h*.60)],.022,random.choice(grassm),2,True)

planter(2.45,3.35,1.58,1.75,3)
planter(5.65,4.15,1.52,2.30,3.2)
planter(6.65,1.35,1.05,1.38,2.5)
# One sagging maintenance bunting line, rather than repeated tabs around every rim.
curve('Bunting support cord',[(1.15,2.25,2.54),(3.55,2.72,2.35),(6.05,3.35,2.72)],.018,dark,2)
flagm=[orange,mat('Faded teal fabric',(.27,.42,.39),.9),mat('Dusty cream fabric',(.64,.55,.40),.9)]
for i in range(11):
    t=(i+.4)/11; x=1.15+4.90*t; y=2.25+1.10*t; z=2.54+.18*t-.26*math.sin(math.pi*t)
    width=.22; h=.32+random.uniform(-.04,.04)
    me=bpy.data.meshes.new('Triangular cloth pennant'); me.from_pydata([(-width/2,0,0),(width/2,0,0),(random.uniform(-.035,.035),.015,-h)],[],[(0,1,2)]); me.materials.append(flagm[i%3])
    ob=bpy.data.objects.new('Weathered cloth pennant',me); bpy.context.collection.objects.link(ob); ob.location=(x,y,z)

# small tree / work cart left midground for scale and narrative
cube('Maintenance cart chassis',(-6.2,.20,.45),(2.0,.85,.36),orange,.08)
cube('Maintenance tug rear counterweight',(-6.85,.20,.72),(.60,.80,.34),orange,.06)
cube('Maintenance tug hood',(-5.75,.20,.72),(.82,.80,.30),orange,.07)
for x in [-6.85,-5.55]:
  for y in [-.22,.62]: cyl('Cart rubber wheel',(x,y,.23),.29,.15,dark,24,.025).rotation_euler[0]=math.pi/2
cube('Tug cabin roof',(-6.45,.20,1.42),(.86,.88,.12),dark,.04)
for x in [-6.83,-6.10]:
  for y in [-.18,.57]: curve('Tug protective cab post',[(x,y,.82),(x,y,1.40)],.035,dark2,2)
cube('Tug seat',(-6.48,.43,.98),(.46,.34,.16),wood,.04)
cube('Tug dashboard',(-6.04,.18,1.06),(.18,.52,.18),dark2,.025)
# Fork mast and forks make the orange silhouette read as a small service forklift.
for x in [-5.34,-5.07]: curve('Forklift vertical mast',[(x,.20,.44),(x,.20,1.72)],.045,dark,2)
for z in [.60,1.56]: curve('Forklift mast crossbar',[(-5.38,.20,z),(-5.02,.20,z)],.035,dark2,1)
for y in [-.06,.36]: curve('Forklift tine',[(-5.22,y,.40),(-4.25,y,.40)],.055,dark,2)
cube('Tug amber warning lamp',(-6.45,.20,1.53),(.12,.12,.12),orange,.025)

# Distance band: an irregular watercourse, soft sand banks and a gradual color horizon.
def flat_patch(name, points, z, material):
    me=bpy.data.meshes.new(name+' mesh'); me.from_pydata([(x,y,z) for x,y in points],[],[tuple(range(len(points)))]); me.materials.append(material); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); return ob
near=[(-3.8,7.75),(-2.1,7.48),(-.3,7.72),(1.5,7.46),(3.3,7.78),(5.1,7.52),(7.0,7.78)]
far=[(7.0,11.05),(5.1,10.82),(3.3,11.12),(1.5,10.84),(-.3,11.10),(-2.1,10.82),(-3.8,11.05)]
flat_patch('Curved blue green watercourse',near+far,-.09,water)
curve('Soft near water edge',[(x,y,.015) for x,y in near],.045,stone_edge,3)
curve('Soft far water edge',[(x,y,.015) for x,y in far[::-1]],.055,background,3)
for i in range(5):
    x=-4.8+i*2.35; y=9.45+random.uniform(-.16,.16)
    curve('Quiet water ripple',[(x,y,.0),(x+.55,y+.05,.0),(x+1.2,y-.025,.0)],.012,stone_edge,2)
flat_patch('Far pale sand bank',[(-12,10.9),(-8,10.7),(-4,11.0),(0,10.72),(4,11.02),(8,10.74),(12,11.0),(12,12.6),(-12,12.6)],-.05,background)
# Gradient panel blends blue-gray distance into the warm ground at the horizon.
backmat=mat('Blue to warm atmospheric gradient',(.2,.32,.40),1)
nt=backmat.node_tree; bs=nt.nodes.get('Principled BSDF'); tc=nt.nodes.new('ShaderNodeTexCoord'); sep=nt.nodes.new('ShaderNodeSeparateXYZ'); ramp=nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(tc.outputs['Generated'],sep.inputs['Vector']); nt.links.new(sep.outputs['Z'],ramp.inputs['Fac'])
cr=ramp.color_ramp; cr.elements.remove(cr.elements[1]); cr.elements[0].position=0.0; cr.elements[0].color=(.48,.38,.27,1)
for pos,col in [(.20,(.56,.47,.36,1)),(.30,(.39,.44,.43,1)),(.43,(.26,.39,.45,1)),(.72,(.25,.37,.44,1)),(1.0,(.19,.29,.37,1))]:
    e=cr.elements.new(pos); e.color=col
nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
def skyline(name, profile, y, depth, material):
    n=len(profile); verts=[(x,y,z) for x,z in profile]+[(x,y+depth,z) for x,z in profile]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    for i in range(n-1): faces.append((i,i+1,n+i+1,n+i))
    me=bpy.data.meshes.new(name+' terrain mesh'); me.from_pydata(verts,[],faces); me.materials.append(material); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); return ob
skyline('Soft blue distant ridge',[(-14,-.55),(-10,.4),(-7,.15),(-4,1.1),(-1,.45),(3,1.3),(6,.5),(10,1.0),(14,-.4)],14.3,.3,backmat)
skyline('Warm low shoreline',[(-13,-.8),(-9,-.05),(-6,-.20),(-3,.30),(0,-.05),(4,.35),(8,-.10),(13,-.7)],12.45,.25,background)

# camera and lighting
camd=bpy.data.cameras.new('P1 fixed still camera'); cam=bpy.data.objects.new('P1 fixed still camera',camd); bpy.context.collection.objects.link(cam)
cam.location=(.25,-25.0,15.2); target=Vector((0.0,.35,.95)); cam.rotation_euler=(target-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); camd.lens=53; camd.sensor_width=36; camd.dof.use_dof=True; camd.dof.focus_distance=27.0; camd.dof.aperture_fstop=5.6; scene.camera=cam
ld=bpy.data.lights.new('Warm late afternoon key','AREA'); lo=bpy.data.objects.new('Warm late afternoon key',ld); bpy.context.collection.objects.link(lo); lo.location=(-5,-1,12); ld.energy=950; ld.color=(1.0,.82,.64); ld.size=4.4; lo.rotation_euler=(Vector((0,1,0))-lo.location).to_track_quat('-Z','Y').to_euler()
ld2=bpy.data.lights.new('Cool sky fill','AREA'); lo2=bpy.data.objects.new('Cool sky fill',ld2); bpy.context.collection.objects.link(lo2); lo2.location=(2,5,9); ld2.energy=300; ld2.color=(.62,.78,1.0); ld2.size=9; lo2.rotation_euler=(Vector((0,1,0))-lo2.location).to_track_quat('-Z','Y').to_euler()
sun_data=bpy.data.lights.new('Warm directional afternoon sun','SUN'); sun=bpy.data.objects.new('Warm directional afternoon sun',sun_data); bpy.context.collection.objects.link(sun); sun.location=(-8,-5,10); sun_data.energy=2.25; sun_data.color=(1.0,.80,.58); sun_data.angle=.09; sun.rotation_euler=(Vector((0,1,0))-sun.location).to_track_quat('-Z','Y').to_euler()
scene.render.image_settings.color_mode='RGBA'; scene.camera.data.lens=53
scene.render.filepath=os.path.join(OUT,'03_final.png')

# Save editable source with final resolution settings, then make a low-cost preview render.
scene.render.resolution_x=1920; scene.render.resolution_y=1078; scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'scene.blend'))
scene.render.resolution_percentage=50
start=time.time(); bpy.ops.render.render(write_still=True); elapsed=time.time()-start
with open(os.path.join(ROOT,'render_log.json'),'w',encoding='utf-8') as f:
 json.dump({'command':'blender -b scene.blend -P build_scene.py','engine':scene.render.engine,'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'camera_location':list(cam.location),'camera_rotation_euler':list(cam.rotation_euler),'lens_mm':camd.lens,'render_seconds':round(elapsed,2),'object_count':len(scene.objects)},f,indent=2)
