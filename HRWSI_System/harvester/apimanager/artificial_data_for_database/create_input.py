#!/usr/bin/env python3
"""
This script creates artificial inputs personalized from a config file
"""
import os
import sys
import random
from datetime import datetime, timedelta
import yaml

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from HRWSI_System.harvester.harvester import Harvester
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager


def random_date(start_date: str, end_date: str, datetime_format: str) -> datetime:
    """Pull a date randomly between a start date and an end date"""

    # Convert srting in datetime object
    start_date_obj = datetime.strptime(start_date, datetime_format)
    end_date_obj = datetime.strptime(end_date, datetime_format)

    # Calculate the difference in seconds between the two dates
    seconds_difference = int((end_date_obj - start_date_obj).total_seconds())

    # Generate a random number of seconds in this difference
    random_seconds = random.randint(0, seconds_difference)

    # Add this number to start_date
    random_date_obj = start_date_obj + timedelta(seconds=random_seconds)

    return random_date_obj

def date_string_to_measurement_day(date_string: str) -> int:
    """Transform a date_string in the format: Year-Month-Day in an integer: YearMonthDay"""

    return int(date_string[:4]+date_string[5:7]+date_string[8:10])

def construct_input_data(tile_list: list[str],
                         input_type: str,
                         processing_condition: str,
                         start_date: str,
                         end_date: str,
                         datetime_format:str, mission: str) -> tuple[str, str, datetime, int]:
    """This function construct the input_path of an input and return usefull data to create input (tile name, creation date and measurement day).
    The path is construct to look like this :
    - /HRWSI/T10XET/MSIL1C/GRS_PC/2024/01/10/S2_MSIL1C_20240110T085402_T10XET_20240110T085402.SAFE
    In other words : 
    - /HRWSI/tile_name/input_type/processing_condition/year/month/day/S2_input_type_date_tile_name_date.SAFE"""

    tile_name = tile_list[random.randint(0, len(tile_list)-1)]
    date = random_date(start_date, end_date, datetime_format)
    measurement_day = int(date.strftime("%Y%m%d"))

    input_path = f"/HRWSI/{tile_name}/{input_type}/{processing_condition}/{str(measurement_day)[:4]}/{str(measurement_day)[4:6]}/{str(measurement_day)[6:8]}/{mission}_{input_type}_{date.strftime('%Y%m%dT%H%M%S')}_{tile_name}_{date.strftime('%Y%m%dT%H%M%S')}.SAFE"

    return input_path, tile_name, date, measurement_day

def create_input(start_date: str,
                 end_date: str,
                 tile_list: list[str],
                 input_description: dict,
                 datetime_format: str) -> None:
    """Create input with : 
    - a tile list, 
    - a input description which contains the input type, the processing condition, the mission and the number of input who want to create,
    - a start date and a end date because the creation date of the input will be selected randomly between its 2 dates.
    Input are then add in Database"""

    # Construct tuple of input
    input_tuple = tuple(
        (
            pc["processing_condition"],
            date,
            tile,
            measurement_day,
            input_path,
            pc["mission"]
        )
        for inputs in input_description
        for pc in inputs["pc"]
        for _ in range(pc["nb_input"])
        for input_path, tile, date, measurement_day in
        [construct_input_data(tile_list, inputs["input_type"],
                              pc["processing_condition"],
                              start_date,
                              end_date,
                              datetime_format,
                              pc["mission"])]
    )

    # Connect to HRWSI database
    conn, cur = HRWSIDatabaseApiManager.connect_to_database()

    # Identify new input
    start_measurement_day = date_string_to_measurement_day(start_date)
    end_measurement_day = date_string_to_measurement_day(end_date)
    candidate_already_in_database_request = f"SELECT input_path FROM hrwsi.input i WHERE i.measurement_day >= {start_measurement_day} and i.measurement_day <= {end_measurement_day};"
    new_input_tuple = Harvester.identify_new_candidate(cursor=cur, request=candidate_already_in_database_request, candidates_tuple=input_tuple, col_index_in_candidate=4)

    # Add input
    insert_input_request = "INSERT INTO hrwsi.input (processing_condition_name, date, tile, measurement_day, input_path, mission) VALUES ( %s, %s, %s, %s, %s, %s)"
    cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, insert_input_request, new_input_tuple)

    # Close connection
    HRWSIDatabaseApiManager.commit_and_close_connection_to_database(conn, cur)

if __name__ == "__main__":

    # Load config file
    with open('HRWSI_System/harvester/apimanager/artificial_data_for_database/config_create_input.yaml', 'r', encoding="utf-8") as config_file:
        config_data = yaml.safe_load(config_file)

    tiles_list = config_data["tile_list"]
    date_to_start = config_data["start_date"]
    date_to_end = config_data["end_date"]
    inputs_description = config_data["input_description"]
    format_of_datetime = '%Y-%m-%d %H:%M:%S'

    create_input(start_date=date_to_start, end_date=date_to_end, tile_list=tiles_list, input_description=inputs_description, datetime_format=format_of_datetime)
