----------------------------------
----- PROCESSING TASKS -----------
----------------------------------

--- COLD TABLES ---
/*
TABLE FOR THE PROCESSING TASK TYPES.
List all types of processing tasks. 
*/
CREATE TABLE hrwsi.processing_task_type (

    id bigserial UNIQUE,
    name text NOT null UNIQUE,
    description text
);
INSERT INTO hrwsi.processing_task_type VALUES -- Caution: values must be the same as in the processing_task_type.py enum module.
  (1, 'CM_PT', ''),
  (2, 'FSC_PT', ''),
  (3, 'WIC_S2_PT', ''),
  (4, 'WIC_S1_PT', ''),
  (5, 'SWS_TPT', ''),
  (6, 'WDS_PT', ''),
  (7, 'GFSC_PT', ''),
  (8, 'WIC_S1_S2_PT', '');


/*
TABLE FOR THE PRIORITY LEVELS.
List all priority levels that can be affected to processing tasks in production.
*/
CREATE TABLE hrwsi.priority_level (

  id smallint PRIMARY KEY,
  name text NOT null UNIQUE,
  description text
);
INSERT INTO hrwsi.priority_level VALUES
  (1, 'nrt', '');

/*
TABLE FOR THE PROCESSING MODE TYPES.
List all processing mode types that can be used by scientific algorithms in production.
*/
CREATE TABLE hrwsi.processing_mode_type (

  id smallint PRIMARY KEY,
  name text NOT null UNIQUE,
  description text
);
INSERT INTO hrwsi.processing_mode_type VALUES
  (1, 'maja_init', ''),
  (2, 'maja_nominal', '');

/*
TABLE FOR THE PROCESSING STATUS CODES.
List all processing status code that describe the evolution of the processing tasks.
*/
CREATE TABLE hrwsi.processing_status (

  id smallint PRIMARY KEY,
  code bigint NOT null UNIQUE,
  name text NOT null UNIQUE,
  description text
);
INSERT INTO hrwsi.processing_status VALUES
  (1, 0, 'processed', ''),
  (2, 1, 'started', ''),
  (3, 110, 'internal_error', ''),
  (4, 210, 'external_error', '');

--- CORE TABLES ---
/*
TABLE FOR THE PROCESSING TASKS.
List all the processing tasks, linked to a triggering condition, with all the informations needed.
*/
CREATE TABLE hrwsi.processing_tasks (

  id bigserial UNIQUE,
  triggering_condition_fk_id bigserial REFERENCES hrwsi.triggering_conditions(id) ON DELETE CASCADE,
  processing_task_type_id smallint REFERENCES hrwsi.processing_task_type(id) NOT null,
  creation_date timestamp NOT null,
  nomad_job_id uuid,
  has_ended boolean,
  processing_mode_id smallint REFERENCES hrwsi.processing_mode_type(id),
  intermediate_files_path text,
  priority_id smallint REFERENCES hrwsi.priority_level(id)
);

/*
TABLE FOR NOMAD JOB DISPATCH.
List all nomad job dispatch, linked to the processing task corresponding.
*/
CREATE TABLE hrwsi.nomad_job_dispatch (

  id bigserial UNIQUE,
  processing_task_fk_id bigserial REFERENCES hrwsi.processing_tasks(id) ON DELETE CASCADE NOT null,
  nomad_job_dispatch text NOT null,
  dispatch_date timestamp NOT null,
  log_path text
);

/*
TABLE FOR THE PROCESSING STATUS.
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
*/
CREATE FUNCTION hrwsi.get_number_of_error_statuses_by_processing_task (processing_task_id bigint)
  RETURNS bigint AS $$
  
  declare 
    error_statuses_number bigint;

  BEGIN 
    SELECT COUNT(psw.id) INTO error_statuses_number
    FROM hrwsi.processing_tasks pt
    INNER JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
    INNER JOIN hrwsi.processing_status_workflow psw ON psw.nomad_job_dispatch_fk_id = njd.id
    WHERE pt.id = processing_task_id
    AND psw.processing_status_id = 3;

    RETURN error_statuses_number;
  END $$ LANGUAGE plpgsql stable;

/*
*/
CREATE FUNCTION hrwsi.is_processing_tasks_processed (processing_task_id bigint)
  RETURNS boolean AS $$

  BEGIN 
    RETURN CASE WHEN EXISTS (
      SELECT
          pt.id
      FROM hrwsi.processing_tasks pt
      INNER JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
      INNER JOIN hrwsi.processing_status_workflow psw ON psw.nomad_job_dispatch_fk_id = njd.id
      WHERE psw.processing_status_id = 1
      AND pt.id = processing_task_id
    )
    THEN CAST(1 AS bit)
    ELSE CAST(0 AS bit)
    END CASE;
  END $$ LANGUAGE plpgsql stable;

/*
*/
CREATE FUNCTION hrwsi.get_processing_tasks_not_finished ()
    RETURNS setof hrwsi.processing_tasks AS $$
BEGIN RETURN query SELECT
    pt.id,
    pt.triggering_condition_fk_id,
    pt.processing_task_type_id,
    pt.creation_date,
    pt.nomad_job_id,
    pt.has_ended,
    pt.processing_mode_id,
    pt.intermediate_files_path,
    pt.priority_id
FROM hrwsi.processing_tasks pt
WHERE pt.has_ended = False;
END $$ LANGUAGE plpgsql stable;

/*
*/
CREATE FUNCTION hrwsi.get_status_history_by_processing_task_id (processing_task_id bigint)
    RETURNS setof hrwsi.processing_status_history AS $$
BEGIN RETURN query SELECT
    psw.id,
    psw.date,
    ps.code,
    ps.name,
    psw.message
FROM hrwsi.nomad_job_dispatch njd
INNER JOIN hrwsi.processing_status_workflow psw ON psw.nomad_job_dispatch_fk_id = njd.id
INNER JOIN hrwsi.processing_status ps ON ps.id = psw.processing_status_id
WHERE njd.processing_task_fk_id = processing_task_id;
END $$ LANGUAGE plpgsql stable;

/*
*/
CREATE FUNCTION hrwsi.get_nomad_job_dispatch_list_by_processing_task_id (processing_task_id bigint)
    RETURNS setof hrwsi.nomad_job_dispatch_info AS $$
BEGIN RETURN query SELECT
    pt.nomad_job_id,
    njd.nomad_job_dispatch,
    njd.dispatch_date,
    njd.log_path
FROM hrwsi.processing_tasks pt
INNER JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
WHERE pt.id = processing_task_id;
END $$ LANGUAGE plpgsql stable;

/*
*/
CREATE FUNCTION hrwsi.get_current_nomad_job_dispatch_by_processing_task_id (processing_task_id bigint)
    RETURNS setof hrwsi.nomad_job_dispatch_info AS $$
BEGIN RETURN query SELECT
    pt.nomad_job_id,
    njd.nomad_job_dispatch,
    njd.dispatch_date,
    njd.log_path
FROM hrwsi.processing_tasks pt
INNER JOIN hrwsi.nomad_job_dispatch njd ON njd.processing_task_fk_id = pt.id
WHERE pt.id = processing_task_id
ORDER BY njd.id DESC
LIMIT 1;
END $$ LANGUAGE plpgsql stable;