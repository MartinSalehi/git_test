import bpy,os,json
ROOT='/workspace/male_left_thigh';OUT=ROOT+'/nx_fast'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
report={}
for name,target in [('FEMUR_L',700),('HIP_L',900)]:
    bpy.ops.wm.stl_import(filepath=ROOT+'/output/'+name+'.stl');o=bpy.context.object;o.name=name
    bpy.context.view_layer.objects.active=o
    # Anatomical surfaces are organic; a quad layout supports smooth CAD patches.
    bpy.ops.object.quadriflow_remesh(target_faces=target,use_mesh_symmetry=False,use_preserve_sharp=False,use_preserve_boundary=False,seed=5)
    vertices=[list(v.co) for v in o.data.vertices];faces=[list(f.vertices) for f in o.data.polygons]
    json.dump({'vertices':vertices,'faces':faces},open(OUT+'/'+name+'_quads.json','w'))
    report[name]={'vertices':len(vertices),'quads':sum(len(f)==4 for f in faces),'other_faces':sum(len(f)!=4 for f in faces)}
    print(name,report[name],flush=True)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
    bpy.ops.wm.stl_export(filepath=OUT+'/'+name+'_retopo.stl',export_selected_objects=True)
json.dump(report,open(OUT+'/retopology_report.json','w'),indent=2)
