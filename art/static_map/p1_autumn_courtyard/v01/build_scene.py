import bpy, math, random, os, json, hashlib, time
from mathutils import Vector

random.seed(841028)
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'renders')
os.makedirs(OUT, exist_ok=True)

def mat(name, color, rough=.78, metallic=0.0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metallic
    if name.startswith(('Warm limestone','Limestone variation','Stone worn','Pale cast','Planter aged')):
        nt=m.node_tree; tex=nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=13; tex.inputs['Detail'].default_value=4; tex.inputs['Roughness'].default_value=.72
        ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.18; ramp.color_ramp.elements[0].color=(*[v*.79 for v in color],1); ramp.color_ramp.elements[1].position=.82; ramp.color_ramp.elements[1].color=(*[min(1,v*1.18) for v in color],1)
        bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.16; bump.inputs['Distance'].default_value=.045
        nt.links.new(tex.outputs['Fac'],ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'],p.inputs['Base Color']); nt.links.new(tex.outputs['Fac'],bump.inputs['Height']); nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m

stone=mat('Warm limestone | cut slabs',(.53,.385,.255),.84)
stone2=mat('Limestone variation',(.61,.455,.31),.82)
stone_edge=mat('Stone worn edges',(.63,.485,.34),.8)
joint=mat('Recessed warm joints',(.27,.22,.18),.96)
dark=mat('Oxidized iron',(.10,.095,.083),.58,.72)
dark2=mat('Iron edge highlights',(.24,.21,.17),.5,.62)
wood=mat('Old stained wood',(.25,.14,.075),.84)
trunkmat=mat('Tree bark warm umber',(.20,.105,.052),.93)
leafm=[mat('Amber leaf %02d'%i,c,.9) for i,c in enumerate([(.18,.055,.018),(.28,.095,.026),(.38,.15,.040),(.24,.075,.023),(.46,.20,.052)])]
grassm=[mat('Dry grass %02d'%i,c,.92) for i,c in enumerate([(.49,.31,.13),(.70,.49,.22),(.82,.65,.34),(.36,.25,.13),(.61,.40,.17)])]
concrete=mat('Planter aged pale concrete',(.47,.43,.37),.92)
water=mat('Distant blue green water',(.19,.34,.38),.55)
background=mat('Far warm terrain',(.49,.40,.31),1)
earth=mat('Autumn soil beyond platform',(.24,.18,.12),.96)
orange=mat('Safety ochre paint',(.67,.30,.095),.72)

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
def curve(name, pts, radius, m, res=2):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=12; cu.bevel_depth=radius; cu.bevel_resolution=res
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
    for bp,co in zip(sp.bezier_points,pts): bp.co=co; bp.handle_left_type='AUTO'; bp.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(ob); assign(ob,m); return ob
def leaf(name, loc, size, rot, material):
    # Gently cupped pointed leaf mesh, long axis local X; avoids ball-shaped canopy clumps.
    verts=[(-1,0,0),(-.78,-.30,.015),(-.34,-.52,.035),(.28,-.46,.05),(.76,-.26,.025),(1,0,0),(.76,.26,.025),(.28,.46,.05),(-.34,.52,.035),(-.78,.30,.015),(0,0,.13),(0,0,-.07)]
    faces=[]
    for i in range(10): faces.append((i,(i+1)%10,10))
    for i in range(10): faces.append(((i+1)%10,i,11))
    me=bpy.data.meshes.new(name+' mesh'); me.from_pydata(verts,[],faces); me.materials.append(material); ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.location=loc; ob.scale=size; ob.rotation_euler=rot; return ob

# scene reset
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.resolution_x=1280; scene.render.resolution_y=719; scene.render.resolution_percentage=50
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=0; scene.view_settings.gamma=1
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.31,.36,.43,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.38

# contiguous stone deck and a single family of large paving slabs
cube('Deep platform plinth left',(-7.10,.40,-.48),(1.30,14.4,.75),joint,.14)
cube('Deep platform plinth right',(2.975,.40,-.48),(9.55,14.4,.75),joint,.14)
cube('Ground plane beneath courtyard',(0,1,-1.36),(90,90,.18),earth,.03)
for iy in range(10):
  y=-5.90+iy*1.48
  for ix in range(9):
    x=-7.05+ix*1.73 + (0.12 if iy%2 else 0)
    if y < -3.45 and -6.45 < x < -1.80: continue
    w=1.695+random.uniform(-.02,.02); d=1.445+random.uniform(-.018,.018)
    o=cube('Cut limestone slab %02d_%02d'%(iy,ix),(x,y,-.055),(w,d,.18),random.choices([stone,stone2,stone_edge],[.76,.21,.03])[0],.045)
    o.rotation_euler[2]=random.uniform(-.006,.006)
# soft edge/bead around landing
cube('Landing front fascia left',(-6.85,-6.78,-.40),(.75,.22,.65),stone_edge,.07)
cube('Landing front fascia right',(2.78,-6.78,-.40),(9.0,.22,.65),stone_edge,.07)

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
for x0,x1 in [(-7.1,-6.52),(-1.70,1.5),(4.1,7.1)]:
  for x in [x0,(x0+x1)/2,x1]: curve('Landing rail post',[(x,-6.62,-.24),(x,-6.62,.62)],.035,dark,2)
  curve('Landing iron rail',[(x0,-6.62,.62),(x1,-6.62,.62)],.065,dark,2)

# tree: branching tapered curves with intentionally open, asymmetrical crown
tx,ty=-5.05,2.55
curve('Main old tree trunk',[(tx,ty,.05),(tx+.10,ty,1.05),(tx-.12,ty,2.15),(tx+.18,ty,3.05),(tx+.50,ty,3.9)],.25,trunkmat,3)
branches=[((tx,ty,1.45),(tx-1.0,ty-.12,2.0),(tx-1.72,ty+.02,2.55)),((tx-.02,ty,1.85),(tx-.55,ty+.15,2.55),(tx-.72,ty+.25,3.15)),((tx+.05,ty,2.0),(tx+.90,ty+.05,2.5),(tx+1.35,ty+.15,3.1)),((tx+.18,ty,2.45),(tx+.15,ty-.20,3.05),(tx-.08,ty-.25,3.55)),((tx+.2,ty,2.25),(tx+1.18,ty-.18,2.5),(tx+1.85,ty-.25,2.8)),((tx-.05,ty,1.75),(tx-1.22,ty-.2,1.95),(tx-1.95,ty-.3,2.25)),((tx,ty,2.15),(tx-.95,ty-.15,2.75),(tx-1.50,ty-.25,3.15)),((tx+.05,ty,1.95),(tx+.68,ty-.2,3.0),(tx+1.12,ty-.28,3.35)),((tx+.2,ty,2.35),(tx+1.35,ty+.12,2.85),(tx+2.0,ty+.18,3.15))]
for n,b in enumerate(branches): curve('Tree main branch %02d'%n,b,.115-trunc if False else .105,trunkmat,3)
# leaf sprays placed on branch line in irregular drifts, not a closed spherical shell
clusters=[]
for bi,b in enumerate(branches):
    a=Vector(b[1]); e=Vector(b[2]); direction=e-a
    # Alternate technique: small fan-shaped twig sprays rather than evenly spaced leaf cards.
    for j in range(18):
        t=(j+.35)/18; center=a+direction*t
        center.x+=random.uniform(-.25,.25); center.y+=random.uniform(-.22,.22); center.z+=random.uniform(-.20,.24)
        if (bi in (0,5) and 7<=j<=10) or (bi==2 and 8<=j<=10): continue
        for q in range(random.randint(4,6)):
            p=center+Vector((random.uniform(-.18,.18),random.uniform(-.13,.13),random.uniform(-.13,.16)))
            ang=random.uniform(-1.2,1.2)+q*.34
            s=(random.uniform(.31,.48),random.uniform(.12,.23),random.uniform(.12,.24))
            leaf('Clustered fan of amber leaves',p,s,(random.uniform(-.8,.8),random.uniform(-.8,.8),ang),random.choice(leafm))
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
    # small ochre pennant trim under the lip
    for k in range(20):
      a=2*math.pi*k/20
      p=(cx+(r+.09)*math.cos(a),cy+(r+.09)*math.sin(a),base+h-.23)
      leaf('Small faded pennant',p,(.13,.025,.09),(0,0,a),orange)
    # thick root mound gives connected grass silhouette
    for k in range(46):
      a=random.random()*math.tau; rr=random.uniform(0,r*.55)
      leaf('Dense dry grass root tuft',(cx+rr*math.cos(a),cy+rr*math.sin(a),base+h+.12+random.uniform(-.03,.10)),(random.uniform(.22,.42),random.uniform(.20,.37),random.uniform(.12,.22)),(0,0,a),random.choice(grassm))
    # smooth curved blades, multiple layers and varied lean; tapered bevel via poly curve radii
    for k in range(820):
      a=random.random()*math.tau; rr=random.uniform(0,r*.72); hh=random.uniform(.48,1.22)
      x=cx+rr*math.cos(a); y=cy+rr*math.sin(a); lean=random.uniform(.36,1.00); phi=random.uniform(2.4,3.75)+random.uniform(-.55,.55)
      pts=[(x,y,base+h+.12),(x+lean*.36*math.cos(phi),y+lean*.36*math.sin(phi),base+h+.12+hh*.50),(x+lean*math.cos(phi),y+lean*math.sin(phi),base+h+.12+hh)]
      cu=bpy.data.curves.new('Curved tapered grass blade','CURVE'); cu.dimensions='3D'; cu.resolution_u=5; cu.bevel_depth=.048; cu.bevel_resolution=1
      sp=cu.splines.new('BEZIER'); sp.bezier_points.add(2)
      for bp,p,rad in zip(sp.bezier_points,pts,[.9,.65,.02]): bp.co=p; bp.radius=rad; bp.handle_left_type='AUTO'; bp.handle_right_type='AUTO'
      ob=bpy.data.objects.new('Fine dry grass blade',cu); bpy.context.collection.objects.link(ob); assign(ob,random.choice(grassm))
    # outward shaggy rim blades
    for k in range(70):
      a=random.random()*math.tau; x=cx+(r*.57)*math.cos(a); y=cy+(r*.57)*math.sin(a); h=random.uniform(.4,.85)
      curve('Splayed planter edge grass',[(x,y,base+h+.1),(x+.38*math.cos(a),y+.38*math.sin(a),base+h+.1+h*.55)],.027,random.choice(grassm),1)

planter(2.45,3.35,1.58,1.75,3)
planter(5.65,4.15,1.52,2.30,3.2)
planter(6.65,1.35,1.05,1.38,2.5)

# small tree / work cart left midground for scale and narrative
cube('Maintenance cart chassis',(-6.2,.20,.45),(2.0,.85,.36),orange,.08)
for x in [-6.85,-5.55]:
  for y in [-.22,.62]: cyl('Cart rubber wheel',(x,y,.23),.29,.15,dark,24,.025).rotation_euler[0]=math.pi/2
cube('Cart windshield',(-6.2,.18,1.05),(.92,.04,.55),dark2,.025)
cube('Cart seat',(-6.2,.48,.90),(.52,.38,.16),wood,.04)

# distance band: softened blue water and sand banks, deliberately low contrast
cube('Far cool water channel',(0,6.8,-.18),(18,4.2,.10),water,.06)
for i in range(5):
    x=-7+i*3.2
    ob=cube('Distant pale sand bank',(x,8.2,.02),(3.2,1.8,.24),background,.18); ob.rotation_euler[2]=random.uniform(-.08,.08)
curve('Water edge far', [(-8,5.45,.02),(-4,5.25,.02),(0,5.52,.02),(4,5.28,.02),(8,5.50,.02)],.12,stone_edge,3)
# layered distant autumn silhouettes and a cool haze wall give the upper band a soft horizon
backmat=mat('Blue grey distant atmospheric backdrop',(.13,.27,.37),1)
cube('Soft distant horizon panel',(0,12.8,3.3),(30,.18,12),backmat,0)
for i,(x,y,z,s) in enumerate([(-8.0,9.4,1.0,1.2),(-5.3,10.0,1.2,1.5),(-2.7,9.8,.9,1.1),(3.0,10.1,1.2,1.45),(5.8,9.6,1.0,1.25),(8.0,10.2,1.4,1.6)]):
    for q in range(25):
        ang=random.random()*math.tau; rr=random.uniform(0,s*.75)
        leaf('Soft distant autumn foliage',(x+rr*math.cos(ang),y+rr*math.sin(ang),z+1.0+random.uniform(-.2,.7)),(random.uniform(.35,.70),random.uniform(.30,.60),random.uniform(.28,.60)),(random.uniform(-.4,.4),random.uniform(-.4,.4),ang),random.choice(leafm))

# camera and lighting
camd=bpy.data.cameras.new('P1 fixed still camera'); cam=bpy.data.objects.new('P1 fixed still camera',camd); bpy.context.collection.objects.link(cam)
cam.location=(.25,-19.5,12.0); target=Vector((0.0,-1.25,.45)); cam.rotation_euler=(target-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); camd.lens=46; camd.sensor_width=36; camd.dof.use_dof=True; camd.dof.focus_distance=22.5; camd.dof.aperture_fstop=5.6; scene.camera=cam
ld=bpy.data.lights.new('Warm late afternoon key','AREA'); lo=bpy.data.objects.new('Warm late afternoon key',ld); bpy.context.collection.objects.link(lo); lo.location=(-5,-1,12); ld.energy=1900; ld.size=6.5; lo.rotation_euler=(Vector((0,1,0))-lo.location).to_track_quat('-Z','Y').to_euler()
ld2=bpy.data.lights.new('Cool sky fill','AREA'); lo2=bpy.data.objects.new('Cool sky fill',ld2); bpy.context.collection.objects.link(lo2); lo2.location=(2,5,9); ld2.energy=1000; ld2.color=(.60,.77,1.0); ld2.size=9; lo2.rotation_euler=(Vector((0,1,0))-lo2.location).to_track_quat('-Z','Y').to_euler()
sun_data=bpy.data.lights.new('Warm directional afternoon sun','SUN'); sun=bpy.data.objects.new('Warm directional afternoon sun',sun_data); bpy.context.collection.objects.link(sun); sun.location=(-8,-5,10); sun_data.energy=1.4; sun_data.color=(1.0,.78,.55); sun_data.angle=.16; sun.rotation_euler=(Vector((0,1,0))-sun.location).to_track_quat('-Z','Y').to_euler()
scene.render.image_settings.color_mode='RGBA'; scene.camera.data.lens=49
scene.render.filepath=os.path.join(OUT,'03_final.png')

# Save editable source with final resolution settings, then make a low-cost preview render.
scene.render.resolution_x=1920; scene.render.resolution_y=1078; scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'scene.blend'))
scene.render.resolution_percentage=50
start=time.time(); bpy.ops.render.render(write_still=True); elapsed=time.time()-start
with open(os.path.join(ROOT,'render_log.json'),'w',encoding='utf-8') as f:
 json.dump({'command':'blender -b scene.blend -P build_scene.py','engine':scene.render.engine,'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'camera_location':list(cam.location),'camera_rotation_euler':list(cam.rotation_euler),'lens_mm':camd.lens,'render_seconds':round(elapsed,2),'object_count':len(scene.objects)},f,indent=2)
