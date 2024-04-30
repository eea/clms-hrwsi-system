#!/usr/bin/env python3
"""
Exception_plan module implements the template for plan exceptions.
It is meant to be used when raising error on the feasibility, validity,
or quality of a processing plan computed by the scheduler.
"""

class ExceptionPlan(Exception):
    """
    Template for exceptions that occur at the scheduling stage.
    """

    def __init__(self, message=""):
        Exception.__init__(self)
        self.message = message
