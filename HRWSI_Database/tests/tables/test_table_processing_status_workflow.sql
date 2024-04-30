BEGIN;

SELECT plan(3);


SELECT columns_are(
    'hrwsi',
    'processing_status_workflow',
    ARRAY [
        'id', 
        'nomad_job_dispatch_fk_id', 
        'processing_status_id', 
        'date', 
        'message'
    ]
);

SELECT fk_ok(
    'hrwsi',
    'processing_status_workflow',
    'nomad_job_dispatch_fk_id',
    'hrwsi',
    'nomad_job_dispatch',
    'id'
);

SELECT fk_ok(
    'hrwsi',
    'processing_status_workflow',
    'processing_status_id',
    'hrwsi',
    'processing_status',
    'id'
);


SELECT * FROM finish();

ROLLBACK