import sys,os,json,numpy as np,time
os.environ['XDG_CACHE_HOME']='/workspace/male_left_thigh/cache'
sys.path.insert(0,'/workspace/hip_socket_design/python_packages')
import trimesh,cadquery as cq,vtk
from OCP.gp import gp_Pnt
from OCP.Geom import Geom_BezierSurface
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace,BRepBuilderAPI_Sewing,BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS
from OCP.BRepMesh import BRepMesh_IncrementalMesh
ROOT='/workspace/male_left_thigh';OUT=ROOT+'/nx_fast'
def build(name,alpha=1.):
    data=json.load(open(OUT+'/'+name+'_quads.json'));v=np.array(data['vertices']);q=np.array(data['faces'])
    if name=='FEMUR_L':
        center=np.array(json.load(open(ROOT+'/output/model_metadata.json'))['hip_center_mm'])
        dv=v-center;r=np.linalg.norm(dv,axis=1);w=np.clip((45-r)/15,0,1);w=w*w*(3-2*w)
        v-=.8*w[:,None]*dv/r[:,None]
    if name=='HIP_L':
        location=np.array([128.,-57.4,1005.7]);adj=[set() for _ in v]
        for face in q:
            for a,b in zip(face,np.roll(face,-1)):
                adj[a].add(b);adj[b].add(a)
        weight=np.clip((6-np.linalg.norm(v-location,axis=1))/6,0,1)**2
        for iteration in range(5):
            mean=np.array([v[list(a)].mean(0) for a in adj]);v+=.45*weight[:,None]*(mean-v)
    triangles=np.vstack([q[:,[0,1,2]],q[:,[0,2,3]]]);mesh=trimesh.Trimesh(v,triangles,process=False)
    if mesh.volume<0:q=q[:,::-1];triangles=np.vstack([q[:,[0,1,2]],q[:,[0,2,3]]]);mesh=trimesh.Trimesh(v,triangles,process=False)
    normals=mesh.vertex_normals;edges={}
    def edge(a,b):
        key=(min(a,b),max(a,b))
        if key not in edges:
            a0,b0=key;p0=v[a0];p3=v[b0];d=p3-p0
            edge_alpha=alpha
            if name=='HIP_L':
                location=np.array([128.,-57.4,1005.7])
                distance=np.linalg.norm((p0+p3)/2-location)
                blend=np.clip((distance-4)/8,0,1);blend=blend*blend*(3-2*blend)
                edge_alpha*=blend
            t0=d-edge_alpha*np.dot(d,normals[a0])*normals[a0]
            t1=d-edge_alpha*np.dot(d,normals[b0])*normals[b0]
            edges[key]=np.array([p0,p0+t0/3,p3-t1/3,p3])
        return edges[key] if a<b else edges[key][::-1]
    sew=BRepBuilderAPI_Sewing(1e-5)
    for a,b,c,d in q:
        cp=np.zeros((4,4,3));cp[:,0]=edge(a,b);cp[3,:]=edge(b,c);cp[:,3]=edge(d,c);cp[0,:]=edge(a,d)
        for i in [1,2]:
            for j in [1,2]:
                u=i/3;t=j/3
                bilinear=(1-u)*(1-t)*v[a]+u*(1-t)*v[b]+u*t*v[c]+(1-u)*t*v[d]
                cp[i,j]=(1-t)*cp[i,0]+t*cp[i,3]+(1-u)*cp[0,j]+u*cp[3,j]-bilinear
        poles=TColgp_Array2OfPnt(1,4,1,4)
        for i in range(4):
            for j in range(4):poles.SetValue(i+1,j+1,gp_Pnt(*cp[i,j]))
        surf=Geom_BezierSurface(poles);sew.Add(BRepBuilderAPI_MakeFace(surf,1e-7).Face())
    sew.Perform();s=cq.Shape.cast(sew.SewedShape());print(name,'sewn',len(s.Faces()),len(s.Shells()),flush=True)
    solid=cq.Solid(BRepBuilderAPI_MakeSolid(s.Shells()[0].wrapped).Solid())
    if solid.Volume()<0:solid=cq.Solid(TopoDS.Solid_s(solid.wrapped.Reversed()))
    valid=solid.isValid();print(name,'valid',valid,'volume',solid.Volume(),flush=True)
    assert valid
    solid.exportBrep(OUT+'/'+name+'.brep')
    BRepMesh_IncrementalMesh(solid.wrapped,.15,False,.2,True)
    vv,ff=solid.tessellate(.2,.2);m=trimesh.Trimesh([x.toTuple() for x in vv],ff,process=True);m.fix_normals();m.export(OUT+'/'+name+'.stl')
    r=vtk.vtkSTLReader();r.SetFileName(ROOT+'/output/'+name+'.stl');r.Update();distance=vtk.vtkImplicitPolyDataDistance();distance.SetInput(r.GetOutput())
    points=np.vstack([m.vertices[::max(1,len(m.vertices)//10000)],m.triangles_center[::max(1,len(m.faces)//10000)]])
    errors=np.abs([distance.EvaluateFunction(p) for p in points])
    return {'solid_valid':valid,'faces':len(solid.Faces()),'volume_mm3':solid.Volume(),'mesh_watertight':bool(m.is_watertight),'sampled_median_difference_mm':float(np.median(errors)),'sampled_p95_difference_mm':float(np.percentile(errors,95)),'sampled_max_difference_mm':float(np.max(errors)),'samples':len(errors)}
if __name__=='__main__':
    report={}
    for n in ['FEMUR_L','HIP_L']:
        report[n]=build(n);json.dump(report,open(OUT+'/surface_validation.json','w'),indent=2)
    print('DONE',json.dumps(report),flush=True)
