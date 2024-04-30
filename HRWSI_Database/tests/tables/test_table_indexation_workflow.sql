BEGIN;

SELECT plan(3);


SELECT columns_are(
    'hrwsi',
    'indexation_workflow',
    ARRAY [
        'id',
        'product_fk_id',
        'publication_date',
        'indexation_date',
        'failure_date',
        'indexation_failure_type_id'
    ]
);

SELECT fk_ok(
    'hrwsi',
    'indexation_workflow',
    'product_fk_id',
    'hrwsi',
    'products',
    'id'
);

SELECT fk_ok(
    'hrwsi',
    'indexation_workflow',
    'indexation_failure_type_id',
    'hrwsi',
    'indexation_failure_type',
    'id'
);


SELECT * FROM finish();

ROLLBACK