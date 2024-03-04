BEGIN;

SELECT plan(2);


SELECT columns_are(
    'hrwsi',
    'triggering_conditions',
    ARRAY [
        'id', 
        'triggering_condition_type_id', 
        'date', 
        'tile', 
        'measurement_day', 
        'triggering_product_path'
    ]
);

SELECT fk_ok(
    'hrwsi',
    'triggering_conditions',
    'triggering_condition_type_id',
    'hrwsi',
    'triggering_condition_type',
    'id'
);


SELECT * FROM finish();

ROLLBACK