#!/usr/bin/env python3
"""
HRWSI_database_api_manager module implements the method to interact with HRWSI Database to extract candidate inputs.
"""
import sys
import os
import datetime
import psycopg2
import psycopg2.extras

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from HRWSI_System.harvester.apimanager.api_manager import ApiManager

class HRWSIDatabaseApiManager(ApiManager):
    """Interact with HRWSI Database"""

    PRODUCT_TYPE_ID_WHO_CAN_CREATE_INPUT_REQUEST = 'SELECT DISTINCT pt.id AS product_type_id FROM hrwsi.product_type pt LEFT JOIN hrwsi.processing_routine pr ON pr.input_type=pt.data_type WHERE pr.input_type is NOT NULL;'
    COLLECT_PRODUCTS_THAT_BECOME_INPUTS_REQUEST = "SELECT product_path, creation_date, tile, measurement_day, mission FROM hrwsi.products p INNER JOIN hrwsi.input i ON i.id = p.input_fk_id WHERE p.creation_date >= '%s' AND p.product_type_id IN %s;"

    def get_candidate_inputs(self) -> tuple[tuple]:

        self.logger.info("Begin get_candidate_inputs for HRWSI Database")

        # Connect to Dtabase
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Today
        today = datetime.date.today()

        # Creation_date interval
        limit_creation_date = datetime.timedelta(days=self.max_day_since_publication_date)
        begin_creation_date = today - limit_creation_date

        # Convert cur in a dict
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        # Collect code of product_type who can create input
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.PRODUCT_TYPE_ID_WHO_CAN_CREATE_INPUT_REQUEST)
        product_type_id = tuple(result["product_type_id"] for result in cur)
        product_type_id = '(' + str(product_type_id[0]) + ')' if len(product_type_id)==1 else product_type_id
        self.logger.debug("Product_type_id : %s", product_type_id)

        # Collects products created in the last 7 days and that can create inputs
        collect_products_that_become_inputs_request = self.COLLECT_PRODUCTS_THAT_BECOME_INPUTS_REQUEST % (begin_creation_date, product_type_id)
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, collect_products_that_become_inputs_request)

        # Create input tuple
        candidate_input_tuple = ()
        candidate_input_tuple = self.create_input_tuple(cur, candidate_input_tuple)

        # Close connection
        HRWSIDatabaseApiManager.commit_and_close_connection_to_database(conn, cur)

        self.logger.info("End get_candidate_inputs for HRWSI Database")

        return candidate_input_tuple

    def create_input_tuple(self, cur: psycopg2.extensions.cursor, candidate_input_tuple: tuple[tuple]) -> tuple[tuple]:
        """Create tuple of input thanks to the request result"""

        self.logger.info("Begin create_input_tuple for HRWSI Database")

        # Create input tuple
        candidate_input_tuple = tuple(
            (
                self.processing_condition_name,
                result['creation_date'],
                result['tile'],
                result['measurement_day'],
                result['product_path'],
                result['mission']
            )
            for result in cur)

        self.logger.info("End create_input_tuple for HRWSI Database")

        return candidate_input_tuple

    @staticmethod
    def connect_to_database() -> tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
        """ Function to enable connection to HRWSI Database"""

        # Load config file
        config_data = ApiManager.read_config_file()

        dbname = config_data["database"]["dbname"]
        user = config_data["database"]["user"]
        password = config_data["database"]["password"]
        host = config_data["database"]["host"]
        port = config_data["database"]["port"]

        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)

        # Open a cursor to perform database operations
        cur = conn.cursor()

        return conn, cur

    @staticmethod
    def commit_and_close_connection_to_database(conn: psycopg2.extensions.connection, cur: psycopg2.extensions.cursor) -> None:
        """Commit the changes and close the connection with the database"""

        # Make the changes to the database persistent
        conn.commit()

        # Close communication with the database
        cur.close()
        conn.close()

    @staticmethod
    def execute_request_in_database(cur: psycopg2.extensions.cursor, request: str, data_tuple: tuple[tuple]=None) -> psycopg2.extensions.cursor:
        """Execute a request in HRWSI Database"""
        # If we want to insert (maybe many row) in database
        if data_tuple is not None :
            psycopg2.extras.execute_batch(cur, request, data_tuple)
        # Execute other request
        else:
            cur.execute(request)
        return cur
