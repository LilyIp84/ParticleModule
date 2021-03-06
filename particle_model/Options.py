""" Module dealing with initialising the code from an xml format options file using spud"""

import numpy

from particle_model import Parallel
from particle_model import Debug
import vtk
# from particle_model import IO

try:
    import libspud
except ImportError:
    Debug.logger.warning("Want the libspud python package. Try: \n sudo apt-get install python-spud")


class Inlet(object):
    """ class for an inlet surface"""
    def __init__(self, surface_ids, insertion_rate, velocity, pdf, **kwargs):

        self.surface_ids = surface_ids
        self.insertion_rate = insertion_rate
        self.pdf = pdf
        self.velocity = velocity
        self.kwargs = kwargs

    def weigh(self, time, boundary, cache=None):
        """ Calculate inlet weight from pdf."""
        inlet_weight = 0
        for index in boundary.GetNumberOfCells():
            if boundary.GetCellData().GetScalars('SurfaceIds').GetValue(index) in self.surface_ids:
                cell = boundary.GetCell(index)
                npts = cell.GetNumberOfPoints()

                if cell.GetCellType() == vtk.VTK_LINE:
                    mass = numpy.sqrt(cell.GetLength2())
                elif cell.GetCellType() == vtk.VTK_TRIANGLE:
                    mass = cell.ComputeArea()

                for _ in range(npts):
                    if self.pdf:
                        inlet_weight += self.pdf(cell.GetPoints().GetPoint(_),
                                                 time) * mass / npts
                    else:
                        inlet_weight += numpy.sqrt(sum(cache.get_velocity(cell.GetPoints().GetPoint(_),
                                                                          time)**2)) * mass / npts

        return inlet_weight

    def cum_weight(self, time, boundary, cache=None):
        """Calculate inlet cumulative weight."""
        inlet_weight = 0
        weights = []
        for index in range(boundary.GetNumberOfCells()):
            if boundary.GetCellData().GetScalars('SurfaceIds').GetValue(index) in self.surface_ids:
                cell = boundary.GetCell(index)
                npts = cell.GetNumberOfPoints()

                if cell.GetCellType() == vtk.VTK_LINE:
                    mass = numpy.sqrt(cell.GetLength2())
                elif cell.GetCellType() == vtk.VTK_TRIANGLE:
                    mass = cell.ComputeArea()

                for _ in range(npts):
                    old_inlet_weight = inlet_weight

                    if self.pdf:
                        inlet_weight += self.pdf(cell.GetPoints().GetPoint(_),
                                                 time) * mass / npts
                    else:
                        inlet_weight += numpy.sqrt(sum(cache.get_velocity(cell.GetPoints().GetPoint(_),
                                                                          time)**2)) * mass / npts

                    weights.append((index, old_inlet_weight, inlet_weight))

        return weights

    def select_point(self, time, weights, boundary):
        """Given the boundary cdf weights, find a suitable insertion point."""

        total_weight = weights[-1][-1]
        prob = total_weight * numpy.random.random()

        index = 0
        for index, weight_low, weight_high in weights:
            if weight_low < prob and weight_high >= prob:
                break

        # quick test code

        cell = boundary.GetCell(index)
        pnt0 = numpy.array(cell.GetPoints().GetPoint(0))

        pnrm = 1.0

        pnt = numpy.empty(3)
        pnt[:] = pnt0[:]

        for _ in range(1, cell.GetNumberOfPoints()):
            prob = numpy.random.random()
            pnrm = pnrm * prob
            edge = numpy.array(cell.GetPoints().GetPoint(_)) - pnt0
            pnt += pnrm * edge
            pnrm = 1.0 - pnrm

        return pnt

    def get_number_of_insertions(self, time, delta_t):
        """ Return the result of a  poisson series on how many insertions occur."""
        del time
        return numpy.random.poisson(delta_t * self.insertion_rate)


class OptionsReader(object):
    """ Handle processing the XML into python"""
    def __init__(self, options_file=None):

        if options_file:
            libspud.load_options(options_file)

            self.simulation_name = libspud.get_option('/simulation_name')
            self.dimension = libspud.get_option('/geometry/dimension')

    def get_name(self):
        """ Return the simulation name (for output/cross communication with fluidity)."""
        return libspud.get_option('/simulation_name')

    def get_gravity(self):
        """ Return the acceleration due to gravity."""
        options_base = '/physical_parameters/gravity'
        magnitude = 0
        direction = numpy.zeros(3)
        self.dimension = libspud.get_option('/geometry/dimension')

        if libspud.have_option(options_base):
            magnitude = libspud.get_option(options_base + '/magnitude')
            direction[:self.dimension] = libspud.get_option(options_base +
                                                            '/vector_field[0]/prescribed/value[0]/constant')

        return magnitude * direction

    def get_rotation(self):
        """ Return the rotation vector."""
        options_base = '/physical_parameters/coriolis/specified_axis'
        omega = numpy.zeros(3)
        origin = numpy.zeros(3)

        if libspud.have_option(options_base):
            omega[2] = libspud.get_option(options_base + '/rotational_velocity')
            origin[:self.dimension] = libspud.get_option(options_base + '/point_on_axis')

        return omega, origin

    def get_model_option(self, option_name):
        """ interogate the model specific options """

        options_base = '/embedded_models/particle_model/'
        if libspud.have_option(options_base + option_name):
            return libspud.get_option(options_base + option_name)
        # otherwise
        return None

    def get_outlet_ids(self):
        """ interogate the model specific options """
        options_base = '/embedded_models/particle_model/outlet_ids/surface_ids'
        if libspud.have_option(options_base):
            return libspud.get_option(options_base)
        # otherwise
        return None

    def get_inlets(self):
        """ Wrap the inlet data into a class """

        inlets = []

        options_base = '/embedded_models/particle_model/inlet'

        for _ in range(libspud.option_count(options_base)):
            val = None
            options_key = options_base + '[%s]' % _
            surface_ids = libspud.get_option(options_key + '/surface_ids')
            insertion_rate = libspud.get_option(options_key + '/insertion_rate')
            if libspud.have_option(options_key + '/particle_velocity/constant'):
                rvel = libspud.get_option(options_key + '/particle_velocity/constant')
                velocity = lambda x, t: rvel
            elif libspud.have_option(options_key + '/particle_velocity/fluid_velocity'):
                velocity = None
            else:
                g_vars, l_vars = globals(), locals()
                exec(libspud.get_option(options_key + '/particle_velocity/python')) in g_vars, l_vars
                velocity = l_vars['val']
            if libspud.have_option(options_key + '/probability_density_function/constant'):
                rpdf = libspud.get_option(options_key + '/probability_density_function/constant')
                pdf = lambda x, t: rpdf
            elif libspud.have_option(options_key + '/probability_density_function/fluid_velocity'):
                pdf = None
            else:
                g_vars, l_vars = globals(), locals()
                exec(libspud.get_option(options_key + '/probability_density_function/python')) in g_vars, l_vars
                pdf = l_vars['val']

            inlets.append(Inlet(surface_ids, insertion_rate, velocity, pdf))

        return inlets

    def get_mesh_filename(self):
        """Return the mesh file name"""
        if Parallel.is_parallel():
            return libspud.get_option('/geometry/mesh::CoordinateMesh/from_file/file_name') + '_%d.msh' % Parallel.get_rank()
        # otherwise
        return libspud.get_option('/geometry/mesh::CoordinateMesh/from_file/file_name') + '.msh'

    def get_current_time(self):
        """Return the current time from the options file."""
        return libspud.get_option('/timestepping/timestep')

    def get_timestep(self):
        """Return the timestep from the options file."""
        return libspud.get_option('/timestepping/timestep')

    def get_finish_time(self):
        """Return the finish time from the options file."""
        return libspud.get_option('/timestepping/finish_time')

    def get_adapts_at_first_timestep(self):
        """Return the number of fluidity adapts at first timestep."""
        if libspud.have_option('/mesh_adaptivity/hr_adaptivity/adapt_at_first_timestep/number_of_adapts'):
            return libspud.get_option('/mesh_adaptivity/hr_adaptivity/adapt_at_first_timestep/number_of_adapts')
        # otherwise
        return 0

    def get_dump_period(self):
        """Return the dump period and whether this is measured in timesteps."""
        if libspud.have_option('/io/dump_period_in_timesteps'):
            opt_type = libspud.get_child_name('/io/dump_period_in_timesteps', 0)
            period = libspud.get_option('/io/dump_period_in_timesteps/' + opt_type)
            return period, True
        # otherwise
        opt_type = libspud.get_child_name('/io/dump_period', 0)
        period = libspud.get_option('/io/dump_period/' + opt_type)
        return period, False
