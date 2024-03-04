BEGIN;

SELECT plan(18);


SELECT has_function(
    'hrwsi',
    'get_number_of_error_statuses_by_processing_task',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'is_processing_tasks_processed',
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

SELECT function_returns(
    'hrwsi',
    'get_number_of_error_statuses_by_processing_task',
    'bigint',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'is_processing_tasks_processed',
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


-- #################################################
-- 2. Seed data for function tests
-- #################################################

\set tc_id_1 1
\set tc_id_2 2
\set tc_id_with_pt 2
\set tc_triggering_condition_type_id 1
\set measurement_day_1 20240109
\set measurement_day_2 20240110
\set pt_id_1 1
\set pt_id_2 2
\set njd_id_1 1
\set njd_id_2 2
\set njd_id_3 3
\set pt_processing_task_type_id 1
\set pt_has_ended True
\set pt_has_not_ended False
\set pt_processing_mode_id 1
\set pt_priority_id 1
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
-- -- \set tc_triggering_product_path '/eodata/Sentinel-2/MSI/L1C/2024/01/09/S2B_MSIL1C_20240109T103329_N0510_R108_T33VUC_20240109T112201.SAFE'
-- -- \set pt_creation_date
-- -- \set pt_nomad_job_id
-- -- \set pt_intermediate_files_path
-- 
-- triggering condition 1
insert into hrwsi.triggering_conditions
(id, triggering_condition_type_id, date, tile, measurement_day, triggering_product_path)
values (:tc_id_1, :tc_triggering_condition_type_id, '2024-01-09 12:15:11', '33VUC', :measurement_day_1, '/eo');

-- triggering condition 2
insert into hrwsi.triggering_conditions
(id, triggering_condition_type_id, date, tile, measurement_day, triggering_product_path)
values (:tc_id_2, :tc_triggering_condition_type_id, '2024-01-10 12:15:11', '33VUC', :measurement_day_2, '/eo_2');

-- processing_task ended
insert into hrwsi.processing_tasks
(id, triggering_condition_fk_id, processing_task_type_id, creation_date, nomad_job_id, has_ended, processing_mode_id, intermediate_files_path, priority_id)
values (:pt_id_1, :tc_id_1, :pt_processing_task_type_id, '2024-01-09 12:16:11', '2b6d5038-a317-4aed-a04d-bd439c603b5d', :pt_has_ended, :pt_processing_mode_id, '/intermediate_file_path_1', :pt_priority_id);

-- processing_task not ended
insert into hrwsi.processing_tasks
(id, triggering_condition_fk_id, processing_task_type_id, creation_date, nomad_job_id, has_ended, processing_mode_id, intermediate_files_path, priority_id)
values (:pt_id_2, :tc_id_2, :pt_processing_task_type_id, '2024-01-10 12:16:12', '2b6d5038-a317-4aed-a04d-bd439c603b5e', :pt_has_not_ended, :pt_processing_mode_id, '/intermediate_file_path_2', :pt_priority_id);

-- nomad job dispatch 1 for processing task 1
insert into hrwsi.nomad_job_dispatch
(id, processing_task_fk_id, nomad_job_dispatch, dispatch_date, log_path)
values (:njd_id_1, :pt_id_1, 'dispatch-1704816717-aa015f21', '2024-01-09 12:17:11', 'log_path_1-1');

-- nomad job dispatch 2 for processing task 1
insert into hrwsi.nomad_job_dispatch
(id, processing_task_fk_id, nomad_job_dispatch, dispatch_date, log_path)
values (:njd_id_2, :pt_id_1, 'dispatch-1704816717-aa015f22', '2024-01-09 12:18:11', 'log_path_1-2');

-- nomad job dispatch 1 for processing task 2
insert into hrwsi.nomad_job_dispatch
(id, processing_task_fk_id, nomad_job_dispatch, dispatch_date, log_path)
values (:njd_id_3, :pt_id_2, 'dispatch-1704816717-aa015f23', '2024-01-10 12:17:11', 'log_path_2-1');

-- processing status workflow 1 for nomad job dispatch 1 for processing task 1
insert into hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
values (:psw_id_1, :njd_id_1, :ps_id_2, '2024-01-09 12:17:12', 'status 1');

-- processing status workflow 2 for nomad job dispatch 1 for processing task 1
insert into hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
values (:psw_id_2, :njd_id_1, :ps_id_3, '2024-01-09 12:17:13', 'status 2');

-- processing status workflow 1 for nomad job dispatch 2 for processing task 1
insert into hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
values (:psw_id_3, :njd_id_2, :ps_id_2, '2024-01-09 12:18:13', 'status 3');

-- processing status workflow 2 for nomad job dispatch 2 for processing task 1
insert into hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
values (:psw_id_4, :njd_id_2, :ps_id_1, '2024-01-09 12:18:14', 'status 4');

-- processing status workflow 1 for nomad job dispatch 1 for processing task 2
insert into hrwsi.processing_status_workflow
(id, nomad_job_dispatch_fk_id, processing_status_id, date, message)
values (:psw_id_5, :njd_id_3, :ps_id_2, '2024-01-10 12:17:12', 'status 1');


-- -- #################################################
-- -- 3. Test function invocation success cases
-- -- #################################################

PREPARE get_number_of_error_statuses_by_processing_task_have AS 
    SELECT * 
    FROM hrwsi.get_number_of_error_statuses_by_processing_task(:pt_id_1);

PREPARE is_processing_tasks_processed_have AS 
    SELECT * 
    FROM hrwsi.is_processing_tasks_processed(:pt_id_1);

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


PREPARE get_processing_tasks_not_finished_want AS 
    SELECT 
        :pt_id_2::bigint, 
        :tc_id_2::bigint, 
        :pt_processing_task_type_id::smallint, 
        '2024-01-10 12:16:12'::timestamp, 
        '2b6d5038-a317-4aed-a04d-bd439c603b5e'::uuid, 
        :pt_has_not_ended::boolean, 
        :pt_processing_mode_id::smallint, 
        '/intermediate_file_path_2'::text, 
        :pt_priority_id::smallint;

PREPARE get_status_history_by_processing_task_id_want AS 
    SELECT psw.id, psw.date, ps.code, ps.name, psw.message 
    FROM hrwsi.nomad_job_dispatch njd
    INNER JOIN hrwsi.processing_status_workflow psw ON psw.nomad_job_dispatch_fk_id = njd.id
    INNER JOIN hrwsi.processing_status ps ON ps.id = psw.processing_status_id
    WHERE psw.id = 1 OR psw.id = 2 OR psw.id = 3 OR psw.id = 4
    ORDER BY psw.id ASC;

PREPARE get_nomad_job_dispatch_list_by_processing_task_id_want AS 
    SELECT pt.nomad_job_id, njd.nomad_job_dispatch, njd.dispatch_date, njd.log_path
    FROM hrwsi.processing_tasks pt
    INNER JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
    WHERE njd.id = 1 OR njd.id = 2;

PREPARE get_current_nomad_job_dispatch_by_processing_task_id_want AS 
    SELECT pt.nomad_job_id, njd.nomad_job_dispatch, njd.dispatch_date, njd.log_path
    FROM hrwsi.processing_tasks pt
    INNER JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
    WHERE njd.id = 2;

PREPARE get_number_of_error_statuses_by_processing_task_want AS
    SELECT 1::bigint;

PREPARE is_processing_tasks_processed_want AS
    SELECT True::boolean;
 
SELECT results_eq(
    'get_number_of_error_statuses_by_processing_task_have',
    'get_number_of_error_statuses_by_processing_task_want',
    'test get_number_of_error_statuses_by_processing_task_have'
);
 
SELECT results_eq(
    'is_processing_tasks_processed_have',
    'is_processing_tasks_processed_want',
    'test is_processing_tasks_processed'
);

SELECT results_eq(
    'get_processing_tasks_not_finished_have',
    'get_processing_tasks_not_finished_want',
    'test get_triggering_conditions_without_processing_task'
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

SELECT * FROM finish();

ROLLBACK