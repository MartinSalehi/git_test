import os,sys,time,json,numpy as np
os.environ['XDG_CACHE_HOME']='/workspace/male_left_thigh/cache'
sys.path.insert(0,'/workspace/hip_socket_design/python_packages')
import trimesh,vtk,cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.STEPControl import STEPControl_Controller
from OCP.Interface import Interface_Static
from cadquery.occ_impl.exporters.assembly import exportAssembly
ROOT='/workspace/male_left_thigh';OUT=ROOT+'/nx_fast'
def vol(s):
    p=GProp_GProps();BRepGProp.VolumePropertiesGK_s(s.wrapped,p,1e-7,False,True,False,False,False);return p.Mass()
shapes={n:cq.Shape.importBrep(OUT+'/'+n+'.brep') for n in ['FEMUR_L','HIP_L']}
report=json.load(open(OUT+'/surface_validation.json'))
r=vtk.vtkSTLReader();r.SetFileName(ROOT+'/output/SOFT_TISSUE_ENVELOPE.stl');r.Update();d=vtk.vtkImplicitPolyDataDistance();d.SetInput(r.GetOutput())
meshes={n:trimesh.load(OUT+'/'+n+'.stl') for n in shapes}
for n,m in meshes.items():
    pts=np.vstack([m.vertices,m.triangles_center]);dist=np.array([d.EvaluateFunction(p) for p in pts]);report[n]['minimum_sampled_skin_cover_mm']=float(-dist.max());assert dist.max()<0,(n,dist.max())
clash=trimesh.boolean.intersection(list(meshes.values()),engine='manifold')
print('Curved bones sampled overlap',clash.volume,flush=True);assert abs(clash.volume)<1e-5
outer=cq.Shape.importBrep(ROOT+'/output/skin_outer.brep')
make=BRepBuilderAPI_MakeSolid(outer.Shells()[0].wrapped)
for shape in shapes.values():make.Add(TopoDS.Shell_s(shape.Shells()[0].wrapped.Reversed()))
tissue=cq.Solid(make.Solid());assert tissue.isValid();assert len(tissue.Solids())==1
ov=vol(outer);tv=vol(tissue);bv=sum(vol(s) for s in shapes.values());balance=ov-tv-bv
print('Volume balance',balance,flush=True);assert abs(balance)<2
shapes['SOFT_TISSUE_L']=tissue;report['SOFT_TISSUE_L']={'solid_valid':True,'faces':len(tissue.Faces()),'shells':len(tissue.Shells()),'volume_balance_error_mm3':balance}
STEPControl_Controller.Init_s();Interface_Static.SetCVal_s('write.step.schema','AP214IS')
for n,s in shapes.items():
    s.exportBrep(OUT+'/'+n+'.brep');s.exportStep(OUT+'/'+n+'_SMOOTH.step',write_pcurves=True)
assy=cq.Assembly(name='LEFT_MALE_HIP_THIGH_NX_SMOOTH')
for n in ['SOFT_TISSUE_L','FEMUR_L','HIP_L']:
    assy.add(shapes[n],name=n,color=cq.Color(.65,.36,.25) if n=='SOFT_TISSUE_L' else cq.Color(.88,.80,.61))
path=OUT+'/START_HERE_NX_SMOOTH_ASSEMBLY.step'
assert exportAssembly(assy,path,mode='default',write_pcurves=True)
print('Assembly bytes',os.path.getsize(path),'faces',sum(len(s.Faces()) for s in shapes.values()),flush=True)
print('Reopening revised STEP assembly',flush=True);start=time.time()
back=cq.importers.importStep(path).val();elapsed=time.time()-start
assert len(back.Solids())==3 and back.isValid()
report['assembly']={'valid_after_reopening':True,'solid_bodies':3,'total_faces':sum(len(s.Faces()) for s in shapes.values()),'step_bytes':os.path.getsize(path),'read_seconds_opencascade':elapsed,'file_schema':'AP214','surface_boundaries_included':True,'old_step_bytes':os.path.getsize(ROOT+'/output/NX_LEFT_MALE_HIP_THIGH_ASSEMBLY.step'),'old_total_faces':139998}
print('Revised STEP round trip:',json.dumps(report['assembly']),flush=True)
for n in shapes:
    start=time.time();one=cq.importers.importStep(OUT+'/'+n+'_SMOOTH.step').val();assert one.isValid() and len(one.Solids())==1;report[n]['individual_step_reopened']=True;report[n]['step_read_seconds']=time.time()-start
json.dump(report,open(OUT+'/NX_SMOOTH_VALIDATION.json','w'),indent=2)
