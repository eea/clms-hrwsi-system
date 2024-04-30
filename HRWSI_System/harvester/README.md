# Harvester

This directory contains the code of the Harvester.

The goal of the Harvester is to feed the HRWSI Database by adding inputs. The inputs can come from the WEkEO API or the products table in HRWSI Database.

We can find the UML of the Harvester [here](https://drive.google.com/file/d/1AiwxOcTdKEEIYtjpkgF11U4H3tqJ_8Qy/view?usp=sharing).

## Directory structure

- *[apimanager](apimanager)* : In the apimanager directory, we find all the interaction process with the two API : WEkEO and HRWSI Database.

- The *[Harvester](harvester.py)* processes the data extracted from the two APIs, checks that the data is not already in the HRWSI database before adding them in the input table.

## Library

We use the **requests** library to interact with the WEkEO API and the **psycopg2** library to interact with the HRWSI Database.

**requests** is a python module to use the http protocol in a very simple way. The version use is the 2.13.1. The installation is done with:

```batch
requests_version=2.13.0
pip install requests==${requests_version}
```

**psycopg2** is a PostgreSQL database adapter for the Python programming language. The version use is the 2.9.9. The installation is done with:

```batch
psycopg2_version=2.9.9
pip install psycopg2_binary==${psycopg2_version}
```
