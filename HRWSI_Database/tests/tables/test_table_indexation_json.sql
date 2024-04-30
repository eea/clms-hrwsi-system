BEGIN;

SELECT plan(3);


SELECT columns_are(
    'hrwsi',
    'indexation_json',
    ARRAY [
        'id',
        'product_fk_id',
        'indexation_file_type_id',
        'path'
    ]
);

SELECT fk_ok(
    'hrwsi',
    'indexation_json',
    'product_fk_id',
    'hrwsi',
    'products',
    'id'
);

SELECT fk_ok(
    'hrwsi',
    'indexation_json',
    'indexation_file_type_id',
    'hrwsi',
    'indexation_file_type',
    'id'
);


SELECT * FROM finish();

ROLLBACK