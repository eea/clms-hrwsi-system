----------------------------------
------------- INPUT --------------
----------------------------------

--- COLD TABLES ---
/*
Table for processing routines.
List the various type of processing routines used for the HR-WSI production.
Processing routines are defined by:
   - a name (str)
   - a number of CPUs (int)
   - a number of GB of RAM (int)
   - a number of GB of storage space (int)
   - a duration in minutes (int)
   - a Docker image name (str)
   - an input type (str)
   - a product data type (str)

The processing routines provide information about scientific softwares execution context.
*/
CREATE TABLE hrwsi.processing_routine (

    name text PRIMARY KEY,
    cpu smallint,
    ram smallint,
    storage_space smallint,
    duration smallint,
    docker_image text,
    input_type text,
    product_data_type text,
    product_type_code text
);
INSERT INTO hrwsi.processing_routine VALUES 
  ('MAJA', 5, 5, 5, 5, '', 'MSIL1C', 'L2A', 'S2_MAJA_L2A'), 
  ('FSC', 2, 2, 2, 2, '', 'L2A', 'L2B', 'S2_FSC_L2B');
  
/*
Table for processing condition types.
List the various type of processing conditions used for the HRWSI production.
Processing conditions are defined by:
   - a name
   - a processing routine name (see table processing_routine)
   - a description

Processing conditions define the conditions upon which processing routines
must be launched.
*/
CREATE TABLE hrwsi.processing_condition (

    name text PRIMARY KEY,
    processing_routine_name text REFERENCES hrwsi.processing_routine(name) not NULL,
    description text
);
INSERT INTO hrwsi.processing_condition VALUES -- Caution: values must be the same as in the input_type.py enum module.
  ('MAJA_PC', 'MAJA', 'Conditions to execute MAJA. We want an L1C image not already processed, with mesuration date in the last 30 days and publication date in the last 7 days.'), 
  ('FSC_PC', 'FSC', 'Conditions to calculate Fractional Snow Cover. We want an L2A image not already processed, with creation date in the last 7 days.');

--- CORE TABLES ---
/*
Table for the input met during the operation of the HRWSI production system.
List all the inputs ever met alongside their core informations.
Multiple inputs can refer to the same input_path if there processing condition or
tile are different.

It is a representation of the Input class in the Python code.
*/
CREATE TABLE hrwsi.input (

  id bigserial UNIQUE,
  processing_condition_name text REFERENCES hrwsi.processing_condition(name) NOT null,
  date timestamp NOT null,
  tile text NOT null,
  measurement_day bigint NOT null, -- origin date
  input_path text,
  mission text -- S2 / S1
);


--- FUNCTIONS ---

CREATE FUNCTION hrwsi.get_input_by_input_path (path text)
    RETURNS setof hrwsi.input AS $$
-- To be used when searching for the Inputs that were created mentionning a specific
-- file or directory.
BEGIN RETURN query SELECT
    i.id,
    i.processing_condition_name,
    i.date,
    i.tile,
    i.measurement_day,
    i.input_path,
    i.mission
FROM hrwsi.input i WHERE i.input_path = path;
END $$ LANGUAGE plpgsql stable;

CREATE FUNCTION hrwsi.get_input_by_measurement_day (day bigint)
    RETURNS setof hrwsi.input AS $$
-- To be used when searching for the Inputs that were created on data measured
-- on a specific day.
BEGIN RETURN query SELECT
    i.id,
    i.processing_condition_name,
    i.date,
    i.tile,
    i.measurement_day,
    i.input_path,
    i.mission
FROM hrwsi.input i WHERE i.measurement_day = day;
END $$ LANGUAGE plpgsql stable;

CREATE FUNCTION hrwsi.get_input_by_mission (miss text)
    RETURNS setof hrwsi.input AS $$
-- To be used when searching for the Inputs that were created on data measured
-- by a specific mission. Not to be used one the whole schema bu rather on another
-- function output.
BEGIN RETURN query SELECT
    i.id,
    i.processing_condition_name,
    i.date,
    i.tile,
    i.measurement_day,
    i.input_path,
    i.mission
FROM hrwsi.input i WHERE i.mission = miss;
END $$ LANGUAGE plpgsql stable;

CREATE FUNCTION hrwsi.get_input_by_input_type (in_type text)
    RETURNS setof hrwsi.input AS $$
-- To be used when searching for the Inputs of a specific input_type.
BEGIN RETURN query SELECT
    i.id,
    i.processing_condition_name,
    i.date,
    i.tile,
    i.measurement_day,
    i.input_path,
    i.mission
FROM hrwsi.input i 
INNER JOIN hrwsi.processing_condition pc
ON i.processing_condition_name = pc.name
INNER JOIN hrwsi.processing_routine pr
ON pr.name = pc.processing_routine_name
WHERE pr.input_type = in_type;
END $$ LANGUAGE plpgsql stable;

CREATE FUNCTION hrwsi.get_input_without_processing_task ()
    RETURNS setof hrwsi.input AS $$
-- To be used when searching for the Inputs that have not a processing task
-- allocated yet.
-- Refer to [2_init_database_processing_tasks.sql] about processing tasks.
BEGIN RETURN query SELECT
    i.id,
    i.processing_condition_name,
    i.date,
    i.tile,
    i.measurement_day,
    i.input_path,
    i.mission
FROM hrwsi.input i 
LEFT OUTER JOIN  hrwsi.processing_tasks pt ON i.id = pt.input_fk_id
WHERE pt.id IS NULL;
END $$ LANGUAGE plpgsql stable;