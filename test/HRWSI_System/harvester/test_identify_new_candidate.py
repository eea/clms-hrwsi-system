"""Tests for identify_new_candidate."""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.harvester.harvester import Harvester
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager

def test_identify_new_candidate_with_some_candidate_in_database(
        mocker,
        get_input_example,
        get_path_input_example):
    '''
    Scenario :

    - We have some candidates who are already in database

    Expected behaviour:

    - These candidates aren't add in database
    '''

    tuple_example_one = get_input_example()
    tuple_example_two = get_input_example()
    path_example_one = get_path_input_example(tuple_example_one)

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_discriminating_column_of_candidate_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = path_example_one
    )

    expected = tuple_example_two
    candidate_tuple = tuple_example_one + tuple_example_two
    actual = Harvester.identify_new_candidate(cursor=(), request=(), candidates_tuple=candidate_tuple, col_index_in_candidate=4)

    assert expected == actual
    assert get_discriminating_column_of_candidate_in_database_mock.assert_called_once

def test_identify_new_candidate_with_all_candidate_in_database(
        mocker,
        get_input_example,
        get_path_input_example):
    '''
    Scenario :

    - All candidates are already in database

    Expected behaviour:

    - No one candidate is add in database
    '''

    tuple_example_one = get_input_example()
    path_example_one = get_path_input_example(tuple_example_one)

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_discriminating_column_of_candidate_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = path_example_one
    )

    expected = ()
    candidate_tuple = tuple_example_one
    actual = Harvester.identify_new_candidate(cursor=(), request=(), candidates_tuple=candidate_tuple, col_index_in_candidate=4)

    assert expected == actual
    assert get_discriminating_column_of_candidate_in_database_mock.assert_called_once

def test_identify_new_candidate_with_zero_candidate(
        mocker,
        get_input_example,
        get_path_input_example):
    '''
    Scenario :

    - We try to add a empty list of candidate

    Expected behaviour:

    - No one candidate is add in database
    - No problem with the function
    '''

    tuple_example_one = get_input_example()
    path_example_one = get_path_input_example(tuple_example_one)

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_discriminating_column_of_candidate_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = path_example_one
    )

    expected = ()
    candidate_tuple = ()
    actual = Harvester.identify_new_candidate(cursor=(), request=(), candidates_tuple=candidate_tuple, col_index_in_candidate=4)

    assert expected == actual
    assert get_discriminating_column_of_candidate_in_database_mock.assert_called_once

def test_identify_new_candidate_with_no_intersect_between_candidate_and_input_in_database(
        mocker,
        get_input_example,
        get_path_input_example):
    '''
    Scenario :

    - We have a list of candidate and input in database but no intersection

    Expected behaviour:

    - All candidates is add in database
    '''

    tuple_exemple_one = get_input_example()
    tuple_example_two = get_input_example()
    path_example_one = get_path_input_example(tuple_exemple_one)

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_discriminating_column_of_candidate_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = path_example_one
    )

    expected = tuple_example_two
    candidate_tuple = tuple_example_two
    actual = Harvester.identify_new_candidate(cursor=(), request=(), candidates_tuple=candidate_tuple, col_index_in_candidate=4)

    assert expected == actual
    assert get_discriminating_column_of_candidate_in_database_mock.assert_called_once

def test_identify_new_candidate_without_candidate_in_database(
        mocker,
        get_input_example):
    '''
    Scenario :

    - The database is empty

    Expected behaviour:

    - All candidates is add in database
    '''

    tuple_example_one = get_input_example()

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_discriminating_column_of_candidate_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = ()
    )

    expected = tuple_example_one
    candidate_tuple = tuple_example_one
    actual = Harvester.identify_new_candidate(cursor=(), request=(), candidates_tuple=candidate_tuple, col_index_in_candidate=4)

    assert expected == actual
    assert get_discriminating_column_of_candidate_in_database_mock.assert_called_once

def test_identify_new_candidate_without_candidate_and_empty_database(
        mocker):
    '''
    Scenario :

    - The database and the candidate list are empty

    Expected behaviour:

    - No changes
    '''

    # Use a mocker to simulate the result of execute_request_in_database function in identify_new_candidate
    get_discriminating_column_of_candidate_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = ()
    )

    expected = ()
    candidate_tuple = ()
    actual = Harvester.identify_new_candidate(cursor=(), request=(), candidates_tuple=candidate_tuple, col_index_in_candidate=4)

    assert expected == actual
    assert get_discriminating_column_of_candidate_in_database_mock.assert_called_once
