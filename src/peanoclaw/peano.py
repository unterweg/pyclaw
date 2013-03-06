'''
Created on Jan 29, 2013

@author: kristof
'''

import logging
from ctypes import CDLL
from ctypes import c_bool
from ctypes import c_double
from ctypes import c_int
from ctypes import c_void_p
from ctypes import c_char_p
import signal

class Peano(object):
  '''
  Encapsulation of the Peano library.
  '''


  def __init__(self, solution, initial_minimal_mesh_width, use_dimensional_splitting_optimization, ghostlayer_width, dt_initial, initialization_callback, solver_callback, boundary_condition_callback, interpolation_callback, restriction_callback):
    '''
    Constructor
    '''
    logging.getLogger('peanoclaw').info("Loading Peano-library...")
    self.libpeano = CDLL(self.get_lib_path())
    logging.getLogger('peanoclaw').info("Peano loaded successfully.")
    self.libpeano.pyclaw_peano_new.restype = c_void_p
    self.libpeano.pyclaw_peano_destroy.argtypes = [c_void_p]
    self.libpeano.pyclaw_peano_evolveToTime.argtypes = [c_double, c_void_p, c_void_p, c_void_p]
    
    self.boundary_condition_callback = boundary_condition_callback
    self.solver_callback = solver_callback
    
    # Get parameters for Peano
    dimensions = solution.state.grid.dimensions
    subdivision_factor_x0 = solution.state.grid.dimensions[0].num_cells
    subdivision_factor_x1 = solution.state.grid.dimensions[1].num_cells
    subdivision_factor_x2 = 0 #solution.state.grid.dimensions[2].num_cells #TODO 3D
    number_of_unknowns = solution.state.num_eqn 
    number_of_auxiliar_fields = solution.state.num_aux
    import os, sys
    configuration_file = os.path.join(sys.path[0], 'peanoclaw-config.xml')
      
    self.libpeano.pyclaw_peano_new.argtypes = [ c_double, #Initial mesh width
                                                c_double, #Domain position X0
                                                c_double, #Domain position X1
                                                c_double, #Domain position X2
                                                c_double, #Domain size X0
                                                c_double, #Domain size X1
                                                c_double, #Domain size X2
                                                c_int,    #Subdivision factor X0
                                                c_int,    #Subdivision factor X1
                                                c_int,    #Subdivision factor X2
                                                c_int,    #Number of unknowns
                                                c_int,    #Number of auxiliar fields
                                                c_int,    #Ghostlayer width
                                                c_double, #Initial timestep size
                                                c_char_p, #Config file
                                                c_bool,   #Use dimensional splitting
                                                c_void_p, #q Initialization callback
                                                c_void_p, #Boundary condition callback
                                                c_void_p, #Solver callback
                                                c_void_p, #Interpolation callback
                                                c_void_p] #Restriction callback
    self.peano = self.libpeano.pyclaw_peano_new(c_double(initial_minimal_mesh_width),
                                                c_double(dimensions[0].lower),
                                                c_double(dimensions[1].lower),
                                                c_double(0.0), #Todo 3D
                                                c_double(dimensions[0].upper - dimensions[0].lower),
                                                c_double(dimensions[1].upper - dimensions[1].lower),
                                                c_double(0.0), #Todo 3D
                                                subdivision_factor_x0,
                                                subdivision_factor_x1,
                                                subdivision_factor_x2,
                                                number_of_unknowns,
                                                number_of_auxiliar_fields,
                                                ghostlayer_width,
                                                dt_initial,
                                                c_char_p(configuration_file),
                                                use_dimensional_splitting_optimization,
                                                initialization_callback.get_initialization_callback(),
                                                boundary_condition_callback.get_boundary_condition_callback(),
                                                solver_callback.get_solver_callback(),
                                                None,
                                                None)
    
    # Set PeanoSolution
    import clawpack.peanoclaw as peanoclaw
    if(isinstance(solution, peanoclaw.Solution)):
        solution.peano = self.peano
        solution.libpeano = self.libpeano
    else:
        logging.getLogger('peanoclaw').warning("Use peanoclaw.Solution instead of pyclaw.Solution together with peanoclaw.Solver to provide plotting functionality.")
    
    #Causes Ctrl+C to quit Peano
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    
            
  def get_lib_path(self):
    r"""
    Returns the path in which the shared library of Peano is located in.
    """
    import os
    import platform
    import clawpack.peanoclaw as peanoclaw
    if platform.system() == 'Linux':
        shared_library_extension = 'so'
    elif platform.system() == 'Darwin':
        shared_library_extension = 'dylib'
    else:
        raise("Unsupported operating system. Only Linux and MacOS supported currently.")    
    
    print(os.path.join(os.path.dirname(peanoclaw.__file__), 'libpeano-claw-2d.' + shared_library_extension))
    return os.path.join(os.path.dirname(peanoclaw.__file__), 'libpeano-claw-2d.' + shared_library_extension)
  
  def evolve_to_time(self, tend):
    self.libpeano.pyclaw_peano_evolveToTime(tend, self.peano, self.boundary_condition_callback.get_boundary_condition_callback(), self.solver_callback.get_solver_callback())

  def teardown(self):
    self.libpeano.pyclaw_peano_destroy(self.peano)
    
    
    