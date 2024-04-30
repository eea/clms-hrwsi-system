#!/usr/bin/env python3
"""
Harvester module is used to extract candidate input, indentify new input and update database.
"""
import os
import sys
import logging
import datetime
import time
import asyncio
import nest_asyncio
import psycopg2
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from utils.logger import LogUtil
from HRWSI_System.harvester.apimanager.api_manager import ApiManager
from HRWSI_System.harvester.apimanager.wekeo_api_manager import WekeoApiManager
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager


class Harvester():
    """Define a harvester"""

    LOGGER_LEVEL = logging.DEBUG
    INSERT_CANDIDATE_REQUEST = "INSERT INTO hrwsi.input (processing_condition_name, date, tile, measurement_day, input_path, mission) VALUES ( %s, %s, %s, %s, %s, %s)"
    LISTEN_REQUEST = "LISTEN processing_tasks_state_processed"
    PRODUCT_DATA_TYPE_OF_RUNNING_PROCESSING_TASKS_REQUEST = 'SELECT get_product_data_type_of_processing_tasks_not_ended FROM hrwsi.get_product_data_type_of_processing_tasks_not_ended();'
    INPUT_TYPE_LIST_REQUEST = 'SELECT DISTINCT input_type FROM hrwsi.processing_routine;'
    CANDIDATE_ALREADY_IN_DATABASE_REQUEST = "SELECT input_path FROM hrwsi.input i WHERE i.measurement_day>=%s;"
    PROCESSING_TASK_UNPROCESSED_REQUEST = "SELECT count(task_id) FROM (SELECT pt.input_fk_id AS task_id FROM hrwsi.processing_tasks pt WHERE pt.creation_date>'%s') AS x, hrwsi.is_one_processing_task_processed_for_an_input(task_id) WHERE is_one_processing_task_processed_for_an_input=false;"

    def __init__(self, request_list:list[ApiManager] = None):

        self.request_list = request_list
        self.logger = LogUtil.get_logger('Log_harvester', self.LOGGER_LEVEL, "log_harvester/logs.log")
        self.last_notification_time = None

        # Load config file
        config_data = ApiManager.read_config_file()

        self.delta_time_notification_max = datetime.timedelta(seconds=config_data["harvester_waiting_time"]["delta_seconds_max_between_notifications"])
        self.nb_of_second_between_each_notify_verification = config_data["harvester_waiting_time"]["nb_of_second_between_each_notify_verification"]
        self.day_since_creation_of_processing_task = config_data["day_since_creation_of_processing_task"]
        self.sleep_time_before_harvest_product = config_data["harvester_waiting_time"]["sleep_time_before_harvest_product"]
        self.sleep_time_to_wait_scheduling = config_data["harvester_waiting_time"]["sleep_time_to_wait_scheduling"]

        self.input_type_list = None

    def harvest_input(self) -> None:
        """Find candidate input, identify new input and add in database"""

        self.logger.info("Begin harvest input")

        all_candidates_tuple = ()
        deltaday_furthest_date = 0
        for request in self.request_list:
            # Find candidate input
            all_candidates_tuple += request.get_candidate_inputs()
            # Calculate the furthest date of candidate
            if request.max_day_since_measurement_date and deltaday_furthest_date < request.max_day_since_measurement_date:
                deltaday_furthest_date = request.max_day_since_measurement_date
            elif deltaday_furthest_date < request.max_day_since_publication_date:
                deltaday_furthest_date = request.max_day_since_publication_date

        self.logger.debug("Deltaday furthest date : %s", deltaday_furthest_date)

        # Connect to HRWSI. database
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Identify new candidate
        self.logger.info("Begin identify_new_candidate")

        deltaday_furthest_date = datetime.timedelta(days=deltaday_furthest_date)
        today = datetime.date.today()
        furthest_date = (today - deltaday_furthest_date).strftime("%Y%m%d")
        self.logger.debug("Furthest_date : %s", furthest_date)

        candidate_already_in_database_request = self.CANDIDATE_ALREADY_IN_DATABASE_REQUEST % (furthest_date)
        new_input_tuple = Harvester.identify_new_candidate(cur, candidate_already_in_database_request, all_candidates_tuple, 4)
        self.logger.info("End identify_new_candidate")

        self.logger.debug("New input tuple : %s", new_input_tuple)

        # Add new input in database
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.INSERT_CANDIDATE_REQUEST, new_input_tuple)

        # Close connection
        HRWSIDatabaseApiManager.commit_and_close_connection_to_database(conn, cur)

        self.logger.info("End harvest input")

    def run(self) -> None:
        """
        Run harvester workflow
        """

        # Load config file
        config_data = ApiManager.read_config_file()

        # Create request_list for wekeo
        self.request_list = [
            WekeoApiManager(processing_condition_name=pc["processing_condition_name"],
                            input_type=pc["input_type"],
                            max_day_since_publication_date=pc["max_day_since_publication_date"],
                            max_day_since_measurement_date=pc["max_day_since_measurement_date"],
                            tile_list_file=pc["tile_list_file"] if "tile_list_file" in pc else None,
                            geometry_file=pc["geometry_file"] if "geometry_file" in pc else None)
            for pc in config_data["wekeo_api_manager"]]

        # Collect input data on Wekeo API
        self.harvest_input()

        # Create request_list for HRWSI_Database
        self.request_list = [
            HRWSIDatabaseApiManager(processing_condition_name=pc["processing_condition_name"],
                            max_day_since_publication_date=pc["max_day_since_publication_date"])
            for pc in config_data["hrwsi_database_api_manager"]]

        # Connect to Database
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Convert cur in a dict
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        # Collect list of input type in Database
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.INPUT_TYPE_LIST_REQUEST)
        self.input_type_list = [result["input_type"] for result in cur]
        self.logger.debug("Input type list %s", self.input_type_list)

        # Close connection
        HRWSIDatabaseApiManager.commit_and_close_connection_to_database(conn, cur)

        # Initialize last_notification_time
        self.last_notification_time = datetime.datetime.now()

        # Create Listenning loop
        self.create_loop()

    def create_loop(self) -> None:
        """Create a loop to wait and listen notifications"""

        nest_asyncio.apply() # Correct that : by design asyncio does not allow its event loop to be nested

        # Connect to Database
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Convert cur in a dict
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        # Listen channel
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.LISTEN_REQUEST)
        conn.commit()

        self.logger.info("Begin create_loop")

        # Wait for notification
        loop = asyncio.get_event_loop()
        loop.add_reader(conn, self.handle_notify, conn, cur)

        # Add task to verify the last notification date
        task = loop.create_task(self.verify_notification_time(conn, cur, loop))

        # Run the loop
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            # Cancel task
            task.cancel()
            loop.run_until_complete(loop.shutdown_asyncgens())
            # Ended the loop
            loop.close()
            self.logger.info("End create_loop")

    async def verify_notification_time(self, conn: psycopg2.extensions.connection, cur: psycopg2.extensions.cursor, loop: asyncio.AbstractEventLoop) -> None:
        """Verify the last notification time each nb_of_second_between_each_notify_verification seconds"""

        await asyncio.sleep(self.sleep_time_to_wait_scheduling) # Wait the end of scheduling

        # While processing task running and create product who can create new input
        while self.check_running_processing_tasks_product_can_create_input(cur):
            conn.commit()
            await asyncio.sleep(self.nb_of_second_between_each_notify_verification)
            self.logger.info("Time before last notification : %s", datetime.datetime.now() - self.last_notification_time)

            # If waiting notification for too long, harvest input
            if datetime.datetime.now() - self.last_notification_time > self.delta_time_notification_max:
                self.logger.info("Time before last notification is too long : Creation of L2A products input")
                self.last_notification_time = datetime.datetime.now()
                self.harvest_input()

        # Stop the loop
        loop.stop()

    def handle_notify(self, conn: psycopg2.extensions.connection, cur: psycopg2.extensions.cursor) -> None:
        """When a processing task processed notification pop, 
        if all processing task are processed,
        create input for all L2A products and clear notification"""

        self.logger.info("Begin handle_notify : Receive processing task processed notification")

        conn.poll()
        self.last_notification_time = datetime.datetime.now()
        for notify in conn.notifies:
            self.logger.debug("Payload : %s", notify.payload)
        conn.notifies.clear()

        # If all processing tasks created is the last days have one processed job, create input from L2A product
        deltaday_furthest_date_pt = datetime.timedelta(days=self.day_since_creation_of_processing_task)
        today = datetime.date.today()
        furthest_date_pt = (today - deltaday_furthest_date_pt).strftime("%Y-%m-%d")
        self.logger.debug("Furthest_date_pt : %s", furthest_date_pt)

        processing_task_unprocessed_request = self.PROCESSING_TASK_UNPROCESSED_REQUEST % (furthest_date_pt)
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, processing_task_unprocessed_request)
        conn.commit()
        nb_task_unprocessed = [int(result["count"]) for result in cur]
        self.logger.debug("Nb task unprocessed : %s", nb_task_unprocessed[0])

        if not nb_task_unprocessed[0]:
            self.logger.debug("All tasks are processed")
            time.sleep(self.sleep_time_before_harvest_product) # add sleep to have time to close launcher ?
            self.harvest_input()

        self.logger.info("End handle_notify")

    def check_running_processing_tasks_product_can_create_input(self, cur: psycopg2.extensions.cursor) -> bool:
        """True if current product_data_type of processing routine 
        of running processing tasks can create input"""

        self.logger.info("Begin check_running_processing_tasks_product_can_create_input")

        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.PRODUCT_DATA_TYPE_OF_RUNNING_PROCESSING_TASKS_REQUEST)
        product_data_type_list = [result["get_product_data_type_of_processing_tasks_not_ended"] for result in cur]
        self.logger.debug("List of product data type of running processing tasks : %s", product_data_type_list)

        # If each product in product data type list are not in input_type_list or
        # there aren't product data type (all processing task has ended)
        # then new input can't be created
        if (not any(item in product_data_type_list for item in self.input_type_list)) or product_data_type_list==[]:
            self.logger.debug("Running processing tasks product can't create input")
            return False

        self.logger.info("End check_running_processing_tasks_product_can_create_input")
        return True

    @staticmethod
    def identify_new_candidate(cursor: psycopg2.extensions.cursor, request: str, candidates_tuple: tuple[tuple], col_index_in_candidate: int) -> tuple[tuple]:
        """Verify that tuple are not already in input table and return only new input tuple"""

        cur = HRWSIDatabaseApiManager.execute_request_in_database(cursor, request)
        candidate_in_database = [result[0] for result in cur]
        new_tuple = tuple(tuples for tuples in candidates_tuple if tuples[col_index_in_candidate] not in candidate_in_database)

        return new_tuple


if __name__ == "__main__":

    har = Harvester()
    har.run()
