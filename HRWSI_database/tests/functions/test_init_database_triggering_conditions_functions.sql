BEGIN;

SELECT plan(9);


SELECT has_function(
    'hrwsi',
    'get_triggering_conditions_by_triggering_product_path',
    ARRAY ['text']
);

SELECT has_function(
    'hrwsi',
    'get_triggering_conditions_by_measurement_day',
    ARRAY ['bigint']
);

SELECT has_function(
    'hrwsi',
    'get_triggering_conditions_without_processing_task',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_triggering_conditions_by_triggering_product_path',
    'setof hrwsi.triggering_conditions',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_triggering_conditions_by_measurement_day',
    'setof hrwsi.triggering_conditions',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'get_triggering_conditions_without_processing_task',
    'setof hrwsi.triggering_conditions',
    'test ok'
);


-- #################################################
-- 2. Seed data for function tests
-- #################################################

\set tc_id 1
\set tc_id_with_pt 2
\set tc_triggering_condition_type_id 1
\set tc_measurement_day 20240109
\set tc_measurement_day_2 20240110
\set pt_id 1
\set pt_processing_task_type_id 1
\set pt_has_ended True
\set pt_processing_mode_id 1
\set pt_priority_id 1

-- not able to use \set to set not numerical value at the moment. TODO how to parametrize non numerical values in psql tests.
-- \set tc_date '2024-01-09 12:15:11'::timestamp
-- \set tc_tile '33VUC'
-- \set tc_triggering_product_path '/eodata/Sentinel-2/MSI/L1C/2024/01/09/S2B_MSIL1C_20240109T103329_N0510_R108_T33VUC_20240109T112201.SAFE'
-- \set pt_creation_date
-- \set pt_nomad_job_id
-- \set pt_intermediate_files_path

-- triggering condition without processing task
insert into hrwsi.triggering_conditions
(id, triggering_condition_type_id, date, tile, measurement_day, triggering_product_path)
values (:tc_id, :tc_triggering_condition_type_id, '2024-01-09 12:15:11', '33VUC', :tc_measurement_day, '/eo');

-- triggering condition with processing task
insert into hrwsi.triggering_conditions
(id, triggering_condition_type_id, date, tile, measurement_day, triggering_product_path)
values (:tc_id_with_pt, :tc_triggering_condition_type_id, '2024-01-10 12:15:11', '33VUC', :tc_measurement_day_2, '/eo_2');

insert into hrwsi.processing_tasks
(id, triggering_condition_fk_id, processing_task_type_id, creation_date, nomad_job_id, has_ended, processing_mode_id, intermediate_files_path, priority_id)
values (:pt_id, :tc_id_with_pt, :pt_processing_task_type_id, '2024-01-09 12:16:11', '2b6d5038-a317-4aed-a04d-bd439c603b5d', :pt_has_ended, :pt_processing_mode_id, '/intermediate_file_path_1', :pt_priority_id);


-- #################################################
-- 3. Test function invocation success cases
-- #################################################

PREPARE get_triggering_conditions_by_triggering_product_path_have AS SELECT * FROM hrwsi.get_triggering_conditions_by_triggering_product_path('/eo');
PREPARE get_triggering_conditions_by_measurement_day_have AS SELECT * FROM hrwsi.get_triggering_conditions_by_measurement_day(:tc_measurement_day);
PREPARE get_triggering_conditions_without_processing_task_have AS SELECT * FROM hrwsi.get_triggering_conditions_by_measurement_day(:tc_measurement_day);

PREPARE want AS SELECT 1::bigint, 1::smallint, '2024-01-09 12:15:11'::timestamp, '33VUC'::text, 20240109::bigint, '/eo'::text;

SELECT results_eq(
    'get_triggering_conditions_by_triggering_product_path_have',
    'want',
    'test get_triggering_conditions_by_triggering_product_path'
);

SELECT results_eq(
    'get_triggering_conditions_by_measurement_day_have',
    'want',
    'test get_triggering_conditions_by_measurement_day'
);

SELECT results_eq(
    'get_triggering_conditions_without_processing_task_have',
    'want',
    'test get_triggering_conditions_without_processing_task'
);

SELECT * FROM finish();

ROLLBACK