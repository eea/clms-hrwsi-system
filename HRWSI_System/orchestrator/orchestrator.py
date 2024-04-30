#!/usr/bin/env python3
"""
Orchestrator module is used to interact between HRWSI Database and Scheduler.
"""
import os
import sys
import datetime
import json
import logging
import time
import asyncio
import nest_asyncio
import psycopg2
import psycopg2.extras
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from utils.logger import LogUtil
from HRWSI_System.launcher.launcher import Launcher
from HRWSI_System.harvester.harvester import Harvester
from HRWSI_System.harvester.apimanager.api_manager import ApiManager
from HRWSI_System.orchestrator.scheduler.matrix_scheduler import MatrixScheduler
from HRWSI_System.orchestrator.processing_task.processing_task import ProcessingTask
from HRWSI_System.orchestrator.processing_routine.processing_routine import ProcessingRoutine
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager

class Orchestrator():
    """Manage interaction between Database objects and Orchestrator objects"""

    LOGGER_LEVEL = logging.DEBUG
    PROCESSING_ROUTINE_REQUEST = "SELECT pc.name AS pc_name, pr.name, pr.cpu, pr.ram, pr.storage_space, pr.duration, pr.docker_image FROM hrwsi.processing_routine pr INNER JOIN hrwsi.processing_condition pc ON pr.name = pc.processing_routine_name"
    ADD_VIRTUAL_MACHINE_REQUEST = "INSERT INTO hrwsi.virtual_machine (id, name, flavour) VALUES (%s, %s, %s)"
    ADD_PROCESSING_TASKS_REQUEST = "INSERT INTO hrwsi.processing_tasks (input_fk_id, virtual_machine_id, creation_date, preceding_input_id, has_ended) VALUES ( %s, %s, %s, %s, %s)"
    PT_ALREADY_IN_DATABASE_REQUEST = "SELECT input_fk_id FROM hrwsi.processing_tasks"
    VM_ALREADY_IN_DATABASE_REQUEST = "SELECT id FROM hrwsi.virtual_machine"
    UNPROCESSED_INPUT_REQUEST =  "SELECT i.id, i.processing_condition_name FROM hrwsi.input i LEFT OUTER JOIN hrwsi.products p ON i.id = p.input_fk_id WHERE i.date>'%s' AND p.id is NULL;"
    UNPROCESSED_INPUT_WITH_ALL_PT_ENDED_REQUEST = "SELECT get_id_of_unprocessed_inputs_with_all_pt_ended FROM hrwsi.get_id_of_unprocessed_inputs_with_all_pt_ended('%s');"
    LISTEN_REQUEST = "LISTEN input_insertion"

    def __init__(self, visualization: bool = False,
                 json_path: str = None,
                 processing_routine_dict: dict = None,
                 processing_task_list: list[ProcessingTask] = None):

        self.visualization = visualization
        self.json_path = json_path
        self.processing_routine_dict = processing_routine_dict
        self.processing_task_list = processing_task_list
        self.logger = LogUtil.get_logger('Log_orchestrator', self.LOGGER_LEVEL, "log_orchestrator/logs.log")

        # Load config file
        config_data = ApiManager.read_config_file()
        deltaday_furthest_date = datetime.timedelta(days=config_data["day_since_creation_of_processing_task"])
        today = datetime.date.today()
        self.furthest_date = (today - deltaday_furthest_date).strftime("%Y-%m-%d")

        self.seconds_before_clear_notification = config_data["orchestrator_waiting_time"]["seconds_before_clear_notification"]

    def extract_orchestrator_processing_task(self, processing_routine_dict: dict) -> None:
        """Collect input from HRWSI Database and create associated processing_task"""

        self.logger.info("Begin extract orchestrator processing task")

        # Connect to Database
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Convert cursor in a dict
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        # Collect HRWSI Database input created in the last days who don't have product (not processed)
        unprocessed_input_request =  self.UNPROCESSED_INPUT_REQUEST % (self.furthest_date)
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, unprocessed_input_request)

        # Create all processing tasks
        self.processing_task_list = [ProcessingTask(processing_routine=processing_routine_dict[result["processing_condition_name"]],
                                            task_id=result["id"],
                                            t0=None,
                                            depends_on=None)
                                    for result in cur]

        # Close connection
        HRWSIDatabaseApiManager.commit_and_close_connection_to_database(conn, cur)

        self.logger.info("End extract orchestrator processing task")

    def extract_orchestrator_processing_routine(self) -> None:
        """Collect processing routine information in Database and create a dict with all the processing_routine objects"""

        self.logger.info("Begin extract orchestrator processing routine")

        # Connect to Database
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Convert cursor in a dict
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        # Collect processing routine in the Database
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.PROCESSING_ROUTINE_REQUEST)

        # Create all orchestrator processing_routine objects
        self.processing_routine_dict = dict((result["pc_name"],
                                        ProcessingRoutine(name=result["name"],
                                                        cpu=result["cpu"],
                                                        ram=result["ram"],
                                                        storage_space=result["storage_space"],
                                                        duration=result["duration"],
                                                        docker_image=result["docker_image"])
                                        ) for result in cur)

        # Close connection
        HRWSIDatabaseApiManager.commit_and_close_connection_to_database(conn, cur)

        self.logger.info("End extract orchestrator processing task")

    def feed_database_with_processing_task(self) -> None:
        """Feed database with Orchestrator's json plan"""

        self.logger.info("Begin feed database with processing task")

        with open(self.json_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)

        # Create virtual_machine
        vm_tuple = tuple((plan_data[worker][0], worker, plan_data[worker][1]) for worker in plan_data)

        # Create task by virtual machine
        now = datetime.datetime.now()
        processing_tasks_tuple = tuple(
            (
                (task_list["task_id"], plan_data[worker][0], now, plan_data[worker][4][i - 1]["task_id"], False)
                if i != 0
                else (task_list["task_id"], plan_data[worker][0], now, None, False)
            )
            for worker in plan_data
            for i, task_list in enumerate(plan_data[worker][4])
        )

        # Connect to Database
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Identify new processing_task
        new_pt_tuple = self.identify_new_processing_task_in_database(cur, processing_tasks_tuple)

        # Identify new VM
        # Keep only the vm associated to new processing_task
        new_vm_tuple = ()
        if new_pt_tuple:
            list_new_vm_id = set([vm_id[1] for vm_id in new_pt_tuple])
            new_vm_tuple = tuple((vm) for vm in vm_tuple if vm[0] in list_new_vm_id)
        # Keep only VM not already in database
        new_vm_tuple = Harvester.identify_new_candidate(cursor=cur, request=self.VM_ALREADY_IN_DATABASE_REQUEST, candidates_tuple=new_vm_tuple, col_index_in_candidate=0)

        # Add vm in HRWSI Database
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.ADD_VIRTUAL_MACHINE_REQUEST, new_vm_tuple)

        # Add processing_task in HRWSI Database
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.ADD_PROCESSING_TASKS_REQUEST, new_pt_tuple)

        # Close connection
        HRWSIDatabaseApiManager.commit_and_close_connection_to_database(conn, cur)

        self.logger.info("End feed database with processing task")

    def identify_new_processing_task_in_database(self, cursor: psycopg2.extensions.cursor, candidates_tuple: tuple[tuple]) -> tuple[tuple]:
        """Verify that a processing task can be created ie:
            - the input has no processing task, or,
            - all the processing task for the input are ended and no one are processed"""

        self.logger.info("Begin identify new processing task in database")

        # All input with processing task created in the last days ended and no processed
        unprocessed_inputs_with_all_pt_ended_request = self.UNPROCESSED_INPUT_WITH_ALL_PT_ENDED_REQUEST % (self.furthest_date)
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cursor, unprocessed_inputs_with_all_pt_ended_request)
        input_with_pt_ended_and_no_processed = [result[0] for result in cur]
        new_processing_task_tuple = tuple(tuples for tuples in candidates_tuple if tuples[0] in input_with_pt_ended_and_no_processed)

        # Add processing task associated with input without processing task
        new_pt_tuple = Harvester.identify_new_candidate(cursor=cur, request=self.PT_ALREADY_IN_DATABASE_REQUEST, candidates_tuple=candidates_tuple, col_index_in_candidate=0)
        if new_pt_tuple:
            new_processing_task_tuple = new_processing_task_tuple + new_pt_tuple

        self.logger.debug("New processing task : %s", new_processing_task_tuple)

        self.logger.info("End identify new processing task in database")

        return new_processing_task_tuple

    def run_scheduling(self) -> None:
        """Run the scheduling"""

        self.logger.info("Begin run scheduling")

        # Create orchestrator's object
        self.extract_orchestrator_processing_routine()
        self.extract_orchestrator_processing_task(processing_routine_dict=self.processing_routine_dict)

        # Load config file
        config_data = ApiManager.read_config_file()

        # Create matrix_scheduler
        planning = MatrixScheduler(t_max=config_data["scheduling"]["t_max"],
                                cpu_max=config_data["scheduling"]["cpu_max"],
                                ram_max=config_data["scheduling"]["ram_max"],
                                storage_space_max=config_data["scheduling"]["storage_space_max"],
                                vm_max=config_data["scheduling"]["vm_max"],
                                task_list=self.processing_task_list,
                                json_path=self.json_path,
                                vm_name_list=config_data["scheduling"]["vm_name_list"],
                                vm_id_list=config_data["scheduling"]["vm_id_list"])

        # Run Scheduler
        planning.check_feasibility()
        planning.plan()
        planning.check_plan()
        if self.visualization:
            planning.visualization()
        planning.export_to_json()

        # Update json_path (usefull if it's None)
        if not self.json_path:
            self.json_path = planning.json_path

        # Convert plan to processing_task
        self.feed_database_with_processing_task()

        self.logger.info("End run scheduling")

    def run(self) -> None:
        """
        Run orchestrator workflow :
        - wait for input insertion notifications
        - plan and create processing tasks
        """

        # Create Listenning loop
        self.create_loop()

    def create_loop(self) -> None:
        """Create a loop to wait and listen notifications"""

        nest_asyncio.apply() # Correct that : by design asyncio does not allow its event loop to be nested

        # Connect to Database
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Listen channel
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.LISTEN_REQUEST)
        conn.commit()

        self.logger.info("Begin create_loop")

        # Wait for notification
        loop = asyncio.get_event_loop()
        loop.add_reader(conn, self.handle_notify, conn)

        # Run the loop
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            # Ended the loop
            loop.close()
            self.logger.info("End create_loop")

    def handle_notify(self, conn) -> None:
        """When a input insertion notification pop, 
        collect inputs, create plan and processing tasks
        and clear notification"""

        self.logger.info("Begin handle_notify : Receive input insertion notification")

        conn.poll()
        for notify in conn.notifies:
            self.logger.debug("Insertion input type : %s", notify.payload)
        time.sleep(self.seconds_before_clear_notification)
        conn.notifies.clear()
        self.run_scheduling()

        self.logger.info("Run Launcher after Orchestrator")
        launcher = Launcher()
        launcher.run()

        self.logger.info("End handle_notify")


if __name__ == "__main__":

    orchestrator = Orchestrator()
    orchestrator.run()
