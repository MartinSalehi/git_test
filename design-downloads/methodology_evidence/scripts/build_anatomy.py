import sys,os,json
sys.path.insert(0,'/workspace/hip_socket_design/python_packages')
import numpy as np,trimesh
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
ROOT='/workspace/male_left_thigh';OUT=ROOT+'/output'
data=np.load(ROOT+'/sources/makehuman_male.npz')
v=data['vertices'].copy();faces=data['body']
for name,weight in [('hip_width',.65),('hip_depth',.65),('buttocks',.25),('body_weight',.12)]:
    for line in open(ROOT+'/sources/'+name+'.target'):
        t=line.split()
        if len(t)==4 and not line.startswith('#'):v[int(t[0])]+=weight*np.array(list(map(float,t[1:])))
# MakeHuman uses decimetres: X left, Y superior, Z anterior.
floor=v[np.unique(faces),1].min()
mapped=np.column_stack([v[:,0]*100,-v[:,2]*100,(v[:,1]-floor)*100])
skin=trimesh.Trimesh(mapped,faces,process=True)
groups=json.load(open(ROOT+'/sources/makehuman_groups.json'))
def joint(name):
    p=np.array(groups[name]['center']);return np.array([p[0]*100,-p[2]*100,(p[1]-floor)*100])
hip_target=joint('joint-l-upper-leg');knee_target=joint('joint-l-knee')
femur=trimesh.load(ROOT+'/sources/Femur.l.stl');femur.apply_scale(1000)
hip=trimesh.load(ROOT+'/sources/Hip_bone.l.stl');hip.apply_scale(1000)
f=femur.vertices
p=f[(f[:,2]>855)&(f[:,0]<83)]
init=np.r_[np.mean(p,axis=0),24]
fit=least_squares(lambda q:np.linalg.norm(p-q[:3],axis=1)-q[3],init,loss='soft_l1',f_scale=.7)
head=fit.x[:3]
distal=f[f[:,2]<f[:,2].min()+42]
knee=np.r_[np.mean([distal[:,0].min(),distal[:,0].max()]),np.mean([distal[:,1].min(),distal[:,1].max()]),f[:,2].min()+24]
a=knee-head;b=knee_target-hip_target
scale=np.linalg.norm(b)/np.linalg.norm(a)
rot=trimesh.geometry.align_vectors(a,b)[:3,:3]
transform=np.eye(4);transform[:3,:3]=scale*rot;transform[:3,3]=hip_target-scale*rot@head
for mesh in [femur,hip]:mesh.apply_transform(transform);mesh.fix_normals()
pelvic_tilt=trimesh.transformations.rotation_matrix(np.deg2rad(17),[1,0,0],point=hip_target)
hip.apply_transform(pelvic_tilt)
# Preserve the finer anatomical surface detail from the user-supplied scans.
reg=json.load(open(ROOT+'/sources/detailed_registration.json'))
old=json.load(open('/workspace/hip_socket_design/deliverables/geometry_report.json'))
new_bones=[]
for stem,key in [('Femur.l','femoral_head_center_source'),('Hip_bone.l','acetabulum_center_source')]:
    m=trimesh.load(ROOT+'/sources/'+stem+'_detailed.stl')
    T=np.array(reg[stem]['transform']);native_center=T[:3,:3]@np.array(old[key])+T[:3,3]
    m.apply_translation(head-native_center);m.apply_transform(transform)
    if stem=='Hip_bone.l':m.apply_transform(pelvic_tilt)
    m.fix_normals();new_bones.append(m)
femur,hip=new_bones
hip.vertices=hip_target+1.006*(hip.vertices-hip_target)
# Use a 1748 mm generic adult male body, retaining the gluteal and hip contours.
top_z=max(hip.vertices[:,2])+40
bottom_z=min(femur.vertices[:,2])-27
box=trimesh.creation.box([700,700,top_z-bottom_z],transform=trimesh.transformations.translation_matrix([350,0,(top_z+bottom_z)/2]))
outer=trimesh.boolean.intersection([skin,box],engine='manifold')
outer= max(outer.split(only_watertight=True),key=lambda m:m.volume)
for name,m in [('FEMUR_L',femur),('HIP_L',hip),('SOFT_TISSUE_ENVELOPE',outer)]:m.export(OUT+'/'+name+'.stl')
skin.export(ROOT+'/sources/male_body_mm.stl')
meta={'units':'mm','side':'left','coordinates':{'X':'left','Y':'posterior','Z':'superior'},'template_height_mm':float(skin.extents[2]),'hip_center_mm':hip_target.tolist(),'knee_center_mm':knee_target.tolist(),'atlas_head_sphere_source_mm':head.tolist(),'atlas_head_radius_mm':float(fit.x[3]),'registration_scale':scale,'registration_transform':transform.tolist(),'proximal_cut_z':float(top_z),'distal_cut_z':float(bottom_z),'models':{n:{'bounds_mm':m.bounds.tolist(),'dimensions_mm':m.extents.tolist(),'watertight':bool(m.is_watertight),'vertices':len(m.vertices),'faces':len(m.faces),'volume_mm3':float(m.volume)} for n,m in [('FEMUR_L',femur),('HIP_L',hip),('SOFT_TISSUE_ENVELOPE',outer)]}}
json.dump(meta,open(OUT+'/model_metadata.json','w'),indent=2)
print(json.dumps(meta,indent=2),flush=True)
