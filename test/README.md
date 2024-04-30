# Test

This directory included all the test of the code. We used **Pytest** to test our code.

**Pytest** is a framework for testing and checking whether the different conditions are right or wrong.

There are two ways to run the tests :

* In shell by using this command on top of the project :

```batch
python3 -m pytest
```

* In VSCode by following these instructions :

  * Install Python Extension :

    * On the left tool bar, search for Python on the extension search engine.
    * Open and install the Python extension found at the top of the search result.

  * Configure Pytest :

    * On the left tool bar, click the flask icon.
    * Click on "Configure Python Tests".
    * There are two options, choose "Pytest".
    * Select the folder that contains the test code.
    * Now you can see your tests, just click on the play icon to run the tests

Configuration of test directories follow the code configuration. Here is the detail of what each directory contain.

## HRWSI_System

This directory contain all the test about the system.

In this directory, we access on API, but the tests need to work even if the API connection doesn't. For this, we want to mock the functions who use API interactions. To use mocker,  it's necessary to install pytest-mock like that :

```batch
pip install pytest-mock
```

### Harvester

We find there the Harvester's tests.

We test :

* **identify_new_candidate** function who checks if candidate are already on database and returns only candidate who aren't.

* **create_tuple** function who create input tuple form to fit the database input.

* **check_running_processing_tasks_product_can_create_input** function who checks if running processing tasks product type can create input ie are in the input type list.

### Launcher

We find there the Harvester's tests.

We test the following function :

* **check_all_processing_tasks_has_not_ended**, who checks if all the processing tasks are finished.

### Orchestrator

We find there the Orchestrator’s tests.

We test one function in each file : **plan**, **check_plan** and **check_feasibility** :

* **plan** planned all the Processing_task as fast as possible with a minimal resources.

* **check_plan** verify that the plan respect dependency, limit resources and plan all Processing_task once.

* **check_feasibility** verify that the Processing_routine are feasable with the limit materials resources and all Processing_task can be planned in limit time.

We can find the details of the behaviour of each function [here](https://docs.google.com/document/d/1wFyunvr8BNWvSiJscfk7o_9oxOPS0iXNCAQG-vJrO24/edit?usp=sharing).

We also test **identify_new_processing_task_in_database** who checks if we can add processing tasks candidates in database or not. We can add it if :

* the input associated to the processing_task doesn't already have processing task, or,

* all the processing_tasks of the input associated are ended and no one is processed.
