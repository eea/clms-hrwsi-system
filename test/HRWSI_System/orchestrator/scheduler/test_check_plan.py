"""Tests for check_plan."""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.orchestrator.scheduler.scheduler import Scheduler
from HRWSI_System.orchestrator.processing_task.processing_task import ProcessingTask
from HRWSI_System.orchestrator.processing_routine.processing_routine import ProcessingRoutine
from HRWSI_System.orchestrator.orchestrator_exceptions.false_plan import FalsePlan

def test_task_with_dependency():
    '''
    Scenario:

    - Plan with no respect of dependency

    Expected behaviour:

    - Raises "False plan : No respect of dependency"
    '''

    # Creation of plan with dependencies problem
    processing_routine_a = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=0, depends_on=[2])

    processing_routine_b = ProcessingRoutine(name="foo2", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=1, depends_on=None)

    planning = Scheduler(t_max=2, cpu_max=1, ram_max=1, storage_space_max=1, vm_max=1, task_list=[task_a, task_b])

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_task_with_many_dependencies():
    '''
    Scenario:

    - Plan with no respect of dependencies

    Expected behaviour:

    - Raises "False plan : No respect of dependency"
    '''

    # Creation of plan with dependencies problem
    processing_routine_a = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=0, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_a, task_id=2, t0=1, depends_on=None)

    processing_routine_b = ProcessingRoutine(name="foo2", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_c = ProcessingTask(processing_routine=processing_routine_b, task_id=1, t0=0, depends_on=[1,2])
    planning = Scheduler(t_max=2, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=2, task_list=[task_a, task_b, task_c])

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_needeed_cpu_at_every_time_doesnt_exceed_limit_cpu():
    '''
    Scenario:

    - At every time, needed cpu by Processing_task running exceed limit cpu

    Expected behaviour:

    - Raises "False plan : No respect of CPU limit"
    '''

    # Creation of plan with cpu_max exceeds at a time t
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=0, depends_on=None)
    planning = Scheduler(t_max=2, cpu_max=1, ram_max=2, storage_space_max=2, vm_max=2, task_list=[task_a, task_b])

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_needeed_ram_at_every_time_doesnt_exceed_limit_ram():
    '''
    Scenario:

    - At every time, needed ram by Processing_task running exceed limit ram

    Expected behaviour:

    - Raises "False plan : No respect of RAM limit"
    '''

    # Creation of plan with ram_max exceeds at a time t
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=0, depends_on=None)
    planning = Scheduler(t_max=2, cpu_max=2, ram_max=1, storage_space_max=2, vm_max=2, task_list=[task_a, task_b])

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_needeed_storage_space_at_every_time_doesnt_exceed_limit_storage_space():
    '''
    Scenario:

    - At every time, needed storage_space by Processing_task running exceed limit storage_space

    Expected behaviour:

    - Raises "False plan : No respect of Storage Space limit"
    '''

    # Creation of plan with storage_place_max exceeds at a time t
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=0, depends_on=None)
    planning = Scheduler(t_max=2, cpu_max=2, ram_max=2, storage_space_max=1, vm_max=2, task_list=[task_a, task_b])

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_needeed_vm_at_every_time_doesnt_exceed_limit_vm():
    '''
    Scenario:

    - At every time, needed vm by Processing_task running doesn't exceed limit vm

    Expected behaviour:

    - Raises "False plan : No respect of VM limit"
    '''

    # Creation of plan vm_max exceeds at a time t
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=0, depends_on=None)
    planning = Scheduler(t_max=2, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=1, task_list=[task_a, task_b])

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_all_task_processed_at_the_end_of_the_planning():
    '''
    Scenario:

    - At the end of the plan, not all Processing_task are processed

    Expected behaviour:

    - Raises "False plan : Incomplete plan"
    '''
    # Creation of plan with at least a Processing_task unplanned
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=None, depends_on=None)
    planning = Scheduler(t_max=2, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=2, task_list=[task_a, task_b])

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_task_start_after_starting_time():
    '''
    Scenario:

    - Processing_task begin before the starting time

    Expected behaviour:

    - Raises "False plan : Task begin before starting time"
    '''

    # Creation of plan with a Processing_task with t0<0 
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=-1, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=0, depends_on=None)
    planning = Scheduler(t_max=2, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=1, task_list=[task_a, task_b])

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_task_end_after_limit_time():
    '''
    Scenario:

    - Processing_task end after the limit time t_max

    Expected behaviour:

    - Raises "False plan : Task end after t_max"
    '''

    # Creation of plan with a Processing_task with t0 + duration >= t_max
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=2, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=2, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=0, depends_on=None)
    planning = Scheduler(t_max=3, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=2, task_list=[task_a, task_b])

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_task_plan_only_once():
    '''
    Scenario:

    - At least one Processing_task planned several time

    Expected behaviour:

    - Raises "False plan : Task over planification"
    '''

    # Creation of plan with one processing_task planned two times on same vm on attribute_plan
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=2, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    planning = Scheduler(t_max=3, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=2, task_list=[task_a])
    
    planning.attribution_plan = {"Worker_1" : ["uuid1", "flavour", 0, 2, [task_a, task_a]]}

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

    # Creation of plan with one processing_task planned two times on different vm on attribute_plan
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=2, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    planning = Scheduler(t_max=3, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=2, task_list=[task_a])
    
    planning.attribution_plan = {"Worker_1" : ["uuid1", "flavour", 0, 1, [task_a]], "Worker_2" : ["uuid2", "flavour", 0, 1, [task_a]]}

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_two_task_at_same_time():
    '''
    Scenario:

    - Two Processing_task overlaps

    Expected behaviour:

    - Raises "False plan : Task overlap"
    '''
    # Creation of plan with two tasks begin at same time in same vm in attribute_plan
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=2, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=0, depends_on=None)
    planning = Scheduler(t_max=3, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=2, task_list=[task_a, task_b])

    planning.attribution_plan = {"Worker_1" : ["uuid1", "flavour", 0, 2, [task_a, task_b]]}

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

    # Creation of plan with task overlap in attribute_plan
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=2, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=1, depends_on=None)
    planning = Scheduler(t_max=3, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=2, task_list=[task_a, task_b])
    
    planning.attribution_plan = {"Worker_1" : ["uuid1", "flavour", 0, 2, [task_a, task_b]]}

    try:
        assert planning.check_plan() is False
    except FalsePlan as exc:
        print(exc)

def test_plan_true():
    '''
    Scenario:

    - At every time, needed resources by Processing_task running doesn't exceed limit resources
    - Processing_task with dependencies begin after the end of their dependencies
    - At the end of the plan, all Processing_task are processed
    - Processing_task begin after the starting time
    - Processing_task end before the limit time t_max

    Expected behaviour:

    - Calls the function to check if the plan is True (expected answer : True)
    '''

    # Creation of a True plan
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=2, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=0, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=2, depends_on=[1])
    task_c = ProcessingTask(processing_routine=processing_routine, task_id=3, t0=0, depends_on=None)
    task_d = ProcessingTask(processing_routine=processing_routine, task_id=4, t0=2, depends_on=[3])
    planning = Scheduler(t_max=5, cpu_max=2, ram_max=2, storage_space_max=2, vm_max=2, task_list=[task_a, task_b, task_c, task_d])

    assert planning.check_plan() is True