# Artificial Data For Database

This folder contains the following scripts to create artificial data in HRWSI Database:

- *[create_input.py](create_input.py)* : To create data in HRWSI Database input table. The data contains a random creation_date between a start_date and an end_date. The tile names are randomly selected from the tile_list of the configuration file. The configuration file also allows you to specify the amount of each type of input you want to create.

- *[create_products.py](create_products.py)* : To create data in HRWSI Database products table. The data created are the product of all the input with a measruement_day between start_day_input end end_day_input. In the configuration file, we fix a process time to create the products at the inpute date + process time.
