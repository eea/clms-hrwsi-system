#!/usr/bin/env python3
"""
Impossible_plan module is an error that occurs when the plan isn't feasable ie 
when the resources are not enough to schedule the processing tasks no matter the time limit.
"""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from HRWSI_System.orchestrator.orchestrator_exceptions.exception_plan import ExceptionPlan

class ImpossiblePlan(ExceptionPlan):
    """
    Error to be raised during Scheduler.check_feasibility().
    This error is raised when the plan isn't feasable no matter what time limit we have.
    """

    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Impossible : {self.message}"
