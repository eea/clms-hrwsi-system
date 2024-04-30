BEGIN;

SELECT plan(2);


SELECT columns_are(
    'hrwsi',
    'nomad_job_dispatch',
    ARRAY [
        'id', 
        'processing_task_fk_id', 
        'nomad_job_dispatch', 
        'dispatch_date', 
        'log_path'
    ]
);

SELECT fk_ok(
    'hrwsi',
    'nomad_job_dispatch',
    'processing_task_fk_id',
    'hrwsi',
    'processing_tasks',
    'id'
);


SELECT * FROM finish();

ROLLBACK