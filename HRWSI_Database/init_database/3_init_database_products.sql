----------------------------------
----- PRODUCTS -------------------
----------------------------------

--- COLD TABLES ---
/*
Table for the product type.
List all product types.
*/
CREATE TABLE hrwsi.product_type (

  id bigserial UNIQUE,
  code text NOT null UNIQUE,
  name text NOT null UNIQUE,
  data_type text,
  description text
);
INSERT INTO hrwsi.product_type VALUES
  (1, 'S2_MAJA_L2A', 'Sentinel-2 MAJA computation of Sentinel-2-like images L2A', 'L2A', ''),
  (2, 'S2_FSC_L2B', 'Fractional Snow Cover L2B', 'L2B', '');
/*
Table for the indexation failure types.
List all types of indexation failure that can be encountered by the publication.
*/
CREATE TABLE hrwsi.indexation_failure_type (
  id smallint PRIMARY KEY,
  code bigint NOT null UNIQUE,
  name text NOT null UNIQUE,
  description text
);
INSERT INTO hrwsi.indexation_failure_type VALUES
  (1, 110, 'error_failed_publication', ''),
  (2, 120, 'error_publication_max_retry', ''),
  (3, 130, 'error_timeout_indexation', '');

/*
Table for the indexation file types.
List all types of indexation files that can be used by the publication.
*/
CREATE TABLE hrwsi.indexation_file_type (
    id smallint PRIMARY KEY,
    name text NOT null UNIQUE,
    description text
);
INSERT INTO hrwsi.indexation_file_type VALUES
    (1, 'INSPIRE', '');

--- CORE TABLES ---
/*
Table for the products.
List all products, from processing tasks that generated products, linked to a triggering condition entry.
*/
CREATE TABLE hrwsi.products (
  
  id bigserial UNIQUE,
  input_fk_id bigserial REFERENCES hrwsi.input(id) ON DELETE CASCADE NOT null,
  product_path text NOT null UNIQUE,
  creation_date timestamp NOT null,
  catalogued_date timestamp NOT null,
  kpi_file_path text,
  product_type_id smallint REFERENCES hrwsi.product_type(id) NOT null
);

/*
Table for the indexation jsons.
List all indexation files generated, and link them to the products they indexed.
*/
CREATE TABLE hrwsi.indexation_json (

  id bigserial UNIQUE,
  product_fk_id bigserial REFERENCES hrwsi.products(id) ON DELETE CASCADE NOT null,
  indexation_file_type_id smallint REFERENCES hrwsi.indexation_file_type(id),
  path text NOT null UNIQUE
);

/*
Table for the indexation workflows.
List all tries of indexation, be it successfull or not, linked to the product that is to be indexed.
*/
CREATE TABLE hrwsi.indexation_workflow (

  id bigserial UNIQUE,
  product_fk_id bigserial REFERENCES hrwsi.products(id) ON DELETE CASCADE NOT null,
  publication_date timestamp NOT null,
  indexation_date timestamp,
  failure_date timestamp,
  indexation_failure_type_id smallint REFERENCES hrwsi.indexation_failure_type(id)
);

--- FUNCTIONS ---

/*
Not used because indexation is not yet implemented
*/
CREATE FUNCTION hrwsi.is_product_indexed (product_id bigint)
    RETURNS boolean AS $$
  BEGIN 
    RETURN CASE WHEN EXISTS (
      SELECT iw.id
      FROM hrwsi.indexation_workflow iw
      WHERE iw.product_fk_id = product_id
      AND iw.indexation_date IS NOT NULL
    )
    THEN CAST(1 AS bit)
    ELSE CAST(0 AS bit)
    END CASE;
  END $$ LANGUAGE plpgsql stable;

/*
Not used because indexation is not yet implemented
*/
CREATE FUNCTION hrwsi.is_product_indexation_currently_failed (product_id bigint)
    RETURNS boolean AS $$
  BEGIN 
    RETURN CASE WHEN EXISTS (
      SELECT intermediate_iw.id
      FROM (
          SELECT iw.id, iw.failure_date 
          FROM hrwsi.indexation_workflow iw
          WHERE iw.product_fk_id = product_id
          ORDER BY iw.id DESC
          LIMIT 1
      ) AS intermediate_iw
      WHERE intermediate_iw.failure_date IS NOT NULL
    )
    THEN CAST(1 AS bit)
    ELSE CAST(0 AS bit)
    END CASE;
  END $$ LANGUAGE plpgsql stable;

/*
Not used because indexation is not yet implemented
*/
CREATE FUNCTION hrwsi.get_indexation_file_path_by_type_name_by_product_id (
    type_name text, product_id bigint
)
  RETURNS text AS $$

  declare
    path text;

  BEGIN 
    SELECT ij.path INTO path
    FROM hrwsi.indexation_json ij
    JOIN hrwsi.products p ON p.id = ij.product_fk_id
    JOIN hrwsi.indexation_file_type ift ON ift.id = ij.indexation_file_type_id
    WHERE p.id = product_id
    AND ift.name = type_name;

    RETURN path;
  END $$ LANGUAGE plpgsql stable;