-----------------------------------------------------------------------------

/*
Log level status, expressed as an integer with the same values as in logging.py,
so we can request only the messages with e.g. status > WARNING
*/
CREATE TABLE hrwsi.log_levels (
  id smallint NOT null UNIQUE,
  name text NOT null UNIQUE
);
INSERT INTO hrwsi.log_levels VALUES
  (50, 'CRITICAL'),
  (40, 'ERROR'),
  (30, 'WARNING'),
  (20, 'INFO'),
  (10, 'DEBUG');

--- TRIGGERS ---

/*
Add trigger to capture input insertion on Database in real time
*/
CREATE function hrwsi.notify_input_function()
RETURNS trigger as $$
  BEGIN 
    perform pg_notify('input_insertion', new_table.processing_condition_name::text)
    FROM new_table;
    RETURN NEW; 
  END; 
$$ LANGUAGE plpgsql;

CREATE TRIGGER notify_input_trigger
AFTER INSERT ON hrwsi.input
REFERENCING NEW TABLE AS new_table 
FOR EACH STATEMENT EXECUTE FUNCTION hrwsi.notify_input_function();

/*
Add trigger to capture processing tasks processed on Database in real time
*/
CREATE function hrwsi.notify_processing_task_processed_function()
RETURNS trigger as $$
  BEGIN
    IF NEW.processing_status_id = 2 THEN
        perform pg_notify('processing_tasks_state_processed', NEW.id::text);
        RETURN NEW;
    ELSE
      RETURN NULL;
    END IF;
  END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER notify_processing_task_processed_trigger
AFTER INSERT ON hrwsi.processing_status_workflow
FOR EACH ROW EXECUTE FUNCTION hrwsi.notify_processing_task_processed_function();

