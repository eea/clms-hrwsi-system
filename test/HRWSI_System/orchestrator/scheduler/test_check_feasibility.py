"""Tests for check_feasability."""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.orchestrator.scheduler.scheduler import Scheduler
from HRWSI_System.orchestrator.processing_task.processing_task import ProcessingTask
from HRWSI_System.orchestrator.processing_routine.processing_routine import ProcessingRoutine
from HRWSI_System.orchestrator.orchestrator_exceptions.impossible_plan import ImpossiblePlan

def test_time_to_processed_all_task():
    '''
    Scenario:

    - We don't have time to processed all processing_task in t_max

    Expected behaviour:

    - Raises "Impossible : Not enough time"
    '''

    # Initialisation of Plan with sum of Processing_task duration > t_max and resources allow only one task at same time
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=None, depends_on=None)
    planning = Scheduler(t_max=1, cpu_max=1, ram_max=1, storage_space_max=1, vm_max=1, task_list=[task_a, task_b])

    try:
        assert planning.check_feasibility() is False
    except ImpossiblePlan as exc:
        print(exc)

def test_routine_cpu_doesnt_exceed_limit_cpu():
    '''
    Scenario:

    - Processing_routine cpu exceed limit cpu

    Expected behaviour:

    - Raises "Impossible : Not enough CPU"
    '''

    # Initialisation of Plan with a Processing_routine cpu > cpu_max
    processing_routine = ProcessingRoutine(name="foo", cpu=2, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=None, depends_on=None)
    planning = Scheduler(t_max=1, cpu_max=1, ram_max=1, storage_space_max=1, vm_max=1, task_list=[task_a])

    try:
        assert planning.check_feasibility() is False
    except ImpossiblePlan as exc:
        print(exc)

def test_routine_ram_doesnt_exceed_limit_ram():
    '''
    Scenario:

    - Processing_routine ram exceed limit ram

    Expected behaviour:

    - Raises "Impossible : Not enough RAM"
    '''

    # Initialisation of Plan with a Processing_routine ram > ram_max
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=2, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=None, depends_on=None)
    planning = Scheduler(t_max=1, cpu_max=1, ram_max=1, storage_space_max=1, vm_max=1, task_list=[task_a])

    try:
        assert planning.check_feasibility() is False
    except ImpossiblePlan as exc:
        print(exc)

def test_routine_storage_space_doesnt_exceed_limit_storage_space():
    '''
    Scenario:

    - Processing_routine storage space doesn't exceed limit storage space

    Expected behaviour:

    - Raises "Impossible : Not enough Storage Space"
    '''

    # Initialisation of Plan with a Processing_routine storage_space > storage_space_max
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=2, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=None, depends_on=None)
    planning = Scheduler(t_max=1, cpu_max=1, ram_max=1, storage_space_max=1, vm_max=1, task_list=[task_a])

    try:
        assert planning.check_feasibility() is False
    except ImpossiblePlan as exc:
        print(exc)

def test_vm_max_doesnt_equal_zero():
    '''
    Scenario:

    - vm_max = 0

    Expected behaviour:

    - Raises "Impossible : Not enough VM"
    '''

    # Initialisation of Plan with vm_max = 0
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=None, depends_on=None)
    planning = Scheduler(t_max=1, cpu_max=1, ram_max=1, storage_space_max=1, vm_max=0, task_list=[task_a])

    try:
        assert planning.check_feasibility() is False
    except ImpossiblePlan as exc:
        print(exc)

def test_plan_feasable():
    '''
    Scenario:

    - Processing_routine resources doesn't exceed limit resources
    - We have time to processed all processing_task in t_max
    - We have at least one VM

    Expected behaviour:

    - Calls the function to check the feasibility of the plan (expected answer : True)
    '''

    # Initialisation of feasable plan
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=None, depends_on=None)
    planning = Scheduler(t_max=1, cpu_max=1, ram_max=1, storage_space_max=1, vm_max=1, task_list=[task_a])

    assert planning.check_feasibility()
