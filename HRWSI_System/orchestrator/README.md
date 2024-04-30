# Orchestrator

This directory contains the code of the Orchestrator.

The goal of the Orchestrator is to plan all processing_tasks in a given time using the fewest hardware resources needed. It has to respect all the resources limitations : CPU, RAM, Storage_Space and VM.

At the end, the Orchestrator give a plan with the number of VM needed, their id, creation and destruction time and all the processing_tasks to processed on a machine.

We can find the UML of the Orchestrator [here](https://drive.google.com/file/d/1193-_3y2BQRZSmj2IKnt0lmGALMyZTZL/view?usp=sharing).

## Directory structure

- *[orchestrator_exceptions](orchestrator_exceptions)* : It contains all the personalized exceptions for the Orchestrator.

- *[processing_routine](processing_routine)* : Defines a processing routine with the resources required for processing.

- *[processing_task](processing_task)* : Defines a processing task with it's dependency, the routine associated and the start time.

- *[scheduler](scheduler)* : Schedules processing tasks and provide the resulting plan to the Worker Pool Manager.

- The *[Orchestrator](orchestrator.py)* interact between the HRWSI Database and the Scheduler. It collect non processed inputs in HRWSI Database, transform inputs in Orchestrator's object and plan them. Then, it convert the plan in HRWSI Database processing tasks and add them in Database.
