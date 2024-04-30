#!/usr/bin/env python3
"""
Processing_task module is used to represent the processing tasks to be schedulded by the scheduler
and executed on workers.
"""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from HRWSI_System.orchestrator.processing_routine.processing_routine import ProcessingRoutine

class ProcessingTask():
    """Define a processing task"""

    def __init__(self, processing_routine: ProcessingRoutine,
                 task_id: int,
                 t0: int,
                 depends_on: list[int]):

        self.processing_routine = processing_routine
        self.task_id = task_id
        self.t0 = t0
        self.depends_on = depends_on
