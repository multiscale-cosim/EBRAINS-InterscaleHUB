# ------------------------------------------------------------------------------
#  Copyright 2020 Forschungszentrum Jülich GmbH and Aix-Marseille Université
# "Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements; and to You under the Apache License,
# Version 2.0. "
#
# Forschungszentrum Jülich
# Institute: Institute for Advanced Simulation (IAS)
# Section: Jülich Supercomputing Centre (JSC)
# Division: High Performance Computing in Neuroscience
# Laboratory: Simulation Laboratory Neuroscience
# Team: Multi-scale Simulation and Design
# ------------------------------------------------------------------------------
from EBRAINS_InterscaleHUB.translator.delegation.elephant_plugin import ElephantPlugin
from EBRAINS_InterscaleHUB.translator.delegation.spike_rate_inter_conversion import SpikeRateConvertor
from EBRAINS_InterscaleHUB.common.interscalehub_utils import debug_log_message

from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.default_directories_enum import DefaultDirectories


class ElephantDelegator:
    """
    NOTE: some functionalities only had on attribute/method, e.g. rate_to_spike.
    -> new Class "spike_rate_conversion" contains all related functionalities.
    """
    def __init__(self, configurations_manager, log_settings, sci_params=None):
        """
        """
        self._log_settings = log_settings
        self._configurations_manager = configurations_manager
        self.__logger = self._configurations_manager.load_log_configurations(
                                        name="ElephantDelegator",
                                        log_configurations=self._log_settings,
                                        target_directory=DefaultDirectories.SIMULATION_RESULTS)
        # init members
        self.spike_rate_conversion = SpikeRateConvertor(
                                        configurations_manager, 
                                        log_settings,
                                        sci_params=sci_params)

        self.elephant_plugin = ElephantPlugin(
                                        configurations_manager, 
                                        log_settings)
        # dir member methods
        self.spikerate_methods = [f for f in dir(SpikeRateConvertor) if not f.startswith('_')]
        self.plugin_methods = [f for f in dir(ElephantPlugin) if not f.startswith('_')]
        debug_log_message(rank=0,  # hardcoded
                          logger=self.__logger,
                          msg="Initialised")

    def __getattr__(self, func):
        """
        """
        # TODO add support to access the attributes of the classes to be delegated
        def method(*args):
            if func in self.spikerate_methods:
                return getattr(self.spike_rate_conversion, func)(*args)
            elif func in self.plugin_methods:
                return getattr(self.elephant_plugin, func)(*args)
            else:
                raise AttributeError
        return method