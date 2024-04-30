#!/usr/bin/env python3
"""
False_plan module is an error that occurs when the plan isn't true ie 
when the plan doesn't respect limit resources.
"""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from HRWSI_System.orchestrator.orchestrator_exceptions.exception_plan import ExceptionPlan

class FalsePlan(ExceptionPlan):
    """
    Error to be raised during Scheduler.check_plan().
    This error is raised when the plan is mathematically false.
    """

    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"False plan : {self.message}"