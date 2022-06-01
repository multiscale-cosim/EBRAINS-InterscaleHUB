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
#
# ------------------------------------------------------------------------------ 
# 
from mpi4py import MPI
import time
import numpy as np

<<<<<<< HEAD:refactored_modular/Communicator_tvb_to_nest.py
from EBRAINS_InterscaleHUB.refactored_modular.Communicator import Communicator
from EBRAINS_InterscaleHUB.refactored_modular import interscalehub_utils
from EBRAINS_InterscaleHUB.refactored_modular import interscalehub_mediator as mediator
#from EBRAINS_InterscaleHUB.Interscale_hub.transformer import generate_data
=======
from EBRAINS_InterscaleHUB.refactored_modular.communicator_base import BaseCommunicator
from EBRAINS_InterscaleHUB.refactored_modular import interscalehub_utils
from EBRAINS_InterscaleHUB.refactored_modular.interscalehub_enums import DATA_BUFFER_STATES
>>>>>>> b7850ec8a33de877557fb4cdaa1c899d4efcaaf9:refactored_modular/communicator_tvb_to_nest.py

from EBRAINS_RichEndpoint.Application_Companion.common_enums import Response

# NestTvbPivot and TvbNestPivot classes:
# TODO: proper abstraction -> extract the usecase details from the general implementation
# -> Init, start, stop are pretty much the same every time
# -> incoming (receive) and outgoing (send) loops (M:N mapping)
# -> the analyse (method) should be 
#   a) pivot, as raw data to cosim data 
#   b) transform (might be trivial) and 
#   c) analysis (might be trivial)

# TODO: rework on the receive and send loops (both, general coding style and usecase specifics)

<<<<<<< HEAD:refactored_modular/Communicator_tvb_to_nest.py
class CommunicatorTvbNest(Communicator):
=======

class CommunicatorTvbNest(BaseCommunicator):
>>>>>>> b7850ec8a33de877557fb4cdaa1c899d4efcaaf9:refactored_modular/communicator_tvb_to_nest.py
    '''
    Implements the PivotBaseClass for abstracting the pivot operations and
    the underlying communication protocol. This class provides wrappers
    for receiving the data from TVB simulator and sending it to NEST simulator
    after processing/transforming to the required format.
    '''
<<<<<<< HEAD:refactored_modular/Communicator_tvb_to_nest.py
    def __init__(self, configurations_manager, log_settings, name, databuffer,
                 intracomm, param, comm_receiver, comm_sender):
        '''
        '''
        super().__init__(configurations_manager,
                         log_settings,
                         name,
                         databuffer
                         )
        
        # Parameter for transformation and analysis
        self.__param = param
        # INTERcommunicator
        # TODO: Revisit the protocol to TVB and NEST
        # TODO: rank 0 and rank 1 hardcoded
        if intracomm.Get_rank() == 1:
            self.__comm_receiver = comm_receiver
            self.__num_sending = self.__comm_receiver.Get_remote_size()
        elif intracomm.Get_rank() == 0:    
            self.__comm_sender = comm_sender
            self.__num_receiving = self.__comm_sender.Get_remote_size()
        self.__logger.info("Initialised")
=======
    def __init__(self, configurations_manager, log_settings,
                 parameters, data_buffer_manager, mediator):
        '''
        Implements the BaseCommunicator. It 
        1) Receives the data from TVB
        2) Transforms it to the required format such as to 'spikes'
        3) Sends the transformed data to NEST
        '''
         # initialize the common settings such as logger, data buffer, etc.
        super().__init__(configurations_manager,
                         log_settings,
                         __name__,
                         data_buffer_manager,
                         mediator)
        
        # Parameter for transformation and analysis
        self.__parameters = parameters
        self.__logger.info("Initialized")
>>>>>>> b7850ec8a33de877557fb4cdaa1c899d4efcaaf9:refactored_modular/communicator_tvb_to_nest.py

    def start(self, intra_communicator, inter_comm_receiver, inter_comm_sender):
        '''
        Start the pivot operation.
        M:N mapping of MPI ranks, receive data, further process data.
        
        MVP: receive on rank 0, do the rest on rank 1.
        '''
        # NOTE  self.__comm_receiver, self.__comm_sender, self.__num_sending
        # and self.__num_receiving are defined in Base class.

        # Rank-0 will receive the data
        if intra_communicator.Get_rank() == 0:
            # set inter_communicator for sending the data
            self.__comm_sender = inter_comm_sender
            self.__num_receiving = self.__comm_sender.Get_remote_size()
            return self._send()
<<<<<<< HEAD:refactored_modular/Communicator_tvb_to_nest.py
        elif intracomm.Get_rank() == 1: #  Science/analyse and sender to TVB, rank 1
            return self._receive()
=======
>>>>>>> b7850ec8a33de877557fb4cdaa1c899d4efcaaf9:refactored_modular/communicator_tvb_to_nest.py

        # Rank-1 will transform and send the data
        elif intra_communicator.Get_rank() == 1:
            # set inter_communicator for receiving the data
            self.__comm_receiver = inter_comm_receiver
            self.__num_sending = self.__comm_receiver.Get_remote_size()
            return self._receive()

    def stop(self):
        '''
        TODO: proper execution of stop command
        '''
        self.__stop = True
        return Response.OK

    def _receive(self):
        '''
        Receive data on rank 0. Put it into the shared mem buffer.
        Replaces the former 'receive' function.
        NOTE: First refactored version -> not pretty, not final. 
        '''
        # The last two buffer entries are used for shared information
        # --> they replace the status_data variable from previous version
        # --> find more elegant solution?
        # set buffer to 'ready to receive from tvb'
        # self.__databuffer[-1] = 1
        self.__data_buffer_manager.set_ready_at(index=-1)

        # marks the 'head' of the buffer
        # self.__databuffer[-2] = 0
        self.__data_buffer_manager.set_head_at(index=-2)

        # init placeholder for incoming data
        size = np.empty(1, dtype='i') # size of the rate-array
        status_ = MPI.Status()
        # self.__logger.info("TVBtoNEST -- consumer/receiver -- Rank:"+str(self.__comm_receiver.Get_rank()))
        while True:
            # NOTE: Check communication protocol between simulators and transformers!
            requests=[]
            for rank in range(self.__num_sending):
                requests.append(self.__comm_receiver.isend(True,dest=rank,tag=0))
            MPI.Request.Waitall(requests)
            # NOTE: works for now, needs rework if multiple ranks are used on TVB side
            # we receive from "ANY_SOURCE", but only check the status_ of the last receive...
            # get the starting and ending time of the simulation step
            # NEW: receive directly into the buffer
            # self.__comm_receiver.Recv([self.__databuffer[0:], MPI.DOUBLE], source=0, tag=MPI.ANY_TAG, status=status_)
            data_buffer = self.__data_buffer_manager.get_from(starting_index=0)
            self.__comm_receiver.Recv([data_buffer, MPI.DOUBLE], source=0, tag=MPI.ANY_TAG, status=status_)
            if status_.Get_tag() == 0:
                # wait until ready to receive new data (i.e. the sender has cleared the buffer)
                # while self.__databuffer[-1] != 1: # TODO: use MPI, remove the sleep
                while self.__data_buffer_manager.get_at(index=-1) != DATA_BUFFER_STATES.READY:
                    time.sleep(0.001)
                    pass
                # Get the size/shape of the data
                self.__comm_receiver.Recv([size, 1, MPI.INT], source=status_.Get_source(), tag=0, status=status_)
                # NEW: receive directly into the buffer
                # First two entries are the times, see above
                # self.__comm_receiver.Recv([self.__databuffer[2:], MPI.DOUBLE], source=status_.Get_source(), tag=0, status=status_)
                data_buffer = self.__data_buffer_manager.get_from(starting_index=2)
                self.__comm_receiver.Recv([data_buffer, MPI.DOUBLE], source=status_.Get_source(), tag=0, status=status_)
                # Mark as 'ready to do analysis'
                # self.__databuffer[-1] = 0
                self.__data_buffer_manager.set_head_at(index=-1)

                # self.__databuffer[-2] = size # info about size of data array
                self.__data_buffer_manager.set_custom_value_at(index=-2, value=size)

                # continue receiving the data
                continue
            elif status_.Get_tag() == 1:
                # NOTE: simulation ended
                # everything goes fine, terminate the loop and respond with OK
                return Response.OK
            else:
                # A 'bad' MPI tag is received,
                # log the exception with traceback
                interscalehub_utils.log_exception(
                    log_message="bad mpi tag :",
                    mpi_tag_received=status_.Get_tag())
                # terminate with Error
                return Response.ERROR
        
        # logger.info('TVB_to_NEST: End of receive function')

    def _send(self):
        '''
        Send data to NEST (multiple MPI ranks possible).
        Replaces the former 'send' function.
        NOTE: First refactored version -> not pretty, not final. 
        '''
        status_ = MPI.Status()
        # NOTE: hardcoded...
        check = np.empty(1,dtype='b')
        size_list = np.empty(1, dtype='i')
        id_first_spike_detector = self.__parameters['id_first_spike_detector']


        ###########################################################
        #TODO Refactor to move this functionality to appropriate location
        
        #NOTE As per protocol, it should be the response message of 'init'
        # command, and should return the PID and the port information

        import os
        from EBRAINS_RichEndpoint.Application_Companion.common_enums import INTEGRATED_SIMULATOR_APPLICATION as SIMULATOR
        pid_and_local_minimum_step_size = \
        {SIMULATOR.PID.name: os.getpid(),
        SIMULATOR.LOCAL_MINIMUM_STEP_SIZE.name: 0.0}
        print(f'{pid_and_local_minimum_step_size}')
        ###########################################################
        
        while True:
            # TODO: This is still not correct. We only check for the Tag of the last rank.
            # IF all ranks send always the same tag in one iteration (simulation step)
            # then this works. But it should be handled differently!!!!
            for rank in range(self.__num_receiving):
                self.__comm_sender.Recv([check, 1, MPI.CXX_BOOL], source=rank, tag=MPI.ANY_TAG, status=status_)
            if status_.Get_tag() == 0:
                # wait until the receiver has cleared the buffer, i.e. filled with new data
                # while self.__databuffer[-1] != 0: # TODO: use MPI, remove the sleep
                while self.__data_buffer_manager.get_at(index=-1) != DATA_BUFFER_STATES.HEAD: # TODO: use MPI, remove the sleep
                    time.sleep(0.001)
                    pass

                # NOTE: calling the mediator which calls the corresponding transformer functions
<<<<<<< HEAD:refactored_modular/Communicator_tvb_to_nest.py
                spikes_times = mediator.rate_to_spike(self.__databuffer)
                
                # Mark as 'ready to receive next simulation step'
                self.__databuffer[-1] = 1
=======
                # TODO: change to inject the buffer in the wrapper method of mediator
                # spikes_times = mediator.rate_to_spike(self.__data_buffer_manager.mpi_shared_memory_buffer)
                spikes_times = self.__mediator.rate_to_spike()
>>>>>>> b7850ec8a33de877557fb4cdaa1c899d4efcaaf9:refactored_modular/communicator_tvb_to_nest.py
                
                # Mark as 'ready to receive next simulation step'
                # self.__databuffer[-1] = 1
                self.__data_buffer_manager.set_ready_at(index=-1)

                ### OLD code, kept the communication and science as it is for now
                # NOTE: Receive from status_.Get_source() and rank
                # Send to status_.Get_source() and rank
                # why?
                # a second status_ object is used, should not be named the same
                for rank in range(self.__num_receiving):
                    # NOTE: hardcoded 10 in simulation mocks
                    self.__comm_sender.Recv([size_list, 1, MPI.INT], source=rank, tag=0, status=status_)
                    if size_list[0] != 0:
                        list_id = np.empty(size_list, dtype='i')
                        # NOTE: hardcoded np.arange(0,10,1) in simulation mocks
                        self.__comm_sender.Recv([list_id, size_list, MPI.INT], source=status_.Get_source(), tag=0, status=status_)
                        # Select the good spike train and send it
                        # TODO: create lists, append to lists, nested loops
                        # this is slow and will be a bottleneck when we scale up.
                        data = []
                        shape = []
                        for i in list_id:
                            shape += [spikes_times[i-id_first_spike_detector].shape[0]]
                            data += [spikes_times[i-id_first_spike_detector]]
                        send_shape = np.array(np.concatenate(([np.sum(shape)],shape)), dtype='i')
                        # firstly send the size of the spikes train
                        # self.__logger.info("sending size of train")
                        self.__comm_sender.Send([send_shape, MPI.INT], dest=status_.Get_source(), tag=list_id[0])
                        # secondly send the spikes train
                        data = np.concatenate(data).astype('d')
                        # self.__logger.info("sending train")
                        self.__comm_sender.Send([data, MPI.DOUBLE], dest=rank, tag=list_id[0])
                ### OLD code end
            elif status_.Get_tag() == 1:
                # NOTE: one sim step? inconsistent with receiving side
                # continue sending data
                continue
            elif status_.Get_tag() == 2:
                # NOTE: simulation ended
                # break
                # everything goes fine, terminate the loop and respond with OK
                return Response.OK
            else:
                # A 'bad' MPI tag is received,
                # log the exception with traceback
                interscalehub_utils.log_exception(
                    logger=self.__logger,
                    log_message="bad mpi tag :",
                    mpi_tag_received=status_.Get_tag())
                # terminate with Error
                return Response.ERROR
        
'''
    def _transform(self):
<<<<<<< HEAD:refactored_modular/Communicator_tvb_to_nest.py
        generator = generate_data(self.__param)
=======
        generator = generate_data(self.__parameters)
>>>>>>> b7850ec8a33de877557fb4cdaa1c899d4efcaaf9:refactored_modular/communicator_tvb_to_nest.py
        # NOTE: count is a hardcoded '0'. Why?
        # time_step are the first two doubles in the buffer
        # rate is a double array, which size is stored in the second to last index
        if int(self.__databuffer[-2]) == 0:
            spikes_times = generator.generate_spike(0,
                                                self.__databuffer[:2],
                                                self.__databuffer[2:])
        else:
            spikes_times = generator.generate_spike(0,
                                                self.__databuffer[:2],
                                                self.__databuffer[2:int(self.__databuffer[-2])])
        return spikes_times
'''
