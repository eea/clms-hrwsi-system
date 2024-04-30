BEGIN;

SELECT plan(42);


SELECT has_function(
    'hrwsi',
    'get_number_of_error_statuses_by_processing_task',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'is_processing_task_processed',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'get_status_history_by_processing_task_id',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'get_processing_tasks_not_finished',
    'test ok'
);

SELECT has_function(
    'hrwsi',
    'get_nomad_job_dispatch_list_by_processing_task_id',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'get_current_nomad_job_dispatch_by_processing_task_id',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'are_all_processing_tasks_in_vm_processed',
    ARRAY ['uuid']
);

SELECT has_function(
    'hrwsi',
    'get_preceding_processing_task',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'is_preceding_processing_task_processed',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'is_one_processing_task_processed_for_an_input',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'are_all_processing_tasks_ended_for_an_input',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'get_ids_of_processing_tasks_ready_to_be_launched',
    'test ok'
);

SELECT has_function(
    'hrwsi',
    'get_product_data_type_of_processing_tasks_not_ended',
    'test ok'
);

SELECT has_function(
    'hrwsi',
    'get_id_of_unprocessed_inputs_with_all_pt_ended',
    ARRAY ['timestamp']
);


SELECT function_returns(
    'hrwsi',
    'get_number_of_error_statuses_by_processing_task',
    'bigint',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'is_processing_task_processed',
    'boolean',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_status_history_by_processing_task_id',
    'setof hrwsi.processing_status_history',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_processing_tasks_not_finished',
    'setof hrwsi.processing_tasks',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_nomad_job_dispatch_list_by_processing_task_id',
    'setof hrwsi.nomad_job_dispatch_info',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_current_nomad_job_dispatch_by_processing_task_id',
    'setof hrwsi.nomad_job_dispatch_info',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'are_all_processing_tasks_in_vm_processed',
    'setof boolean',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_preceding_processing_task',
    'setof hrwsi.processing_tasks',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'is_preceding_processing_task_processed',
    'setof boolean',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'is_one_processing_task_processed_for_an_input',
    'setof boolean',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'are_all_processing_tasks_ended_for_an_input',
    'boolean',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_ids_of_processing_tasks_ready_to_be_launched',
    'setof bigint',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_product_data_type_of_processing_tasks_not_ended',
    'setof text',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_id_of_unprocessed_inputs_with_all_pt_ended',
    'setof bigint',
    'test ok'
);

-- #################################################
-- 2. Seed data for function tests
-- #################################################

\set input_id_1 1
\set input_id_2 2
\set input_id_3 3
\set measurement_day_1 20240109
\set measurement_day_2 20240110
\set measurement_day_3 20240108
\set pt_id_1 1
\set pt_id_2 2
\set pt_id_3 3
\set njd_id_1 1
\set njd_id_2 2
\set njd_id_3 3
\set njd_id_4 4
\set pt_has_ended True
\set pt_has_not_ended False
\set ps_id_1 1
\set ps_id_2 2
\set ps_id_3 3
\set psw_id_1 1
\set psw_id_2 2
\set psw_id_3 3
\set psw_id_4 4
\set psw_id_5 5

-- -- not able to use \set to set not numerical value at the moment. TODO how to parametrize non numerical values in psql tests.
-- -- \set tc_date '2024-01-09 12:15:11'::timestamp
-- -- \set tc_tile '33VUC'
-- -- \set tc_product_path '/eodata/Sentinel-2/MSI/L1C/2024/01/09/S2B_MSIL1C_20240109T103329_N0510_R108_T33VUC_20240109T112201.SAFE'
-- -- \set pt_creation_date
-- -- \set pt_nomad_job_id
-- -- \set pt_intermediate_files_path
-- 
-- input 1
INSERT INTO hrwsi.input
(id, processing_condition_name, date, tile, measurement_day, input_path, mission)
VALUES (:input_id_1, 'MAJA_PC', '2024-01-09 12:15:11', '33VUC', :measurement_day_1, '/eo', 'S2');

-- input 2
INSERT INTO hrwsi.input
(id, processing_condition_name, date, tile, measurement_day, input_path, mission)
VALUES (:input_id_2, 'FSC_PC', '2024-01-10 12:15:11', '33VUC', :measurement_day_2, '/eo_2', 'S2');

-- input 3
INSERT INTO hrwsi.input
(id, processing_condition_name, date, tile, measurement_day, input_path, mission)
VALUES (:input_id_3, 'MAJA_PC', '2024-01-08 12:15:11', '33VUC', :measurement_day_3, '/eo_3', 'S2');

-- virtual machine with all task ended
INSERT INTO hrwsi.virtual_machine
(id, name, flavour)
VALUES ('84374172-c990-11ee-8bee-7c8ae199ff1c', 'worker_1', 'flavour1');

-- virtual machine with all task not ended
INSERT INTO hrwsi.virtual_machine
(id, name, flavour)
VALUES ('94374172-c990-11ee-8bee-7c8ae199ff1d', 'worker_2', 'flavour1');

-- processing_task 1 ended vm 1
INSERT INTO hrwsi.processing_tasks
(id, input_fk_id, virtual_machine_id, creation_date, preceding_input_id, nomad_job_id, has_ended, intermediate_files_path)
VALUES (:pt_id_1, :input_id_1, '84374172-c990-11ee-8bee-7c8ae199ff1c', '2024-01-09 12:16:11', NULL, '2b6d5038-a317-4aed-a04d-bd439c603b5d', :pt_has_ended, '/intermediate_file_path_1');

-- processing_task 3 ended vm 2
INSERT INTO hrwsi.processing_tasks
(id, input_fk_id, virtual_machine_id, creation_date, preceding_input_id, nomad_job_id, has_ended, intermediate_files_path)
VALUES (:pt_id_3, :input_id_3, '94374172-c990-11ee-8bee-7c8ae199ff1d', '2024-01-09 12:16:11', NULL, '2b6d5038-a317-4aed-a04d-bd439c603b5d', :pt_has_ended, '/intermediate_file_path_3');

-- processing_task 2 not ended vm 2
INSERT INTO hrwsi.processing_tasks
(id, input_fk_id, virtual_machine_id, creation_date, preceding_input_id, nomad_job_id, has_ended, intermediate_files_path)
VALUES (:pt_id_2, :input_id_2, '94374172-c990-11ee-8bee-7c8ae199ff1d', '2024-01-10 12:16:12', :input_id_3, NULL, :pt_has_not_ended, '/intermediate_file_path_2');

-- nomad job dispatch 1 for processing task 1
INSERT INTO hrwsi.nomad_job_dispatch
(id, processing_task_fk_id, nomad_job_dispatch, dispatch_date, log_path)
VALUES (:njd_id_1, :pt_id_1, 'dispatch-1704816717-aa015f21', '2024-01-09 12:17:11', 'log_path_1-1');

-- nomad job dispatch 2 for processing task 1
INSERT INTO hrwsi.nomad_job_dispatch
(id, processing_task_fk_id, nomad_job_dispatch, dispatch_date, log_path)
VALUES (:njd_id_2, :pt_id_1, 'dispatch-1704816717-aa015f22', '2024-01-09 12:18:11', 'log_path_1-2');

-- nomad job dispatch 1 for processing task 3
INSERT INTO hrwsi.nomad_job_dispatch
(id, processing_task_fk_id, nomad_job_dispatch, dispatch_date, log_path)
VALUES (:njd_id_4, :pt_id_3, 'dispatch-1704816717-aa015f23', '2024-01-10 12:17:11', 'log_path_3-1');

-- processing status workflow 1 for nomad job dispatch 1 for processing task 1
INSERT INTO hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
VALUES (:psw_id_1, :njd_id_1, :ps_id_1, '2024-01-09 12:17:12', 'status 1');

-- processing status workflow 2 for nomad job dispatch 1 for processing task 1
INSERT INTO hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
VALUES (:psw_id_2, :njd_id_1, :ps_id_3, '2024-01-09 12:17:13', 'status 2');

-- processing status workflow 1 for nomad job dispatch 2 for processing task 1
INSERT INTO hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
VALUES (:psw_id_3, :njd_id_2, :ps_id_1, '2024-01-09 12:18:13', 'status 3');

-- processing status workflow 2 for nomad job dispatch 2 for processing task 1
INSERT INTO hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
VALUES (:psw_id_4, :njd_id_2, :ps_id_3, '2024-01-09 12:18:14', 'status 4');

-- processing status workflow 1 for nomad job dispatch 1 for processing task 3
INSERT INTO hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
VALUES (:psw_id_5, :njd_id_4, :ps_id_2, '2024-01-10 12:17:12', 'status 5');


-- -- #################################################
-- -- 3. Test function invocation success cases
-- -- #################################################

PREPARE get_number_of_error_statuses_by_processing_task_have AS 
    SELECT * 
    FROM hrwsi.get_number_of_error_statuses_by_processing_task(:pt_id_1);

PREPARE is_processing_task_processed_have AS 
    SELECT * 
    FROM hrwsi.is_processing_task_processed(:pt_id_3);

PREPARE get_processing_tasks_not_finished_have AS 
    SELECT * 
    FROM hrwsi.get_processing_tasks_not_finished();

PREPARE get_status_history_by_processing_task_id_have AS 
    SELECT * 
    FROM hrwsi.get_status_history_by_processing_task_id(:pt_id_1);

PREPARE get_nomad_job_dispatch_list_by_processing_task_id_have AS 
    SELECT * 
    FROM hrwsi.get_nomad_job_dispatch_list_by_processing_task_id(:pt_id_1);

PREPARE get_current_nomad_job_dispatch_by_processing_task_id_have AS 
    SELECT * 
    FROM hrwsi.get_current_nomad_job_dispatch_by_processing_task_id(:pt_id_1);

PREPARE are_all_processing_tasks_in_vm_processed_have AS 
    SELECT * 
    FROM hrwsi.are_all_processing_tasks_in_vm_processed('94374172-c990-11ee-8bee-7c8ae199ff1d');

PREPARE get_preceding_processing_task_have AS 
    SELECT * 
    FROM hrwsi.get_preceding_processing_task(:pt_id_2);

PREPARE is_preceding_processing_task_processed_have AS 
    SELECT * 
    FROM hrwsi.is_preceding_processing_task_processed(:pt_id_2);

PREPARE is_one_processing_task_processed_for_an_input_have AS 
    SELECT * 
    FROM hrwsi.is_one_processing_task_processed_for_an_input(:input_id_3);

PREPARE are_all_processing_tasks_ended_for_an_input_have AS 
    SELECT * 
    FROM hrwsi.are_all_processing_tasks_ended_for_an_input(:input_id_1);

PREPARE get_ids_of_processing_tasks_ready_to_be_launched_have AS 
    SELECT * 
    FROM hrwsi.get_ids_of_processing_tasks_ready_to_be_launched();

PREPARE get_product_data_type_of_processing_tasks_not_ended_have AS 
    SELECT * 
    FROM hrwsi.get_product_data_type_of_processing_tasks_not_ended();

PREPARE get_id_of_unprocessed_inputs_with_all_pt_ended_have AS 
    SELECT * 
    FROM hrwsi.get_id_of_unprocessed_inputs_with_all_pt_ended('2024-01-09');


PREPARE get_processing_tasks_not_finished_want AS 
    SELECT 
        :pt_id_2::bigint, 
        :input_id_2::bigint, 
        '94374172-c990-11ee-8bee-7c8ae199ff1d'::uuid, 
        '2024-01-10 12:16:12'::timestamp, 
        :input_id_3::bigint, 
        NULL::uuid, 
        :pt_has_not_ended::boolean,
        '/intermediate_file_path_2'::text;

PREPARE get_status_history_by_processing_task_id_want AS 
    SELECT psw.id, psw.date, ps.code, ps.name, psw.message 
    FROM hrwsi.nomad_job_dispatch njd
    JOIN hrwsi.processing_status_workflow psw ON psw.nomad_job_dispatch_fk_id = njd.id
    JOIN hrwsi.processing_status ps ON ps.id = psw.processing_status_id
    WHERE psw.id = 1 OR psw.id = 2 OR psw.id = 3 OR psw.id = 4
    ORDER BY psw.id ASC;

PREPARE get_nomad_job_dispatch_list_by_processing_task_id_want AS 
    SELECT pt.nomad_job_id, njd.nomad_job_dispatch, njd.dispatch_date, njd.log_path
    FROM hrwsi.processing_tasks pt
    JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
    WHERE njd.id = 1 OR njd.id = 2;

PREPARE get_current_nomad_job_dispatch_by_processing_task_id_want AS 
    SELECT pt.nomad_job_id, njd.nomad_job_dispatch, njd.dispatch_date, njd.log_path
    FROM hrwsi.processing_tasks pt
    JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
    WHERE njd.id = 2;

PREPARE get_number_of_error_statuses_by_processing_task_want AS
    SELECT 2::bigint;

PREPARE is_processing_task_processed_want AS
    SELECT True::boolean;

PREPARE are_all_processing_tasks_in_vm_processed_want AS
    SELECT False::boolean;

PREPARE get_preceding_processing_task_want AS 
    SELECT 
        :pt_id_3::bigint,
        :input_id_3::bigint, 
        '94374172-c990-11ee-8bee-7c8ae199ff1d'::uuid, 
        '2024-01-09 12:16:11'::timestamp, 
        NULL::bigint, 
        '2b6d5038-a317-4aed-a04d-bd439c603b5d'::uuid, 
        :pt_has_ended::boolean,
        '/intermediate_file_path_3'::text;

PREPARE is_preceding_processing_task_processed_want AS
    SELECT True::boolean;

PREPARE is_one_processing_task_processed_for_an_input_want AS
    SELECT True::boolean;

PREPARE are_all_processing_tasks_ended_for_an_input_want AS
    SELECT True::boolean;

PREPARE get_ids_of_processing_tasks_ready_to_be_launched_want AS
    SELECT :pt_id_2::bigint;

PREPARE get_product_data_type_of_processing_tasks_not_ended_want AS
    SELECT 'L2B'::text;

PREPARE get_id_of_unprocessed_inputs_with_all_pt_ended_want AS
    SELECT :pt_id_1::bigint;


SELECT results_eq(
    'get_number_of_error_statuses_by_processing_task_have',
    'get_number_of_error_statuses_by_processing_task_want',
    'test get_number_of_error_statuses_by_processing_task'
);
 
SELECT results_eq(
    'is_processing_task_processed_have',
    'is_processing_task_processed_want',
    'test is_processing_task_processed'
);

SELECT results_eq(
    'get_processing_tasks_not_finished_have',
    'get_processing_tasks_not_finished_want',
    'test get_processing_tasks_not_finished'
);

SELECT results_eq(
    'get_status_history_by_processing_task_id_have',
    'get_status_history_by_processing_task_id_want',
    'test get_status_history_by_processing_task_id'
);

SELECT results_eq(
    'get_nomad_job_dispatch_list_by_processing_task_id_have',
    'get_nomad_job_dispatch_list_by_processing_task_id_want',
    'test get_nomad_job_dispatch_list_by_processing_task_id'
);

SELECT results_eq(
    'get_current_nomad_job_dispatch_by_processing_task_id_have',
    'get_current_nomad_job_dispatch_by_processing_task_id_want',
    'test get_current_nomad_job_dispatch_by_processing_task_id'
);

SELECT results_eq(
    'are_all_processing_tasks_in_vm_processed_have',
    'are_all_processing_tasks_in_vm_processed_want',
    'test are_all_processing_tasks_in_vm_processed'
);

SELECT results_eq(
    'get_preceding_processing_task_have',
    'get_preceding_processing_task_want',
    'test get_preceding_processing_task'
);

SELECT results_eq(
    'is_preceding_processing_task_processed_have',
    'is_preceding_processing_task_processed_want',
    'test is_preceding_processing_task_processed'
);

SELECT results_eq(
    'is_one_processing_task_processed_for_an_input_have',
    'is_one_processing_task_processed_for_an_input_want',
    'test is_one_processing_task_processed_for_an_input'
);

SELECT results_eq(
    'are_all_processing_tasks_ended_for_an_input_have',
    'are_all_processing_tasks_ended_for_an_input_want',
    'test are_all_processing_tasks_ended_for_an_input'
);

SELECT results_eq(
    'get_ids_of_processing_tasks_ready_to_be_launched_have',
    'get_ids_of_processing_tasks_ready_to_be_launched_want',
    'test get_ids_of_processing_tasks_ready_to_be_launched'
);

SELECT results_eq(
    'get_product_data_type_of_processing_tasks_not_ended_have',
    'get_product_data_type_of_processing_tasks_not_ended_want',
    'test get_product_data_type_of_processing_tasks_not_ended'
);

SELECT results_eq(
    'get_id_of_unprocessed_inputs_with_all_pt_ended_have',
    'get_id_of_unprocessed_inputs_with_all_pt_ended_want',
    'test get_id_of_unprocessed_inputs_with_all_pt_ended'
);


SELECT * FROM finish();

ROLLBACK