BEGIN;

SELECT plan(3);


SELECT columns_are(
    'hrwsi',
    'processing_tasks',
    ARRAY [
        'id',
        'input_fk_id',
        'virtual_machine_id',
        'creation_date',
        'preceding_input_id',
        'nomad_job_id',
        'has_ended',
        'intermediate_files_path'
    ]
);

SELECT fk_ok(
    'hrwsi',
    'processing_tasks',
    'input_fk_id',
    'hrwsi',
    'input',
    'id'
);

SELECT fk_ok(
    'hrwsi',
    'processing_tasks',
    'virtual_machine_id',
    'hrwsi',
    'virtual_machine',
    'id'
);


SELECT * FROM finish();

ROLLBACK