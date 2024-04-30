#!/usr/bin/env python3
"""
This script creates artificial product for each input
"""
import os
import sys
import datetime
import yaml
import psycopg2
import psycopg2.extras

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from HRWSI_System.harvester.harvester import Harvester
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager

def create_product(product_type: list, process_time: str, start_day_input: int, end_day_input: int):
    """Create product associated to input and add in Database"""

    # Connect to HRWSI database
    conn, cur = HRWSIDatabaseApiManager.connect_to_database()

    # Convert cur in a dict
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    # Collect inputs
    collect_input_request = f"SELECT id, processing_condition_name, date, tile, measurement_day, input_path, mission, input_type FROM hrwsi.input i INNER JOIN hrwsi.processing_condition pc ON i.processing_condition_name = pc.name INNER JOIN hrwsi.processing_routine pr ON pr.name = pc.processing_routine_name WHERE i.measurement_day >= {start_day_input} AND i.measurement_day <= {end_day_input};"
    cur = HRWSIDatabaseApiManager.execute_request_in_database(cur,collect_input_request)

    # Construct product
    product_tuple = construct_product(cur, product_type, process_time)

    # Convert cur in a tuple
    cur = conn.cursor()

    # Identify new products
    candidate_already_in_database_request = f"SELECT input_fk_id FROM hrwsi.products p INNER JOIN hrwsi.input i ON p.input_fk_id = i.id WHERE i.measurement_day >= {start_day_input} AND i.measurement_day <= {end_day_input}"
    new_products_tuple = Harvester.identify_new_candidate(cursor=cur, request=candidate_already_in_database_request, candidates_tuple=product_tuple, col_index_in_candidate=0)

    # Add product
    insert_product_request = "INSERT INTO hrwsi.products (input_fk_id, product_path, creation_date, catalogued_date, kpi_file_path, product_type_id) VALUES ( %s, %s, %s, %s, %s, %s)"
    cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, insert_product_request, new_products_tuple)

    # Close connection
    HRWSIDatabaseApiManager.commit_and_close_connection_to_database(conn, cur)

def construct_product_path(record: dict, procces_time_delta: datetime) -> str:
    """Construct the product path like that :
    - /HRWSI/T09XVJ/L2A/SPM_PC/2024/01/02/S2_L2A_20240102T103529_T09XVJ_20240102T104029.SAFE
    In other words :
    - /HRWSI/tile_name/input_type/processing_condition/year/month/day/S2_input_type_date_tile_name_date.SAFE"""

    processing_condition_name = record["processing_condition_name"]
    date = record["date"]
    tile = record["tile"]
    measurement_day = record["measurement_day"]
    mission = record["mission"]
    input_type = record["input_type"]
    catalogued_date = date + procces_time_delta

    product_path = f"/HRWSI/{tile}/{input_type}/{processing_condition_name}/{str(measurement_day)[:4]}/{str(measurement_day)[4:6]}/{str(measurement_day)[6:8]}/{mission}_{input_type}_{date.strftime('%Y%m%dT%H%M%S')}_{tile}_{catalogued_date.strftime('%Y%m%dT%H%M%S')}.SAFE"

    return product_path

def construct_product(cur: psycopg2.extensions.cursor, product_type: list, process_time: str) -> tuple[tuple]:
    """Construct the product tuple thanks to the inputs"""

    process_time_obj = datetime.datetime.strptime(process_time, '%H:%M:%S')
    procces_time_delta = datetime.timedelta(hours=process_time_obj.hour, minutes=process_time_obj.minute, seconds=process_time_obj.second)

    product_tuple = tuple(
        (
            record["id"],
            construct_product_path(record, procces_time_delta),
            record["date"] + procces_time_delta,
            record["date"] + procces_time_delta,
            " ",
            next((p_type[0] for p_type in product_type
                  if record['processing_condition_name'] == p_type[1]), None)
        )
        for record in cur
        )

    return product_tuple

if __name__ == "__main__":

    # Load config file
    with open('HRWSI_System/harvester/apimanager/artificial_data_for_database/config_create_products.yaml', 'r', encoding="utf-8") as config_file:
        config_data = yaml.safe_load(config_file)

    product_type_list = config_data["product_type"]
    time_to_process = config_data["processing_duration"] # Time to add at input date for products creation_date and catalogue_date
    input_start_day = config_data["start_day_input"]
    input_end_day = config_data["end_day_input"]

    create_product(product_type_list, time_to_process, input_start_day, input_end_day)
