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