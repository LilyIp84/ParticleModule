"""Unit tests for the file IO"""
from particle_model import IO
from particle_model import Particles

import vtk
import os
import numpy
import filecmp

DATA_DIR = 'particle_model/tests/data'

def test_clean_unstructured_grid():
    """ Test the clean_unstructured_grid routine"""
    reader = vtk.vtkXMLUnstructuredGridReader()
    del reader
    ugrid = vtk.vtkUnstructuredGrid()
    clean_grid = IO.clean_unstructured_grid(ugrid)

    assert clean_grid


def test_polydata(tmpdir):
    """ Test the polydata class """
    from numpy import zeros

    num = 100

    pres = zeros((num, 3))
    vel = zeros((num, 3))

    part = Particles.ParticleBucket(pres, vel)

    filepath = tmpdir.join('test.vtp').strpath

    poly_data = IO.PolyData(tmpdir.join('test.vtp').strpath)

    assert poly_data

    poly_data.append_data(part)

    assert len(poly_data.cell_ids) == num
    assert poly_data.pnts.GetNumberOfPoints() == num

    poly_data.write()

    assert os.path.isfile(filepath)
    assert poly_data.poly_data.GetNumberOfCells() == num

    poly_data.append_data(part)

    assert len(poly_data.cell_ids) == num
    assert poly_data.pnts.GetNumberOfPoints() == 2*num


def test_make_unstructured_grid(tmpdir):
    """ Test the make_unstructured_grid routine."""

    mesh = IO.GmshMesh()
    mesh.read("/".join((DATA_DIR, 'Structured.msh')))


    print "/".join((DATA_DIR, 'Structured.msh'))
    num = len(mesh.nodes)

    vel = numpy.zeros((num, 3))
    pres = numpy.zeros((num,))
    time = 0

    ugrid = IO.make_unstructured_grid(mesh, vel, pres, time,
                                      outfile=tmpdir.join('Structured.vtu').strpath)

    assert num > 0
    assert ugrid.GetNumberOfPoints() == num
    assert ugrid.GetNumberOfCells() == len(mesh.elements)
    assert filecmp.cmpfiles(DATA_DIR, tmpdir.strpath, 'Structured.vtu')
