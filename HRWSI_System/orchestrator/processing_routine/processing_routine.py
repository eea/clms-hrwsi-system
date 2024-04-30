#!/usr/bin/env python3
"""
Processing_routine module is used to represent the processing routine of the processing tasks.
"""

class ProcessingRoutine():
    """Define a processing routine"""

    def __init__(self, name: str,
                 cpu: int,
                 ram: int,
                 storage_space: int,
                 duration: int,
                 docker_image: str):

        self.name = name
        self.cpu = cpu
        self.ram = ram
        self.storage_space = storage_space
        self.duration = duration
        self.docker_image = docker_image
