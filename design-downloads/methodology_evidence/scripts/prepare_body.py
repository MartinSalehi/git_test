import sys,json,numpy as np
sys.path.insert(0,'/workspace/hip_socket_design/python_packages')
import trimesh
ROOT='/workspace/male_left_thigh'
vertices=[];faces=[];group='';group_faces={}
for line in open(ROOT+'/sources/makehuman_base.txt'):
    t=line.split()
    if not t:continue
    if t[0]=='v':vertices.append(list(map(float,t[1:4])))
    elif t[0]=='g':group=t[1];group_faces.setdefault(group,[])
    elif t[0]=='f':
        ids=[int(a.split('/')[0])-1 for a in t[1:]]
        for i in range(1,len(ids)-1):group_faces[group].append([ids[0],ids[i],ids[i+1]])
v=np.array(vertices)
for line in open(ROOT+'/sources/male_young.target'):
    t=line.split()
    if len(t)==4 and not line.startswith('#'):v[int(t[0])]+=np.array(list(map(float,t[1:])))
info={}
for name,f in group_faces.items():
    ids=np.unique(f);p=v[ids]
    info[name]={'vertices':len(ids),'faces':len(f),'center':p.mean(0).tolist(),'bounds':[p.min(0).tolist(),p.max(0).tolist()]}
    if any(k in name.lower() for k in ['pelvis','hip','upperleg','upper-leg','thigh','knee','body']):print(name,info[name])
np.savez(ROOT+'/sources/makehuman_male.npz',vertices=v,**{g:np.asarray(f) for g,f in group_faces.items()})
json.dump(info,open(ROOT+'/sources/makehuman_groups.json','w'),indent=2)
bodyfaces=np.vstack([f for n,f in group_faces.items() if n=='body'])
m=trimesh.Trimesh(v,bodyfaces,process=True);m.export(ROOT+'/sources/male_body.obj')
print('male body',m.bounds,'watertight',m.is_watertight)
