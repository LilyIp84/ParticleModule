import vtk
import pylab as p
import numpy


types_3d=[vtk.VTK_TETRA,vtk.VTK_QUADRATIC_TETRA]
types_2d=[vtk.VTK_TRIANGLE,vtk.VTK_QUADRATIC_TRIANGLE]
types_1d=[vtk.VTK_LINE]

def clean_unstructured_grid(ugrid):
    
    mp=vtk.vtkMergePoints()
    out_grid=vtk.vtkUnstructuredGrid()

    for i in range(ugrid.GetNumberOfPoints()):
        mp.InsertUniquePoint(ugrid.GetPoints().GetPoint(i))
        
    mp.BuildLocator()


    pts=vtk.vtkPoints()
    pts.DeepCopy(mp.GetPoints())
    out_grid.SetPoints(pts)

    for i in range(ugrid.GetNumberOfCells()):
        c=ugrid.GetCell(i)

        for j in range(c.GetNumberOfPoints()):
            c.GetPointIds().SetId(j,mp.FindClosestInsertedPoint(c.GetPoints().GetPoint(j))) 

        out_grid.InsertNextCell(c.GetCellType(),C.GetPointIds())


    out_grid.GetCellData().DeepCopy(ugrid.GetCellData())

    return out_grid
        

def extract_boundary(ugrid):

    out_grid=vtk.vtkUnstructuredGrid()
    pts=vtk.vtkPoints()
    pts.DeepCopy(ugrid.GetPoints())
    out_grid.SetPoints(pts)
    out_grid.GetCellData().CopyStructure(ugrid.GetCellData())

    celltypes=vtk.vtkCellTypes()
    
    ugrid.GetCellTypes(celltypes)

    if any([celltypes.IsType(ct) for ct in types_3d]):
        dim=3
    elif any([celltypes.IsType(ct) for ct in types_2d]):
        dim=2
    elif any([celltypes.IsType(ct) for ct in types_1d]):
        dim=1
    else:
        dim=0

    print dim

    NC=ugrid.GetNumberOfCells()
    NCDA=ugrid.GetCellData().GetNumberOfArrays()

    for i in range(NCDA):
        out_grid.GetCellData().GetArray(i).SetName(ugrid.GetCellData().GetArray(i).GetName())

    

    for i in range(NC):
        c=ugrid.GetCell(i)
        if (dim>c.GetCellDimension()):
            out_grid.InsertNextCell(c.GetCellType(),c.GetPointIds())
            for j in range(NCDA):
                out_grid.GetCellData().GetArray(j).InsertNextTuple(ugrid.GetCellData().GetArray(j).GetTuple(i))


    return out_grid


def plot_boundary(ugrid,**kwargs):
    for i in range(ugrid.GetNumberOfCells()):
        c=ugrid.GetCell(i)
        
        x=[]
        y=[]

        for j in range(c.GetNumberOfPoints()):
            pnt=c.GetPoints().GetPoint(j)
            x.append(pnt[0])
            y.append(pnt[1])

        p.plot(x,y,'k',**kwargs)


def get_ascii_data(filename='data.dat'):
    f=open(filename,'r')

    t=[]
    x=[]
    y=[]
    z=[]
    u=[]
    v=[]
    w=[]

    for m in f.readlines():
        r=[float(M) for M in m.split()]

        t.append(r[0])
        n=len(r[1:])/6
        X=r[1::3]
        Y=r[2::3]
        Z=r[3::3]
        x.append(X[:n])
        u.append(X[n:])
        y.append(Y[:n])
        v.append(Y[n:])
        z.append(Z[:n])
        w.append(Z[n:])

    x=numpy.array(x)
    y=numpy.array(y)
    z=numpy.array(z)
    u=numpy.array(u)
    v=numpy.array(v)
    w=numpy.array(w)

    f.close()

    return t,x,y,z,u,v,w


def ascii_to_polydata_time_series(filename,basename):


    t,x,y,z,u,v,w=get_ascii_data(filename)

    for i, (X,Y,U,V) in enumerate(zip(x,y,u,v)):

        pd=vtk.vtkPolyData()
        pnts=vtk.vtkPoints()
        pnts.Allocate(0)
        pd.SetPoints(pnts)
        pd.Allocate(x.shape[0])

        time=vtk.vtkDoubleArray()
        time.Allocate(x.shape[0])
        time.SetName('Time')

        velocity=vtk.vtkDoubleArray()
        velocity.SetNumberOfComponents(3)
        velocity.Allocate(x.shape[0])
        velocity.SetName('Particle Velocity')

        for k,D in enumerate(zip(X,Y,U,V)):
            px,py,qu,qv=D
            pixel=vtk.vtkPixel()
            pixel.GetPointIds().InsertId(k,pd.GetPoints().InsertNextPoint(px,py,0.))
            time.InsertNextValue(t[i])
            velocity.InsertNextTuple3(qu,qv,0.0)

        pd.GetPointData().AddArray(time)
        pd.GetPointData().AddArray(velocity)
        writer=vtk.vtkXMLPolyDataWriter()
        writer.SetFileName("%s_%d.vtp"%(basename,i))
        writer.SetInput(pd)
        writer.Write()


def ascii_to_polydata(filename,outfile):

    pd=vtk.vtkPolyData()
    pnts=vtk.vtkPoints()
    pnts.Allocate(0)
    pd.SetPoints(pnts)
    t,x,y, z,u,v,w=get_ascii_data(filename)
    pd.Allocate(x.shape[1])

    time=vtk.vtkDoubleArray()
    time.SetName('Time')
    
        
    for X,Y in zip(x.T,y.T):
        line=vtk.vtkLine()
        for k,D in enumerate(zip(t,X,Y)):
            T,px,py=D
            line.GetPointIds().InsertId(k,pd.GetPoints().InsertNextPoint(px,py,0.))
            time.InsertNextValue(T)
        pd.InsertNextCell(line.GetCellType(),line.GetPointIds())

    pd.GetPointData().AddArray(time)
    
    writer=vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(outfile)
    writer.SetInput(pd)
    
    writer.Write()

            
            

    