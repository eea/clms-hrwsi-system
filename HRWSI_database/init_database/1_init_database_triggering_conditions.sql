----------------------------------
----- TRIGGERING CONDITIONS ------
----------------------------------

--- COLD TABLES ---
/*
TABLE FOR TRIGGERING CONDITION TYPES.
List the various type of triggering conditions used for the NRT production.
*/
CREATE TABLE hrwsi.triggering_condition_type (

    id bigserial UNIQUE,
    name text NOT null UNIQUE,
    description text
);
INSERT INTO hrwsi.triggering_condition_type VALUES -- Caution: values must be the same as in the triggering_conditions_type.py enum module.
  (1, 'CM_TC', ''),
  (2, 'FSC_TC', ''),
  (3, 'WIC_S2_TC', ''),
  (4, 'WIC_S1_TC', ''),
  (5, 'SWS_TC', ''),
  (6, 'WDS_TC', ''),
  (7, 'GFSC_TC_1', ''),
  (8, 'GFSC_TC_2', ''),
  (9, 'WIC_S1_S2_TC_1', ''),
  (10, 'WIC_S1_S2_TC_2', '');


--- CORE TABLES ---
/*
TABLE FOR THE TRIGGERING CONDITIONS MET DURING THE OPERATION OF HRWSI SYSTEM.
List all the occurences of triggering conditions met, with core informations about these occurences.
*/
CREATE TABLE hrwsi.triggering_conditions (
  id bigserial UNIQUE,
  triggering_condition_type_id smallint REFERENCES hrwsi.triggering_condition_type(id) NOT null,
  date timestamp NOT null,
  tile text NOT null,
  measurement_day bigint NOT null,
  triggering_product_path text
);


--- FUNCTIONS ---

CREATE FUNCTION hrwsi.get_triggering_conditions_by_triggering_product_path (path text)
    RETURNS setof hrwsi.triggering_conditions AS $$
BEGIN RETURN query SELECT
    tc.id,
    tc.triggering_condition_type_id,
    tc.date,
    tc.tile,
    tc.measurement_day,
    tc.triggering_product_path
FROM hrwsi.triggering_conditions tc WHERE tc.triggering_product_path = path;
END $$ LANGUAGE plpgsql stable;

CREATE FUNCTION hrwsi.get_triggering_conditions_by_measurement_day (day bigint)
    RETURNS setof hrwsi.triggering_conditions AS $$
BEGIN RETURN query SELECT
    tc.id,
    tc.triggering_condition_type_id,
    tc.date,
    tc.tile,
    tc.measurement_day,
    tc.triggering_product_path
FROM hrwsi.triggering_conditions tc WHERE tc.measurement_day = day;
END $$ LANGUAGE plpgsql stable;

CREATE FUNCTION hrwsi.get_triggering_conditions_without_processing_task ()
    RETURNS setof hrwsi.triggering_conditions AS $$
BEGIN RETURN query SELECT
    tc.id,
    tc.triggering_condition_type_id,
    tc.date,
    tc.tile,
    tc.measurement_day,
    tc.triggering_product_path
FROM hrwsi.triggering_conditions tc 
LEFT OUTER JOIN  hrwsi.processing_tasks pt ON tc.id = pt.triggering_condition_fk_id
WHERE pt.id IS NULL;
END $$ LANGUAGE plpgsql stable;