BEGIN;

SELECT plan(1);


SELECT columns_are(
    'hrwsi',
    'virtual_machine',
    ARRAY [
        'id',
        'name',
        'flavour'
    ]
);


SELECT * FROM finish();

ROLLBACK