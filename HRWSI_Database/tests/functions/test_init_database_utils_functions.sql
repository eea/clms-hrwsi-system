BEGIN;

SELECT plan(8);

SELECT has_trigger(
    'hrwsi',
    'input',
    'notify_input_trigger',
    'test ok'
);

SELECT has_trigger(
    'hrwsi',
    'processing_status_workflow',
    'notify_processing_task_processed_trigger',
    'test ok'
);

SELECT trigger_is(
    'hrwsi',
    'input',
    'notify_input_trigger',
    'hrwsi',
    'notify_input_function',
    'test ok'
);

SELECT trigger_is(
    'hrwsi',
    'processing_status_workflow',
    'notify_processing_task_processed_trigger',
    'hrwsi',
    'notify_processing_task_processed_function',
    'test ok'
);

SELECT has_function(
    'hrwsi',
    'notify_input_function',
    'test ok'
);

SELECT has_function(
    'hrwsi',
    'notify_processing_task_processed_function',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'notify_input_function',
    'trigger',
    'test ok'
);

SELECT function_returns(
    'hrwsi',
    'notify_processing_task_processed_function',
    'trigger',
    'test ok'
);

SELECT * FROM finish();

ROLLBACK