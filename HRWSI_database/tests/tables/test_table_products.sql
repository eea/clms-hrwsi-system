BEGIN;

SELECT plan(3);


SELECT columns_are(
    'hrwsi',
    'products',
    ARRAY [
        'id',
        'triggering_condition_fk_id',
        'product_path',
        'creation_date',
        'catalogued_date',
        'kpi_file_path',
        'product_type_id'
    ]
);

SELECT fk_ok(
    'hrwsi',
    'products',
    'triggering_condition_fk_id',
    'hrwsi',
    'triggering_conditions',
    'id'
);

SELECT fk_ok(
    'hrwsi',
    'products',
    'product_type_id',
    'hrwsi',
    'product_type',
    'id'
);


SELECT * FROM finish();

ROLLBACK