"""Tests for identify_new_processing_task_in_database."""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.harvester.harvester import Harvester
from HRWSI_System.orchestrator.orchestrator import Orchestrator
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager

def test_identify_new_pt_with_all_task_to_add_are_from_input_with_other_pt(
        mocker,
        get_processing_task_example,
        get_input_id_form_processing_task_example):
    '''
    Scenario :

    - All processing task candidate are for input who doesn't already have processing task processed

    Expected behaviour:

    - All processing tasks are add
    '''

    tuple_example_one = get_processing_task_example()
    input_id_example_one = get_input_id_form_processing_task_example(tuple_example_one)

    # Use a mocker to simulate the result of identify_new_candidate function in identify_new_processing_task_in_database
    get_pt_tuple_with_input_without_pt = mocker.patch.object(
        Harvester,
        'identify_new_candidate',
        return_value = ()
    )

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_input_id_of_candidate_to_add = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = input_id_example_one
    )

    expected = tuple_example_one
    candidate_tuple = tuple_example_one
    orchestrator = Orchestrator()
    actual = orchestrator.identify_new_processing_task_in_database(cursor=(), candidates_tuple=candidate_tuple)

    assert expected == actual
    assert get_pt_tuple_with_input_without_pt.assert_called_once
    assert get_input_id_of_candidate_to_add.assert_called_once

def test_identify_new_pt_with_some_task_to_add_are_from_input_with_other_pt(
        mocker,
        get_processing_task_example,
        get_input_id_form_processing_task_example):
    '''
    Scenario :

    - Some processing task candidate are for input who doesn't already have processing task processed

    Expected behaviour:

    - These processing tasks are add
    '''

    tuple_example_one = get_processing_task_example()
    tuple_example_two = get_processing_task_example()
    input_id_example_one = get_input_id_form_processing_task_example(tuple_example_one)

    # Use a mocker to simulate the result of identify_new_candidate function in identify_new_processing_task_in_database
    get_pt_tuple_with_input_without_pt = mocker.patch.object(
        Harvester,
        'identify_new_candidate',
        return_value = ()
    )

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_input_id_of_candidate_to_add = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = input_id_example_one
    )

    expected = tuple_example_one
    candidate_tuple = tuple_example_one + tuple_example_two
    orchestrator = Orchestrator()
    actual = orchestrator.identify_new_processing_task_in_database(cursor=(), candidates_tuple=candidate_tuple)

    assert expected == actual
    assert get_pt_tuple_with_input_without_pt.assert_called_once
    assert get_input_id_of_candidate_to_add.assert_called_once

def test_identify_new_pt_without_task_to_add_are_from_input_with_other_pt(
        mocker,
        get_processing_task_example):
    '''
    Scenario :

    - We don't have processing task candidate from input who doesn't already have processing task processed

    Expected behaviour:

    - No one candidate is add in database
    '''

    tuple_example_one = get_processing_task_example()
    tuple_example_two = get_processing_task_example()

    # Use a mocker to simulate the result of identify_new_candidate function in identify_new_processing_task_in_database
    get_pt_tuple_with_input_without_pt = mocker.patch.object(
        Harvester,
        'identify_new_candidate',
        return_value = ()
    )

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_input_id_of_candidate_to_add = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = ()
    )

    expected = ()
    candidate_tuple = tuple_example_one + tuple_example_two
    orchestrator = Orchestrator()
    actual = orchestrator.identify_new_processing_task_in_database(cursor=(), candidates_tuple=candidate_tuple)

    assert expected == actual
    assert get_pt_tuple_with_input_without_pt.assert_called_once
    assert get_input_id_of_candidate_to_add.assert_called_once

def test_identify_new_pt_with_all_task_to_add_are_from_input_without_other_pt(
        mocker,
        get_processing_task_example):
    '''
    Scenario :

    - All processing task candidate are from input without other processing task

    Expected behaviour:

    - All candidates are add in database
    '''

    tuple_example_one = get_processing_task_example()
    tuple_example_two = get_processing_task_example()

    # Use a mocker to simulate the result of identify_new_candidate function in identify_new_processing_task_in_database
    get_pt_tuple_with_input_without_pt = mocker.patch.object(
        Harvester,
        'identify_new_candidate',
        return_value = tuple_example_one + tuple_example_two
    )

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_input_id_of_candidate_to_add = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = ()
    )

    expected = tuple_example_one + tuple_example_two
    candidate_tuple = tuple_example_one + tuple_example_two
    orchestrator = Orchestrator()
    actual = orchestrator.identify_new_processing_task_in_database(cursor=(), candidates_tuple=candidate_tuple)

    assert expected == actual
    assert get_pt_tuple_with_input_without_pt.assert_called_once
    assert get_input_id_of_candidate_to_add.assert_called_once

def test_identify_new_pt_with_some_task_to_add_are_from_input_without_other_pt(
        mocker,
        get_processing_task_example):
    '''
    Scenario :

    - Some processing task candidate are from input without other processing task

    Expected behaviour:

    - These candidates are add in database
    '''

    tuple_example_one = get_processing_task_example()
    tuple_example_two = get_processing_task_example()

    # Use a mocker to simulate the result of identify_new_candidate function in identify_new_processing_task_in_database
    get_pt_tuple_with_input_without_pt = mocker.patch.object(
        Harvester,
        'identify_new_candidate',
        return_value = tuple_example_one
    )

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_input_id_of_candidate_to_add = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = ()
    )

    expected = tuple_example_one
    candidate_tuple = tuple_example_one + tuple_example_two
    orchestrator = Orchestrator()
    actual = orchestrator.identify_new_processing_task_in_database(cursor=(), candidates_tuple=candidate_tuple)

    assert expected == actual
    assert get_pt_tuple_with_input_without_pt.assert_called_once
    assert get_input_id_of_candidate_to_add.assert_called_once

def test_identify_new_pt_with_some_task_to_add_are_from_input_without_other_pt_and_some_from_input_with_other_pt(
        mocker,
        get_processing_task_example):
    '''
    Scenario :

    - Some processing task candidate are from input without other processing task and some from input with other processing task

    Expected behaviour:

    - These candidates are add in database
    '''

    tuple_example_one = get_processing_task_example()
    tuple_example_two = get_processing_task_example()

    # Use a mocker to simulate the result of identify_new_candidate function in identify_new_processing_task_in_database
    get_pt_tuple_with_input_without_pt = mocker.patch.object(
        Harvester,
        'identify_new_candidate',
        return_value = tuple_example_two
    )

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_input_id_of_candidate_to_add = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = tuple_example_one
    )

    expected = tuple_example_one + tuple_example_two
    candidate_tuple = tuple_example_one + tuple_example_two
    orchestrator = Orchestrator()
    actual = orchestrator.identify_new_processing_task_in_database(cursor=(), candidates_tuple=candidate_tuple)

    assert expected == actual
    assert get_pt_tuple_with_input_without_pt.assert_called_once
    assert get_input_id_of_candidate_to_add.assert_called_once

def test_identify_new_pt_without_candidate(
        mocker):
    '''
    Scenario :

    - There arn't candidate 

    Expected behaviour:

    - No one candidate is add in database
    - No problem with the function
    '''

    # Use a mocker to simulate the result of identify_new_candidate function in identify_new_processing_task_in_database
    get_pt_tuple_with_input_without_pt = mocker.patch.object(
        Harvester,
        'identify_new_candidate',
        return_value = ()
    )

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_input_id_of_candidate_to_add = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = ()
    )

    expected = ()
    candidate_tuple = ()
    orchestrator = Orchestrator()
    actual = orchestrator.identify_new_processing_task_in_database(cursor=(), candidates_tuple=candidate_tuple)

    assert expected == actual
    assert get_pt_tuple_with_input_without_pt.assert_called_once
    assert get_input_id_of_candidate_to_add.assert_called_once
