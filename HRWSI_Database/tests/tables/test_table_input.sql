BEGIN;

SELECT plan(2);


SELECT columns_are(
    'hrwsi',
    'input',
    ARRAY [
        'id', 
        'processing_condition_name', 
        'date', 
        'tile', 
        'measurement_day', 
        'input_path',
        'mission'
    ]
);

SELECT fk_ok(
    'hrwsi',
    'input',
    'processing_condition_name',
    'hrwsi',
    'processing_condition',
    'name'
);


SELECT * FROM finish();

ROLLBACK