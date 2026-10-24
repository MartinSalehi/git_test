import bpy,os,json
from mathutils import Vector
ROOT='/workspace/male_left_thigh'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
names=['Femur.l','Hip bone.l','Patella.l','Hip region.l','Femoral region.j','Gluteus maximus muscle.l','Rectus femoris muscle.l','Vastus lateralis muscle.l','Vastus medialis muscle.l']
with bpy.data.libraries.load(ROOT+'/sources/Z-Anatomy/Startup.blend',link=False) as (src,dst):
    dst.objects=[n for n in names if n in src.objects]
meta={}
for o in dst.objects:
    if o is None:continue
    bpy.context.collection.objects.link(o)
    if o.type!='MESH':continue
    verts=[o.matrix_world@v.co for v in o.data.vertices]
    bounds=[[min(v[i] for v in verts) for i in range(3)],[max(v[i] for v in verts) for i in range(3)]]
    print(o.name,len(o.data.vertices),len(o.data.polygons),bounds,flush=True)
    meta[o.name]={'bounds':bounds,'matrix':list(map(list,o.matrix_world)),'vertices':len(o.data.vertices),'faces':len(o.data.polygons)}
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.wm.stl_export(filepath=ROOT+'/sources/'+o.name.replace(' ','_')+'.stl',export_selected_objects=True)
json.dump(meta,open(ROOT+'/sources/atlas_geometry.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/sources/atlas_selected.blend')
