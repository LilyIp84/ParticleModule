"""Example of particles from an options file."""
import particle_model as pm
import numpy
import vtk


def setup(mb,time,dt):
    N = 0

    X = 0.5+0.5*(numpy.random.random((N, 3))-0.5)
    X[:,0] += 0.2
    X[:,2] = 0

    V = numpy.zeros((N,3))
    V[:,0] = 1.0


    SYSTEM=pm.System.get_system_from_options(block=(mb,time,dt))
    PAR=pm.ParticleBase.get_parameters_from_options()[0]

    writer=vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName('boundary.vtu')
    writer.SetInput(SYSTEM.boundary.bnd)
    writer.Write()

    PB = pm.Particles.ParticleBucket(X, V, time, delta_t=0.2*dt,
                                 system=SYSTEM,
                                 parameters=PAR)


    return PB
