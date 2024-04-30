"""Tests for plan."""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.orchestrator.processing_task.processing_task import ProcessingTask
from HRWSI_System.orchestrator.processing_routine.processing_routine import ProcessingRoutine
from HRWSI_System.orchestrator.scheduler.matrix_scheduler import MatrixScheduler

def test_task_compactness():
    '''
    Scenario:

    - Creation of a plan and verification that the solution found is the one expected
    - We limit the materials resources and not the time to see if compactness is respected

    Expected behaviour:

    - Processing_task processed as fast as possible
    '''

    # Creation of a plan
    processing_routine = ProcessingRoutine(name="foo", cpu=1, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine, task_id=2, t0=None, depends_on=[1])
    planning = MatrixScheduler(t_max=5, cpu_max=1, ram_max=1, storage_space_max=1, vm_max=1, task_list=[task_a, task_b])

    # Verification of plan compactness
    planning.plan()

    assert planning.task_list[0].t0 == 0
    assert planning.task_list[1].t0 == 1

def test_plan_correct_compactness():
    '''
    Scenario:

    - Creation of a plan and verification that the solution found is the one expected
    - We limit all the resources to see if compactness is respected with dependencies

    Expected behaviour:

    - Processing_task need to be processed with a minimal resources
    - Processing_task need to be processed as fast as possible
    '''

    processing_routine_a = ProcessingRoutine(name="foo", cpu=2, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_a, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_a, task_id=3, t0=None, depends_on=None)

    processing_routine_b = ProcessingRoutine(name="foo2", cpu=2, ram=1, storage_space=1, duration=3, docker_image="bar")
    task_d = ProcessingTask(processing_routine=processing_routine_b, task_id=4, t0=None, depends_on=[1])
    task_e = ProcessingTask(processing_routine=processing_routine_b, task_id=5, t0=None, depends_on=[2])
    task_f = ProcessingTask(processing_routine=processing_routine_b, task_id=6, t0=None, depends_on=[3])

    processing_routine_c = ProcessingRoutine(name="foo3", cpu=1, ram=1, storage_space=1, duration=2, docker_image="bar")
    task_g = ProcessingTask(processing_routine=processing_routine_c, task_id=7, t0=None, depends_on=[4])
    task_h = ProcessingTask(processing_routine=processing_routine_c, task_id=8, t0=None, depends_on=[5])
    task_i = ProcessingTask(processing_routine=processing_routine_c, task_id=9, t0=None, depends_on=[6])

    planning = MatrixScheduler(t_max=11, cpu_max=4, ram_max=4, storage_space_max=4, vm_max=4, task_list=[task_a, task_b,
                                                                                                   task_c, task_d,
                                                                                                   task_e, task_f,
                                                                                                   task_g, task_h,
                                                                                                   task_i])

    planning.plan()

    assert planning.task_list[0].t0 == 0
    assert planning.task_list[1].t0 == 1
    assert planning.task_list[2].t0 == 0
    assert planning.task_list[3].t0 == 2
    assert planning.task_list[4].t0 == 5
    assert planning.task_list[5].t0 == 1
    assert planning.task_list[6].t0 == 8
    assert planning.task_list[7].t0 == 8
    assert planning.task_list[8].t0 == 4

def test_plan_correct_minimal_resources_and_compactness():
    '''
    Scenario:

    - Creation of a plan and verification that the solution found is the one expected
    - We limit the time and not the materials resources to see if compactness is respected with dependencies

    Expected behaviour:

    - Processing_task need to be processed with a minimal resources
    - Processing_task need to be processed as fast as possible
    '''

    processing_routine_a = ProcessingRoutine(name="foo", cpu=2, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_a, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_a, task_id=3, t0=None, depends_on=None)

    processing_routine_b = ProcessingRoutine(name="foo2", cpu=2, ram=1, storage_space=1, duration=3, docker_image="bar")
    task_d = ProcessingTask(processing_routine=processing_routine_b, task_id=4, t0=None, depends_on=[1])
    task_e = ProcessingTask(processing_routine=processing_routine_b, task_id=5, t0=None, depends_on=[2])
    task_f = ProcessingTask(processing_routine=processing_routine_b, task_id=6, t0=None, depends_on=[3])

    processing_routine_c = ProcessingRoutine(name="foo3", cpu=1, ram=1, storage_space=1, duration=2, docker_image="bar")
    task_g = ProcessingTask(processing_routine=processing_routine_c, task_id=7, t0=None, depends_on=[4])
    task_h = ProcessingTask(processing_routine=processing_routine_c, task_id=8, t0=None, depends_on=[5])
    task_i = ProcessingTask(processing_routine=processing_routine_c, task_id=9, t0=None, depends_on=[6])

    planning = MatrixScheduler(t_max=11, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b,
                                                                                                       task_c, task_d,
                                                                                                       task_e, task_f,
                                                                                                       task_g, task_h,
                                                                                                       task_i])

    planning.plan()

    assert planning.task_list[0].t0 == 0
    assert planning.task_list[1].t0 == 1
    assert planning.task_list[2].t0 == 0
    assert planning.task_list[3].t0 == 2
    assert planning.task_list[4].t0 == 5
    assert planning.task_list[5].t0 == 1
    assert planning.task_list[6].t0 == 8
    assert planning.task_list[7].t0 == 8
    assert planning.task_list[8].t0 == 4

def test_plan_correct_minimal_resources():
    '''
    Scenario:

    - Creation of a plan and verification that the solution found is the one expected
    - We doesn't limit the resources to see if compactness is respected with dependencies

    Expected behaviour:

    - Processing_task need to be processed with a minimal resources
    - Processing_task need to be processed as fast as possible
    '''

    processing_routine_a = ProcessingRoutine(name="foo", cpu=2, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_a, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_a, task_id=3, t0=None, depends_on=None)

    processing_routine_b = ProcessingRoutine(name="foo2", cpu=2, ram=1, storage_space=1, duration=3, docker_image="bar")
    task_d = ProcessingTask(processing_routine=processing_routine_b, task_id=4, t0=None, depends_on=[1])
    task_e = ProcessingTask(processing_routine=processing_routine_b, task_id=5, t0=None, depends_on=[2])
    task_f = ProcessingTask(processing_routine=processing_routine_b, task_id=6, t0=None, depends_on=[3])

    processing_routine_c = ProcessingRoutine(name="foo3", cpu=1, ram=1, storage_space=1, duration=2, docker_image="bar")
    task_g = ProcessingTask(processing_routine=processing_routine_c, task_id=7, t0=None, depends_on=[4])
    task_h = ProcessingTask(processing_routine=processing_routine_c, task_id=8, t0=None, depends_on=[5])
    task_i = ProcessingTask(processing_routine=processing_routine_c, task_id=9, t0=None, depends_on=[6])

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b,
                                                                                                       task_c, task_d,
                                                                                                       task_e, task_f,
                                                                                                       task_g, task_h,
                                                                                                       task_i])

    planning.plan()

    assert planning.task_list[0].t0 == 0
    assert planning.task_list[1].t0 == 1
    assert planning.task_list[2].t0 == 2
    assert planning.task_list[3].t0 == 3
    assert planning.task_list[4].t0 == 6
    assert planning.task_list[5].t0 == 9
    assert planning.task_list[6].t0 == 12
    assert planning.task_list[7].t0 == 14
    assert planning.task_list[8].t0 == 16

def test_plan_write_attribute_plan():
    '''
    Scenario:

    - Creation of a plan and verification that the attribution_plan is write

    Expected behaviour:

    - attribution_plan is not None
    '''

    processing_routine_a = ProcessingRoutine(name="foo", cpu=2, ram=1, storage_space=1, duration=1, docker_image="bar")
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_a, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_a, task_id=3, t0=None, depends_on=None)

    processing_routine_b = ProcessingRoutine(name="foo2", cpu=2, ram=1, storage_space=1, duration=3, docker_image="bar")
    task_d = ProcessingTask(processing_routine=processing_routine_b, task_id=4, t0=None, depends_on=[1])
    task_e = ProcessingTask(processing_routine=processing_routine_b, task_id=5, t0=None, depends_on=[2])
    task_f = ProcessingTask(processing_routine=processing_routine_b, task_id=6, t0=None, depends_on=[3])

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b,
                                                                                                       task_c, task_d,
                                                                                                       task_e, task_f])

    planning.plan()

    assert planning.attribution_plan is not None

def test_sort_routine_by_dependencies():
    '''
    Scenario:

    - Test of all possible cases of routine sorting by dependency

    Expected behaviour:

    - plan doesn't raise error
    '''

    # Routine list = [a,b,c]
    processing_routine_a = ProcessingRoutine(name="foo", cpu=2, ram=1, storage_space=1, duration=1, docker_image="bar")
    processing_routine_b = ProcessingRoutine(name="bar", cpu=2, ram=1, storage_space=1, duration=3, docker_image="bar")
    processing_routine_c = ProcessingRoutine(name="ker", cpu=2, ram=1, storage_space=1, duration=2, docker_image="bar")

    # routine dependencies : a b c
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=None)

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : a -> b -> c
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=[1])
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=[2])

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : a -> c -> b
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=[3])
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=[1])

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : b -> a -> c
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=[2])
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=[1])

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : b -> c -> a
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=[3])
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=[2])

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : c -> a -> b
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=[3])
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=[1])
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=None)

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : c -> b -> a
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=[2])
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=[3])
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=None)

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : (a,b) -> c
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=[1,2])

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : (a,c) -> b
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=[1,3])
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=None)

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : (b,c) -> a
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=[2,3])
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=None)

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : a, b -> c
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=[2])

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : a, c -> b
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=[3])
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=None)

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : b, a -> c
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=[1])

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : b, c -> a
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=[3])
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=None)

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : c, a -> b
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=None)
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=[1])
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=None)

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()

    # routine dependencies : c, b -> a
    task_a = ProcessingTask(processing_routine=processing_routine_a, task_id=1, t0=None, depends_on=[2])
    task_b = ProcessingTask(processing_routine=processing_routine_b, task_id=2, t0=None, depends_on=None)
    task_c = ProcessingTask(processing_routine=processing_routine_c, task_id=3, t0=None, depends_on=None)

    planning = MatrixScheduler(t_max=20, cpu_max=40, ram_max=40, storage_space_max=40, vm_max=40, task_list=[task_a, task_b, task_c])
    planning.plan()
    assert planning.check_plan()