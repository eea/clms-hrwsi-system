BEGIN;

SELECT plan(5);


SELECT columns_are(
    'hrwsi',
    'processing_tasks',
    ARRAY [
        'id',
        'triggering_condition_fk_id',
        'processing_task_type_id',
        'creation_date',
        'nomad_job_id',
        'has_ended',
        'processing_mode_id',
        'intermediate_files_path',
        'priority_id'
    ]
);

SELECT fk_ok(
    'hrwsi',
    'processing_tasks',
    'triggering_condition_fk_id',
    'hrwsi',
    'triggering_conditions',
    'id'
);

SELECT fk_ok(
    'hrwsi',
    'processing_tasks',
    'processing_task_type_id',
    'hrwsi',
    'processing_task_type',
    'id'
);

SELECT fk_ok(
    'hrwsi',
    'processing_tasks',
    'processing_mode_id',
    'hrwsi',
    'processing_mode_type',
    'id'
);

SELECT fk_ok(
    'hrwsi',
    'processing_tasks',
    'priority_id',
    'hrwsi',
    'priority_level',
    'id'
);


SELECT * FROM finish();

ROLLBACK