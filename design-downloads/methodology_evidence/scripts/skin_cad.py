import os,sys,json,numpy as np,vtk,cadquery as cq
os.environ['XDG_CACHE_HOME']='/workspace/male_left_thigh/cache'
sys.path.insert(0,'/workspace/hip_socket_design/python_packages')
import trimesh
from scipy.interpolate import make_interp_spline
from scipy.ndimage import gaussian_filter1d
from OCP.gp import gp_Pnt
from OCP.Geom import Geom_BSplineSurface
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.TColStd import TColStd_Array1OfReal,TColStd_Array1OfInteger
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace,BRepBuilderAPI_MakeWire,BRepBuilderAPI_MakeEdge,BRepBuilderAPI_Sewing,BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS
from vtk.util.numpy_support import vtk_to_numpy
vtk.vtkLogger.SetStderrVerbosity(vtk.vtkLogger.VERBOSITY_ERROR)
ROOT='/workspace/male_left_thigh';OUT=ROOT+'/output'
def arr(values,kind):
    a=kind(1,len(values))
    for i,x in enumerate(values):a.SetValue(i+1,x.item() if hasattr(x,'item') else x)
    return a
def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def build():
    meta=json.load(open(OUT+'/model_metadata.json'));bottom=meta['distal_cut_z'];top=meta['proximal_cut_z']
    read=vtk.vtkSTLReader();read.SetFileName(ROOT+'/sources/male_body_mm.stl');read.Update()
    loop=vtk.vtkLoopSubdivisionFilter();loop.SetInputConnection(read.GetOutputPort());loop.SetNumberOfSubdivisions(2);loop.Update()
    plane=vtk.vtkPlane();plane.SetNormal(0,0,1)
    cut=vtk.vtkCutter();cut.SetInputConnection(loop.GetOutputPort());cut.SetCutFunction(plane)
    strip=vtk.vtkStripper();strip.SetInputConnection(cut.GetOutputPort());strip.JoinContiguousSegmentsOn()
    zs=np.linspace(bottom,top,110);N=128;theta=np.linspace(0,2*np.pi,N,endpoint=False);directions=np.c_[np.cos(theta),np.sin(theta)]
    rings=[]
    for z in zs:
        plane.SetOrigin(0,0,z);strip.Update();pd=strip.GetOutput();points=vtk_to_numpy(pd.GetPoints().GetData());cells=vtk_to_numpy(pd.GetLines().GetData());i=0;candidates=[]
        while i<len(cells):
            n=cells[i];ids=cells[i+1:i+1+n];i+=n+1;p=points[ids,:2]
            if p[:,0].max()>30:candidates.append(p)
        p=max(candidates,key=lambda p:abs(cross(p,np.roll(p,-1,axis=0)).sum()))
        # Clip the planar contour against the median plane X=0.
        clipped=[]
        for a,b in zip(p,np.roll(p,-1,axis=0)):
            if a[0]>=0:clipped.append(a)
            if (a[0]<0)!=(b[0]<0):clipped.append(a+(b-a)*(-a[0]/(b[0]-a[0])))
        p=np.array(clipped)
        center=(p.min(0)+p.max(0))/2
        a=p-center;e=np.roll(p,-1,axis=0)-p
        radii=[]
        for d in directions:
            denom=cross(d,e);safe=np.where(abs(denom)>1e-10,denom,np.nan)
            t=cross(a,e)/safe;u=cross(a,d)/safe
            valid=(t>0)&(u>=-1e-7)&(u<=1+1e-7)
            if not np.any(valid):raise RuntimeError(('radial trace failed',z,d))
            radii.append(t[valid].min())
        row=center+np.array(radii)[:,None]*directions
        rings.append(np.c_[row,np.full(N,z)])
    rings=np.array(rings)
    # Suppress small interpolation ripples while retaining the gluteal fold.
    rings=gaussian_filter1d(rings,1.1,axis=0,mode='nearest')
    rings=gaussian_filter1d(rings,.65,axis=1,mode='wrap')
    rings[:,:,2]=zs[:,None]
    np.savez(OUT+'/skin_surface_data.npz',rings=rings,zs=zs,theta=theta)
    v=make_interp_spline(zs,rings,axis=0)
    deriv=(np.roll(v.c,-1,axis=1)-np.roll(v.c,1,axis=1))/(4*np.pi/N)
    sew=BRepBuilderAPI_Sewing(.0001);surfaces=[]
    for k in range(4):
        ids=np.arange(k*32,(k+1)*32+1)%N;angles=np.arange(k*32,(k+1)*32+1)*2*np.pi/N
        u=make_interp_spline(angles,v.c[:,ids,:].transpose(1,0,2),axis=0,bc_type=([(1,deriv[:,ids[0],:])],[(1,deriv[:,ids[-1],:])]))
        cp=u.c;points=TColgp_Array2OfPnt(1,cp.shape[0],1,cp.shape[1])
        for i in range(cp.shape[0]):
            for j in range(cp.shape[1]):points.SetValue(i+1,j+1,gp_Pnt(*cp[i,j]))
        uk,um=np.unique(u.t,return_counts=True);vk,vm=np.unique(v.t,return_counts=True)
        surface=Geom_BSplineSurface(points,arr(uk,TColStd_Array1OfReal),arr(vk,TColStd_Array1OfReal),arr(um,TColStd_Array1OfInteger),arr(vm,TColStd_Array1OfInteger),3,3)
        surfaces.append((surface,angles[0],angles[-1]));sew.Add(BRepBuilderAPI_MakeFace(surface,1e-6).Face())
    for z in [bottom,top]:
        wire=BRepBuilderAPI_MakeWire()
        for surface,umin,umax in surfaces:wire.Add(BRepBuilderAPI_MakeEdge(surface.VIso(z),float(umin),float(umax)).Edge())
        sew.Add(BRepBuilderAPI_MakeFace(wire.Wire(),True).Face())
    sew.Perform();shape=cq.Shape.cast(sew.SewedShape());print('Skin shells',len(shape.Shells()),'faces',len(shape.Faces()),flush=True)
    solid=cq.Solid(BRepBuilderAPI_MakeSolid(shape.Shells()[0].wrapped).Solid())
    if solid.Volume()<0:solid=cq.Solid(TopoDS.Solid_s(solid.wrapped.Reversed()))
    print('Skin valid',solid.isValid(),'volume',solid.Volume(),flush=True)
    assert solid.isValid() and len(solid.Solids())==1
    solid.exportBrep(OUT+'/skin_outer.brep');solid.exportStep(OUT+'/SKIN_OUTER_REFERENCE.step')
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    BRepMesh_IncrementalMesh(solid.wrapped,.2,False,.2,True)
    vertices,faces=solid.tessellate(.3,.2)
    mesh=trimesh.Trimesh([p.toTuple() for p in vertices],faces,process=True);mesh.fix_normals();mesh.export(OUT+'/SOFT_TISSUE_ENVELOPE.stl')
    print('Skin tessellation',len(mesh.faces),'watertight',mesh.is_watertight,flush=True)
    return solid
if __name__=='__main__':build()
