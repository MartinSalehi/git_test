import sys,os,json,glob,numpy as np,vtk
sys.path.insert(0,'/workspace/hip_socket_design/python_packages')
import trimesh
from scipy.spatial import cKDTree
from vtk.util.numpy_support import numpy_to_vtk,vtk_to_numpy
ROOT='/workspace/male_left_thigh'
def poly(m):
    p=vtk.vtkPolyData();points=vtk.vtkPoints();points.SetData(numpy_to_vtk(m.vertices));p.SetPoints(points)
    cells=vtk.vtkCellArray();cells.SetCells(len(m.faces),numpy_to_vtk(np.c_[np.full(len(m.faces),3),m.faces].astype(np.int64).ravel(),array_type=vtk.VTK_ID_TYPE));p.SetPolys(cells);return p
def icp(m,t,initial):
    mm=m.copy();mm.apply_transform(initial)
    i=vtk.vtkIterativeClosestPointTransform();i.SetSource(poly(mm));i.SetTarget(poly(t));i.GetLandmarkTransform().SetModeToSimilarity();i.SetMaximumNumberOfIterations(60);i.SetMaximumNumberOfLandmarks(3000);i.StartByMatchingCentroidsOff();i.CheckMeanDistanceOn();i.SetMaximumMeanDistance(.001);i.Update()
    mat=np.array([[i.GetMatrix().GetElement(a,b) for b in range(4)] for a in range(4)])
    mm.apply_transform(mat)
    d=vtk.vtkImplicitPolyDataDistance();d.SetInput(poly(t));points=mm.vertices[::max(1,len(mm.vertices)//4000)]
    values=np.abs([d.EvaluateFunction(p) for p in points])
    return np.percentile(values,75),mm,mat@initial,{'median_mm':float(np.median(values)),'p95_mm':float(np.percentile(values,95))}
report={}
for name,pattern in [('Femur.l','FEMUR'),('Hip_bone.l','HIP')]:
    s=trimesh.load(glob.glob('/workspace/attachments/*/'+pattern+'*')[0]);s=max(s.split(only_watertight=False),key=lambda m:len(m.faces));t=trimesh.load(ROOT+'/sources/'+name+'.stl');t.apply_scale(1000)
    # Surface sampling avoids bias from the uneven density in the input scans.
    a,_=trimesh.sample.sample_surface(s,15000,seed=17);b,_=trimesh.sample.sample_surface(t,15000,seed=17)
    ea,Ua=np.linalg.eigh(np.cov(a.T));eb,Ub=np.linalg.eigh(np.cov(b.T));scale=np.sqrt(eb[-1]/ea[-1])
    candidates=[]
    for signs in [(x,y,z) for x in [-1,1] for y in [-1,1] for z in [-1,1]]:
        R=Ub@np.diag(signs)@Ua.T;T=np.eye(4);T[:3,:3]=scale*R;T[:3,3]=b.mean(0)-scale*R@a.mean(0)
        score,m,mat,quality=icp(s,t,T);candidates.append((score,m,mat,quality));print(name,signs,score,quality,flush=True)
    score,m,mat,quality=min(candidates,key=lambda c:c[0]);m.fix_normals();m.export(ROOT+'/sources/'+name+'_detailed.stl')
    report[name]={'transform':mat.tolist(),'quality':quality,'score_p75_mm':float(score),'input_file':pattern+'_matched.stl','determinant':float(np.linalg.det(mat[:3,:3]))}
    json.dump(report,open(ROOT+'/sources/detailed_registration.json','w'),indent=2)
