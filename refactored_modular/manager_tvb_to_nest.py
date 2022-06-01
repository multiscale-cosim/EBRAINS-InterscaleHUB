# ------------------------------------------------------------------------------
#  Copyright 2020 Forschungszentrum Jülich GmbH
# "Licensed to the Apache Software Foundation (ASF) under one or more contributor
#  license agreements; and to You under the Apache License, Version 2.0. "
#
# Forschungszentrum Jülich
#  Institute: Institute for Advanced Simulation (IAS)
#    Section: Jülich Supercomputing Centre (JSC)
#   Division: High Performance Computing in Neuroscience
# Laboratory: Simulation Laboratory Neuroscience
#       Team: Multi-scale Simulation and Design
# ------------------------------------------------------------------------------

import numpy as np
import os
import time


from EBRAINS_InterscaleHUB.refactored_modular.commuincator_tvb_to_nest import CommunicatorTvbNest                       
from EBRAINS_InterscaleHUB.refactored_modular.manager import InterscaleHubBaseManager                                   
from EBRAINS_InterscaleHUB.refactored_modular.interscalehub_enums import DATA_EXCHANGE_DIRECTION                        
from EBRAINS_RichEndpoint.Application_Companion.common_enums import Response                                            
from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.default_directories_enum import DefaultDirectories 


class TvbToNestManager(InterscaleHubBaseManager):
    '''
    Implements the InterscaleHubBaseManager to
    1) Interact with InterscaleHub Facade to steer the execution
    2) Manage the InterscaleHub functionality.
    '''
    def __init__(self, parameters, direction, configurations_manager, log_settings):
        '''
        Init params, create buffer, open ports, accept connections
        '''
        
        self.__log_settings = log_settings
        self.__configurations_manager = configurations_manager
        self.__logger = self.__configurations_manager.load_log_configurations(
                                        name="InterscaleHub -- TVB_TO_NEST Manager",
                                        log_configurations=self.__log_settings,
                                        target_directory=DefaultDirectories.SIMULATION_RESULTS)
        
        # 1) param stuff, create IntercommManager
        self.__logger.debug("Init Params...")
        super().__init__(parameters,
                         DATA_EXCHANGE_DIRECTION.TVB_TO_NEST,
                         self.__configurations_manager,
                         self.__log_settings)
        self.__tvb_nest_communicator = None
        # TODO: set via XML settings? POD
        self.__buffersize = 2 + self.__max_events # 2 doubles: [start_time,end_time] of simulation step
        
        # path to receive_from_tvb (TVB)
        self.__logger.debug("reading port info for receiving from TVB...")
        self.__input_path = self.__get_path_to_TVB()
        # path to spike_generators (NEST)
        self.__logger.debug("reading port info for spike generators...")
        self.__output_path = self.__get_path_to_spike_generators()

        self.__logger.debug("Init Params done.")
        
        # 2) create buffer in self.__databuffer
        self.__logger.debug("Creating MPI shared memory Buffer...")
        self.__databuffer = self.__get_mpi_shared_memory_buffer(self.__buffersize)
        self.__logger.info("Buffer created.")
        
        # 3) Data channel setup
        self.__logger.info("setting up data channels...")
        self.__data_channel_setup(direction)
        self.__logger.info("data channels open and ready.")
        
    def __data_channel_setup(self):
        '''
        Open ports and register connection details.
        Accept connection on ports and create INTER communicators.
        
        MVP: register = write port details to file.
        MVP: Two connections 
            - input = incoming simulation data
            - output = outgoing simulation data
        '''
        # NOTE: create port files and make connection
        # In Demo example: producer/Consumer are inhertied from mpi_io_extern,
        # and then they are started as threads which then call mpi_io_extern run() method
        # which then calls make_connection() method

        # Case: data exchange direction is from NEST-to-TVB
        if self.__intra_comm.Get_rank() == 0:
            self.__output_comm, self.__output_port = self.__set_up_connection(self.__output_path)
            self.__input_comm = None
        else:
            self.__input_comm, self.__input_port = self.__set_up_connection(self.__input_path)
            self.__output_comm = None

    def __get_path_to_TVB(self):
        '''
        helper function to get the path to file containing the connection
        details of TVB for receiving the data from it.
        '''
        # NOTE transformer id is hardcoded as 0 in base class
        return [
            self.__path + "/transformation/receive_from_tvb/" + 
            str(self.__id_proxy_nest_region[self.__transformer_id]) + ".txt"]

    def __get_path_to_spike_generators(self):
        '''
        helper function to get the path to file containing the connection
        details of spike detectors (NEST) for sending the data.
        '''
        # wait until NEST writes the spike generators ids
        while not os.path.exists(self.__path + '/nest/spike_generator.txt.unlock'):
            self.__logger.info("spike generator ids not found yet, retry in 1 second")
            time.sleep(1)
        
        # load data from the file
        spike_generator = np.loadtxt(self.__path + '/nest/spike_generator.txt', dtype=int)
        # case of one spike generator
        try:
            if len(spike_generator.shape) < 2:
                spike_generator = np.expand_dims(spike_generator, 0)
            self.__logger.debug(f"spike generator shape: {spike_generator.shape}")
        except Exception:
            self.__logger.exception('bad shape of spike generator')
            pass  # TODO discuss if terminate with error

        self.__logger.debug(f"spike_generators: {spike_generator}")

        # get the id of first spike generator
        id_first_spike_generator = spike_generator[self.__transformer_id][0]
        # get total number of spike generators
        nb_spike_generators = len(spike_generator[self.__transformer_id])
        # prepare the list of path to spike generators
        path_to_spike_generators = []
        # read from the files to get the path to spike generators
        for i in range(nb_spike_generators):
            # populate the list with path to spike generators
            path_to_spike_generators.append(
                os.path.join(self.__path + "/transformation/spike_generator/",
                             str(id_first_spike_generator + i) + ".txt")
            )

        # return the path to spike generators i.e. receive from TVB
        return path_to_spike_generators

    def start(self):
        '''
        implementation of abstract method to start transformation and
        exchanging the data with TVB and NEST.
        '''
        self.__logger.info("Start data transfer and usecase science...")
        
        # initialize Communicator
        self.__tvb_nest_communicator = CommunicatorTvbNest(
            self.__configurations_manager,
            self.__log_settings,
            self.__parameters,
            self.__interscalehub_buffer_manager)
        
        # start exchanging the data
        if self.__tvb_nest_communicator.start(self.__intra_comm,
                                              self.__input_comm,
                                              self.__output_comm) == Response.ERROR:
            # Case a: something went wrong during the data exchange
            # NOTE the details are already been logged at the origin of the error
            # now terminate with error
            self.__logger.critical('Got error while exchanging the data.')
            return Response.ERROR
        else:
            # Case b: everything went well
            return Response.OK

    def stop(self):
        '''
        implementation of the abstract method to conclude the pivot operations
        and stop exchanging the data.

        TODO: add error handling and fail checks
        '''
        self.__logger.info("Stop InterscaleHub and disconnect...")
        self.__tvb_nest_communicator.stop()
        if self.__intra_comm.Get_rank() == 0:
            self.__intercomm_manager.close_and_finalize(self.__output_comm, self.__output_port)
        else:
            self.__intercomm_manager.close_and_finalize(self.__input_comm, self.__input_port)
