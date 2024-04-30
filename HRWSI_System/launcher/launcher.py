#!/usr/bin/env python3
"""
Launcher module is used to create and associate Nomad job to each processing task.
"""
import os
import sys
import logging
import datetime
import subprocess
import asyncio
import nest_asyncio
import psycopg2
import psycopg2.extras
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from utils.logger import LogUtil
from HRWSI_System.harvester.apimanager.api_manager import ApiManager
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager

class Launcher():
    """Launch processing task execution"""

    LOGGER_LEVEL = logging.DEBUG
    PROCESSING_TASKS_READY_TO_LAUNCH_REQUEST = 'SELECT id, input_fk_id, virtual_machine_id, creation_date, preceding_input_id, nomad_job_id, has_ended, intermediate_files_path FROM hrwsi.processing_tasks pt, hrwsi.get_ids_of_processing_tasks_ready_to_be_launched() WHERE pt.id=get_ids_of_processing_tasks_ready_to_be_launched;'
    NB_OF_PROCESSING_TASKS_NOT_FINISHED_REQUEST = 'SELECT count(id) FROM hrwsi.get_processing_tasks_not_finished();'
    INSERT_NOMAD_JOB_REQUEST = "INSERT INTO hrwsi.nomad_job_dispatch (processing_task_fk_id, nomad_job_dispatch, dispatch_date, log_path) VALUES (%s, %s, %s, %s)"
    INSERT_PROCESSING_STATUS_REQUEST = "INSERT INTO hrwsi.processing_status_workflow (nomad_job_dispatch_fk_id, processing_status_id, date) VALUES (%s, %s, %s)"
    NOMAD_JOB_WITHOUT_PROCESSING_STATUS_REQUEST = "SELECT njd.id FROM hrwsi.nomad_job_dispatch njd LEFT JOIN hrwsi.processing_status_workflow psw ON psw.nomad_job_dispatch_fk_id=njd.id WHERE psw.id is NULL;"
    HCL_INFO_REQUEST = "SELECT pr.docker_image, subquery.name, subquery.pt_id, subquery.nomad_id FROM hrwsi.processing_routine pr INNER JOIN hrwsi.processing_condition pc ON pr.name = pc.processing_routine_name INNER JOIN hrwsi.input i ON i.processing_condition_name = pc.name INNER JOIN ( SELECT pt.input_fk_id, vm.name, pt.id AS pt_id, njd.id AS nomad_id FROM hrwsi.processing_tasks pt INNER JOIN hrwsi.virtual_machine vm ON pt.virtual_machine_id = vm.id INNER JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id WHERE pt.id IN (%s) ) subquery ON subquery.input_fk_id = i.id;"
    LISTEN_REQUEST = "LISTEN input_insertion"

    def __init__(self):

        # Load config file
        config_data = ApiManager.read_config_file()

        self.waiting_seconds = config_data["launcher_waiting_time"]["waiting_seconds"]
        self.logger = LogUtil.get_logger('Log_launcher', self.LOGGER_LEVEL, "log_launcher/logs.log")
        self.new_input = False

    def run(self) -> None:
        """
        Run launcher workflow :
        - wait m minutes
        - collect processing tasks without Nomad job and with preceding task ended or null
        - create and associate Nomad job
        """

        # Create waiting loop
        self.create_loop()

    def create_loop(self) -> None:
        """Create a loop to wait"""

        nest_asyncio.apply() # Correct that : by design asyncio does not allow its event loop to be nested

        # Connect to Database
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Listen channel
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.LISTEN_REQUEST)
        conn.commit()

        # Convert cur in a dict
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        self.logger.info("Begin create_loop")

        # Wait for notification
        loop = asyncio.get_event_loop()
        loop.add_reader(conn, self.handle_notify, conn)

        # Add task to execute workflow each m minutes
        task = loop.create_task(self.waiting(cur, loop, conn))

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
            self.logger.info("End create_loop")

    def handle_notify(self, conn) -> None:
        """When a input insertion notification pop, 
        pretty exit the loop"""

        self.logger.info("Begin handle_notify : Receive input insertion notification")

        conn.poll()
        for notify in conn.notifies:
            self.logger.debug("Insertion input type : %s", notify.payload)

        self.new_input = True

        self.logger.info("End handle_notify")

    async def waiting(self, cur: psycopg2.extensions.cursor, loop: asyncio.AbstractEventLoop, conn: psycopg2.extensions.connection) -> None:
        """Collect processing tasks without Nomad job and with preceding task processed or null"""

        # While all processing tasks hasn't ended and there is no new input in database
        while self.check_all_processing_tasks_has_not_ended(cur) and not self.new_input:

            # Collect processing tasks ready to lauch
            self.logger.info("Collect processing tasks")
            cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.PROCESSING_TASKS_READY_TO_LAUNCH_REQUEST)

            # Create Nomad_job_dispatch
            self.create_nomad_job(cur, conn)

            # Create processing status workflow for new Nomad job dispatch
            self.create_processing_status_workflow_for_new_nomad_job(cur, conn)

            await asyncio.sleep(self.waiting_seconds)

        # Stop the loop
        loop.stop()

    def create_nomad_job(self, cur: psycopg2.extensions.cursor, conn: psycopg2.extensions.connection) -> None:
        """Create nomad job dispatch of processing tasks and add in Database"""

        self.logger.info("Begin create Nomad job dispatch")
        nomad_job_tuples = tuple(
        (
            record["id"],
            " ",
            datetime.datetime.now(),
            "/log/path" #TODO change path
        )
        for record in cur
        )
        self.logger.debug("Nomad job dispatch tuple : %s", nomad_job_tuples)

        # Add in Database
        # TODO change nomad_job_id in processing_tasks ?
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.INSERT_NOMAD_JOB_REQUEST, nomad_job_tuples)
        conn.commit()

        # Create hcl file to nomad only new nomad job are created
        nomad_job_pt_id = [nomad_job[0] for nomad_job in nomad_job_tuples]
        # Collect worker and docker image of routine for each new nomad job dispatch
        for nomad_job_pt in nomad_job_pt_id:
            self.logger.debug("Nomad job pt id : %s", nomad_job_pt)
            hcl_info_request = self.HCL_INFO_REQUEST % (str(nomad_job_pt))
            self.logger.debug("hcl_info_request : %s", hcl_info_request)
            cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, hcl_info_request)

            for result in cur :
                # Create hcl file for each pt
                pt_id = result["pt_id"]
                file_path = f"nomad_job/pt_id_{pt_id}.hcl"
                now = datetime.datetime.now()
                (product_path, input_id, product_type_id, input_path) = Launcher.construct_product_path(cur, conn, pt_id, now)
                # TODO change to docker_image=result["docker_image"], yaml_path
                self.create_hcl_file(file_path=file_path, worker_name=result["name"],
                                    docker_image="redacted/eea_hr-wsi/nrt_production_system/testimage",
                                    yaml_path="/home/eouser/delay/delay.yaml",
                                    processing_task_id=str(pt_id),
                                    nomad_job_id =str(result["nomad_id"]),
                                    product_path = product_path,
                                    input_id = input_id,
                                    product_type_id = product_type_id,
                                    input_path = input_path)
                print(result["docker_image"])

                # Run hcl file
                self.execute_nomad_job(file_path)

                # Delete hcl file
                self.delete_hcl_file(file_path)

        self.logger.info("End create Nomad job dispatch")

    def create_processing_status_workflow_for_new_nomad_job(self, cur: psycopg2.extensions.cursor, conn: psycopg2.extensions.connection) -> None:
        """Collect Nomad job without Processing status workflow and create them"""

        self.logger.info("Begin create Processing status workflow")

        # Collect Nomad job without Processing status workflow
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.NOMAD_JOB_WITHOUT_PROCESSING_STATUS_REQUEST)

        # Create corresponding Processing status workflow
        status = 1 # started

        processing_status_tuples = tuple(
        (
            record["id"],
            status,
            datetime.datetime.now()
        )
        for record in cur
        )
        self.logger.debug("Processing status workflow tuple : %s", processing_status_tuples)

        # Add in Database
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.INSERT_PROCESSING_STATUS_REQUEST, processing_status_tuples)
        conn.commit()

        self.logger.info("End create Processing status workflow")

    def check_all_processing_tasks_has_not_ended(self, cur: psycopg2.extensions.cursor) -> bool:
        """True if all processing tasks has not ended
        False otherwise"""

        self.logger.info("Begin check_all_processing_tasks_has_not_ended")

        # Collect the number of processing tasks not finished
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.NB_OF_PROCESSING_TASKS_NOT_FINISHED_REQUEST)
        nb_task_not_finished = [int(result["count"]) for result in cur]
        self.logger.debug("Nb task not finished : %s", nb_task_not_finished[0])

        # All processing task are finished
        if not nb_task_not_finished[0]:
            self.logger.debug("All processing tasks has ended")
            return False

        self.logger.info("End check_all_processing_tasks_has_not_ended")
        return True

    def create_hcl_file(self, file_path: str, worker_name: str, docker_image: str, yaml_path: str, processing_task_id: str, nomad_job_id: str, product_path: str, input_id: str, product_type_id: str, input_path: str) -> None:
        """Create the content of nomad job"""

        self.logger.info("Begin create hcl file")
        content = '''
        job "processing_task_name" {
        type = "batch"
        group "processing_task_name" {
            # Constraint on worker name
            constraint {
            attribute = "${attr.unique.hostname}"
            value     = "name_of_worker"
            }
            task "processing_task_name" {
            driver = "docker"
            config {
                image = "image_docker"
                auth {
                server_address = "redacted"
                username = "redacted"
                password = "redacted"
                }
            }

        template {
            destination = "/local/delay.yaml"
            data        = <<EOF
            yaml_content
            worker: name_of_worker
            nomad_job_id: id_nomad_job
            processing_task_id: id_processing_task
            product_path: output_path
            input_id: id_of_input
            product_type_id: id_of_product_type
            input_path: path_of_input
            EOF
        }

        template {
            destination = "/local/s3cfg.txt"
            data        = <<EOF
            s3cmd_config
            EOF
        }

            service {
                name = "processing-routine"
                provider = "nomad"
            }
            }
        }
        }
        '''
        content = content.replace("image_docker", docker_image)
        content = content.replace("name_of_worker", worker_name)
        content = content.replace("id_processing_task", processing_task_id)
        content = content.replace("processing_task_name", "processing_task_" + processing_task_id)
        content = content.replace("id_nomad_job", nomad_job_id)
        content = content.replace("output_path", product_path)
        content = content.replace("id_of_input", input_id)
        content = content.replace("id_of_product_type", product_type_id)
        content = content.replace("path_of_input", input_path)

        # Write config file in docker container
        with open(yaml_path, 'r', encoding="utf-8") as config_file:
            file_data = config_file.read()
        content = content.replace("yaml_content", file_data)

        # Write s3config file in docker container
        with open(".s3cfg", 'r', encoding="utf-8") as config_file:
            file_data = config_file.read()
        content = content.replace("s3cmd_config", file_data)

        with open(file_path, 'w', encoding="utf-8") as fichier:
            fichier.write(content)

        self.logger.info("End create hcl file")

    def execute_nomad_job(self, file_name: str) -> None:
        """Run the nomad job file"""

        self.logger.info("Begin execute_nomad_job")
        subprocess.run(["nomad", "job", "run", file_name], check=True)
        self.logger.info("End execute_nomad_job")

    def delete_hcl_file(self, file_path: str) -> None:
        """Delete the hcl at path file_path if exist"""

        self.logger.info("Begin delete_hcl_file")
        if os.path.exists(file_path):
            os.remove(file_path)
        self.logger.info("End delete_hcl_file")

    @staticmethod
    def construct_product_path(cur: psycopg2.extensions.cursor, conn: psycopg2.extensions.connection, pt_id: str, now: datetime) -> tuple:
        """Construct the product path like that :
        - /HRWSI/L2A/SPM_PC/T09XVJ/2024/01/02/S2_L2A_20240102T103529_T09XVJ_20240102T104029.SAFE
        In other words :
        - /HRWSI/input_type/processing_condition/tile_name/year/month/day/S2_input_type_date_tile_name_date.SAFE
        Return also usefull information to create product in Database"""

        # Search input_id and product_type_id in Database
        collect_product_info_request = f"SELECT i.id AS input_id, i.input_path, processing_condition_name, date, tile, measurement_day, input_path, mission, input_type, ptype.id AS product_type_id FROM hrwsi.processing_routine pr INNER JOIN hrwsi.processing_condition pc ON pr.name = pc.processing_routine_name INNER JOIN hrwsi.input i ON pc.name = i.processing_condition_name INNER JOIN hrwsi.product_type ptype ON ptype.code = pr.product_type_code WHERE i.id = ( SELECT i.id FROM hrwsi.input i INNER JOIN hrwsi.processing_tasks pt ON pt.input_fk_id = i.id WHERE pt.id = {pt_id} );"
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, collect_product_info_request)
        conn.commit()

        for result in cur :
            input_id = result["input_id"]
            product_type_id = result["product_type_id"]
            processing_condition_name = result["processing_condition_name"]
            date = result["date"]
            tile = result["tile"]
            measurement_day = result["measurement_day"]
            mission = result["mission"]
            input_type = result["input_type"]
            catalogued_date = now
            input_path = result["input_path"]

            product_path = f"/HRWSI/{input_type}/{processing_condition_name}/{tile}/{str(measurement_day)[:4]}/{str(measurement_day)[4:6]}/{str(measurement_day)[6:8]}/{mission}_{input_type}_{date.strftime('%Y%m%dT%H%M%S')}_{tile}_{catalogued_date.strftime('%Y%m%dT%H%M%S')}.SAFE"

        return (product_path, str(input_id), str(product_type_id), input_path)