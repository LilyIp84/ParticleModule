"""Example of particles in double gyre hitting wall."""
import particle_model as pm
import numpy
from numpy import pi, sin, cos

S = '160'

N = 400

X = 0.5+0.25*(numpy.random.random((N, 3))-0.5)
X[:, 0] += 0.2

V = numpy.zeros((N, 3))
V[:, 0] = -2.0*pi*sin(pi*X[:, 0])*sin(2.0*pi*(X[:, 1]+ X[:, 2]))
V[:, 1] = pi*cos(pi*X[:, 0])*sin(2.0*pi*X[:, 1])*sin(2.0*pi*X[:, 2])
V[:, 2] = pi*cos(pi*X[:, 0])*sin(2.0*pi*X[:, 1])*sin(2.0*pi*X[:, 2])
U = numpy.zeros((N, 3))
GP = numpy.zeros((N, 3))

NAME = 'cube'

BOUNDARY = pm.IO.BoundaryData('cube_boundary.vtu')
TEMP_CACHE = pm.TemporalCache.TemporalCache(NAME)

PB = pm.Particles.ParticleBucket(X, V, 0.0, 1.0e-3, tc=TEMP_CACHE, U=U, GP=GP,
                                 boundary=BOUNDARY, diameter=1e-3)

TEMP_CACHE.data[1][0] = 100.0

PD = pm.IO.PolyData(NAME+'.vtp')
PD.append_data(PB)
pm.IO.write_level_to_polydata(PB, 0, NAME)

for i in range(300):
    print PB.time
    print 'min, max: pos_x', PB.pos[:, 0].ravel().min(), PB.pos[:, 0].ravel().max()
    print 'min, max: vel_x', PB.vel[:, 0].ravel().min(), PB.vel[:, 0].ravel().max()
    PB.update()
    PD.append_data(PB)
    pm.IO.write_level_to_polydata(PB, i+1, NAME)
PD.write()
pm.IO.collision_list_to_polydata(PB.collisions(), 'collisions%s.vtp'%NAME)


