----------------------------------
----- PROCESSING TASKS -----------
----------------------------------

--- COLD TABLES ---

/*
Table for the processing status codes.
List all processing status code that describe the evolution of the processing tasks.
These processing status are representative of what we expect to encoutner for processing
tasks when monitoring the HRWSI oprationnal production system.
*/
CREATE TABLE hrwsi.processing_status (

  id smallint PRIMARY KEY,
  code bigint NOT null UNIQUE,
  name text NOT null UNIQUE,
  description text
);
INSERT INTO hrwsi.processing_status VALUES
  (1, 0, 'started', ''),
  (2, 1, 'processed', ''),
  (3, 110, 'internal_error', ''),
  (4, 210, 'external_error', '');

--- CORE TABLES ---

/*
Table for the virtual machines.
List all the virtual machines, with all the informations needed.
*/
CREATE TABLE hrwsi.virtual_machine (

  id uuid PRIMARY KEY,
  name text NOT NULL,
  flavour text NOT null
);


/*
Table for the processing tasks.
List all the processing tasks, linked to an intput, with all the informations needed.
One input can be linked to several processing tasks.
One processing tasks is associated with one nomad job dispatch.
*/
CREATE TABLE hrwsi.processing_tasks (

  id bigserial UNIQUE,
  input_fk_id bigserial REFERENCES hrwsi.input(id) ON DELETE CASCADE,
  virtual_machine_id uuid REFERENCES hrwsi.virtual_machine(id) NOT null,
  creation_date timestamp NOT null,
  preceding_input_id bigint,
  nomad_job_id uuid,
  has_ended boolean,
  intermediate_files_path text
);

/*
Table for nomad job dispatch.
List all nomad job dispatch, linked to the processing task corresponding.
A nomad job dispatch has several processing status workflow depending on the evolution of the processing task.
*/
CREATE TABLE hrwsi.nomad_job_dispatch (

  id bigserial UNIQUE,
  processing_task_fk_id bigserial REFERENCES hrwsi.processing_tasks(id) ON DELETE CASCADE NOT null,
  nomad_job_dispatch text NOT null,
  dispatch_date timestamp NOT null,
  log_path text
);

/*
Table for the processing status workflow.
List all processing status, linked to the nomad job dispatch of which they describe the evolution.
*/
CREATE TABLE hrwsi.processing_status_workflow (

  id bigserial UNIQUE,
  nomad_job_dispatch_fk_id bigserial REFERENCES hrwsi.nomad_job_dispatch(id) ON DELETE CASCADE NOT null,
  processing_status_id smallint REFERENCES hrwsi.processing_status(id) NOT null,
  date timestamp NOT null,
  message text
);


--- TYPES ---

CREATE TYPE hrwsi.nomad_job_dispatch_info AS
  (
    nomad_job_id uuid,
    nomad_job_dispatch text,
    nomad_job_dispatch_creation_date timestamp,
    nomad_job_dispatch_log_file_path text
  );

CREATE TYPE hrwsi.processing_status_history AS
  (
    id bigint,
    processing_status_date timestamp,
    processing_status_code bigint,
    processing_status_name text,
    processing_status_message text
  );

--- FUNCTIONS ---

/*
Not already used because the error handling is not yet implemented
*/
CREATE FUNCTION hrwsi.get_number_of_error_statuses_by_processing_task (processing_task_id bigint)
  RETURNS bigint AS $$

  declare 
    error_statuses_number bigint;
-- To be used to know if a processing task can't be processed cause of to many errors
  BEGIN 
    SELECT COUNT(psw.id) INTO error_statuses_number
    FROM hrwsi.processing_tasks pt
    JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
    JOIN hrwsi.processing_status_workflow psw ON psw.nomad_job_dispatch_fk_id = njd.id
    WHERE pt.id = processing_task_id
    AND psw.processing_status_id in (3,4);

    RETURN error_statuses_number;
  END $$ LANGUAGE plpgsql stable;


CREATE FUNCTION hrwsi.is_processing_task_processed (processing_task_id bigint)
  RETURNS boolean AS $$
-- To be used to know if a processing task is processed
-- This function is used in other functions
  BEGIN 
    RETURN CASE WHEN EXISTS (
      SELECT
          pt.id
      FROM hrwsi.processing_tasks pt
      JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
      JOIN hrwsi.processing_status_workflow psw ON psw.nomad_job_dispatch_fk_id = njd.id
      WHERE psw.processing_status_id = 2
      AND pt.id = processing_task_id
    )
    THEN CAST(1 AS bit)
    ELSE CAST(0 AS bit)
    END CASE;
  END $$ LANGUAGE plpgsql stable;


CREATE FUNCTION hrwsi.get_processing_tasks_not_finished ()
    RETURNS setof hrwsi.processing_tasks AS $$
-- To be used to collect all the processing tasks not ended
-- This function is used by the Launcher : if all the tasks are finished then it can stop
BEGIN RETURN query SELECT
    pt.id,
    pt.input_fk_id,
    pt.virtual_machine_id,
    pt.creation_date,
    pt.preceding_input_id,
    pt.nomad_job_id,
    pt.has_ended,
    pt.intermediate_files_path
FROM hrwsi.processing_tasks pt
WHERE pt.has_ended = False;
END $$ LANGUAGE plpgsql stable;

/*
Not already used because the error handling is not yet implemented
*/
CREATE FUNCTION hrwsi.get_status_history_by_processing_task_id (processing_task_id bigint)
    RETURNS setof hrwsi.processing_status_history AS $$
-- To be used to know the status history of a processing task thanks to it's id
BEGIN RETURN query SELECT
    psw.id,
    psw.date,
    ps.code,
    ps.name,
    psw.message
FROM hrwsi.nomad_job_dispatch njd
JOIN hrwsi.processing_status_workflow psw ON psw.nomad_job_dispatch_fk_id = njd.id
JOIN hrwsi.processing_status ps ON ps.id = psw.processing_status_id
WHERE njd.processing_task_fk_id = processing_task_id;
END $$ LANGUAGE plpgsql stable;

/*
Not used yet
*/
CREATE FUNCTION hrwsi.get_nomad_job_dispatch_list_by_processing_task_id (processing_task_id bigint)
    RETURNS setof hrwsi.nomad_job_dispatch_info AS $$
-- To be used to know the list of all the nomad job dispatch of a processing task thanks to it's id
BEGIN RETURN query SELECT
    pt.nomad_job_id,
    njd.nomad_job_dispatch,
    njd.dispatch_date,
    njd.log_path
FROM hrwsi.processing_tasks pt
JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
WHERE pt.id = processing_task_id;
END $$ LANGUAGE plpgsql stable;

/*
Not used yet
*/
CREATE FUNCTION hrwsi.get_current_nomad_job_dispatch_by_processing_task_id (processing_task_id bigint)
    RETURNS setof hrwsi.nomad_job_dispatch_info AS $$
-- To be used to know the current nomad job dispatch of a processing task thanks to it's id
BEGIN RETURN query SELECT
    pt.nomad_job_id,
    njd.nomad_job_dispatch,
    njd.dispatch_date,
    njd.log_path
FROM hrwsi.processing_tasks pt
JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
WHERE pt.id = processing_task_id
ORDER BY njd.id DESC
LIMIT 1;
END $$ LANGUAGE plpgsql stable;

/*
Not used yet
*/
CREATE FUNCTION hrwsi.are_all_processing_tasks_in_vm_processed (vm_id uuid)
  RETURNS setof boolean AS $$
-- To be used to know if a virtual machine has processed all it's processing tasks
  BEGIN RETURN query SELECT  
      bool_and(is_processing_task_processed) 
      FROM 
      (
        SELECT pt.id AS task_id
        FROM hrwsi.processing_tasks pt 
        WHERE pt.virtual_machine_id = vm_id
      ) AS x, 
      hrwsi.is_processing_task_processed(task_id);
  END $$ LANGUAGE plpgsql stable;


CREATE FUNCTION hrwsi.get_preceding_processing_task (processing_task_id bigint)
    RETURNS setof hrwsi.processing_tasks AS $$
-- To be used to know the preceding processing task of a processing task 
-- thanks to it's id
-- This function is used in another function
    BEGIN RETURN query SELECT
        pt.id,
        pt.input_fk_id,
        pt.virtual_machine_id,
        pt.creation_date,
        pt.preceding_input_id,
        pt.nomad_job_id,
        pt.has_ended,
        pt.intermediate_files_path
    FROM hrwsi.processing_tasks pt,
    (
      SELECT pt.preceding_input_id AS piid
      FROM hrwsi.processing_tasks pt 
      WHERE pt.id = processing_task_id
    ) AS x
    WHERE pt.input_fk_id = piid;
    END $$ LANGUAGE plpgsql stable;


CREATE FUNCTION hrwsi.is_preceding_processing_task_processed (processing_task_id bigint)
  RETURNS setof boolean AS $$
-- To be used to know if the preceding processing task of a processing task is processed
-- This function is used in another function
  BEGIN RETURN query SELECT  
      is_processing_task_processed
      FROM 
      (
        SELECT id AS precedingid
        FROM hrwsi.get_preceding_processing_task(processing_task_id)
      ) AS x,
      hrwsi.is_processing_task_processed(precedingid);
  END $$ LANGUAGE plpgsql stable;


CREATE FUNCTION hrwsi.is_one_processing_task_processed_for_an_input (input_id bigint)
  RETURNS setof boolean AS $$
-- To be used to know if at least one processing task is processed for a given input
-- This function is used in another function
  BEGIN RETURN query SELECT  
      bool_or(is_processing_task_processed)
      FROM 
      (
        SELECT pt.id AS task_id
        FROM hrwsi.processing_tasks pt 
        WHERE pt.input_fk_id = input_id
      ) AS x, 
      hrwsi.is_processing_task_processed(task_id);
  END $$ LANGUAGE plpgsql stable;


CREATE FUNCTION hrwsi.are_all_processing_tasks_ended_for_an_input (input_id bigint)
  RETURNS boolean AS $$
-- To be used to know if all processing tasks of a given input are ended
-- This function is used in another function
  BEGIN 
    RETURN CASE WHEN EXISTS (
      SELECT
          id
      FROM hrwsi.get_processing_tasks_not_finished() 
      WHERE input_fk_id = input_id
    )
    THEN CAST(0 AS bit)
    WHEN EXISTS (
      SELECT
          id
      FROM hrwsi.processing_tasks 
      WHERE input_fk_id = input_id
    )
    THEN CAST(1 AS bit)
    ELSE CAST(0 AS bit)
    END CASE;
  END $$ LANGUAGE plpgsql stable;


CREATE FUNCTION hrwsi.get_ids_of_processing_tasks_ready_to_be_launched ()
    RETURNS setof bigint AS $$
-- To be used to get ids of processing tasks without Nomad job and with 
-- preceding task processed or null
-- The Launcher uses this function to know for which tasks he must create a nomad job
    BEGIN RETURN query SELECT
        pt.id 
        FROM hrwsi.processing_tasks pt 
        LEFT JOIN hrwsi.nomad_job_dispatch njd
        ON pt.id=njd.processing_task_fk_id
        WHERE pt.preceding_input_id is NULL AND njd.id is NULL
        UNION
        SELECT ptid 
        FROM 
        (
            SELECT pt.id AS ptid, pt.preceding_input_id AS ptpid, pt.nomad_job_id AS ptjid
            FROM hrwsi.processing_tasks pt
            LEFT JOIN hrwsi.nomad_job_dispatch njd
            ON pt.id=njd.processing_task_fk_id
            WHERE njd.id is NULL
        ) AS x, 
        hrwsi.is_preceding_processing_task_processed(ptid)
        WHERE is_preceding_processing_task_processed=true; 
    END $$ LANGUAGE plpgsql stable;


CREATE FUNCTION hrwsi.get_product_data_type_of_processing_tasks_not_ended ()
    RETURNS setof text AS $$
-- To be used to know if current processing tasks can give product which can become a new input
-- The Harvester uses this function : if all unfinished task gives products that can not become inputs, then it stops 
    BEGIN RETURN query SELECT DISTINCT 
        product_data_type 
        FROM 
        (
            SELECT pt.input_fk_id, pt.has_ended 
            FROM hrwsi.processing_tasks pt 
            WHERE pt.has_ended=false
        ) AS pt 
        INNER JOIN hrwsi.input i 
        ON pt.input_fk_id=i.id 
        INNER JOIN hrwsi.processing_condition pc 
        ON pc.name = i.processing_condition_name 
        INNER JOIN hrwsi.processing_routine pr 
        ON pr.name = pc.processing_routine_name;
    END $$ LANGUAGE plpgsql stable;


CREATE FUNCTION hrwsi.get_id_of_unprocessed_inputs_with_all_pt_ended (pt_creation_date timestamp)
    RETURNS setof bigint AS $$
-- To be used to give id of input with all processing tasks created since the date "pt_creation_date" 
-- ended but no one is processed.
-- Th Orchestrator uses this function to identify tasks that need to be planned
    BEGIN RETURN query SELECT 
        input_id 
        FROM 
        (
            SELECT pt.input_fk_id AS input_id 
            FROM hrwsi.processing_tasks pt 
            WHERE pt.has_ended=True
            AND pt.creation_date > pt_creation_date
        ) AS x,
        hrwsi.is_one_processing_task_processed_for_an_input(input_id), 
        hrwsi.are_all_processing_tasks_ended_for_an_input(input_id) 
        WHERE is_one_processing_task_processed_for_an_input = False 
        AND are_all_processing_tasks_ended_for_an_input = True;
    END $$ LANGUAGE plpgsql stable;