# System

This section talks about the system of the project.

There are several parts:

* *[harvester](HRWSI_System/harvester)* : Feed the HRWSI Database by adding input. The input can come from the WEkEO API or the products table in HRWSI Database.

* *[orchestrator](HRWSI_System/orchestrator)* : Plan all processing_tasks in a given time using the fewest hardware resources needed. It has to respect all the resources limitations : CPU, RAM, Storage_Space and VM.

* *[launcher](HRWSI_System/launcher)* : Create and associate Nomad job to processing_tasks ready to launch. A Processing tasks is ready to launch if it's preceding task is processed or null and associate Nomad job doesn't already exist.

We can find the worflows implemented in each part [here](https://drive.google.com/file/d/1NPsXPyxxbMGhp2h9znj8G9Fyh9r1y_rq/view?usp=sharing).

## Database changes in real time

To implement these workflows, we need to be notify of Database changes in real time.

### How capture Database changes in real time ?

For that, we use redacted triggers, notify, and listen :

* redacted triggers are essentially callbacks at the database level that can execute a defined function before, after, or instead of identified operations (i.e., INSERT, UPDATE, DELETE), on the table(s) you specify. This supports the recognition and capture of changed data.

* Notify and listen functions allow you to implement a notification message system where there is a message that is broadcast and a listener running to receive the message :

  * NOTIFY broadcasts a notification event with a defined payload string through defined channels

  * LISTEN establishes sessions on defined channels to capture notifications sent on those channels

With all this utils, we can build a data syncing system that captures changes made to data in real time and delivers those changes to the code that contains the business logic for managing system integrations.

#### Use Notify and Listen

There are two ways to use Notify in PostgreSQL (see [the documentation](https://www.postgresql.org/docs/current/sql-notify.html)) :

* ```sql
  NOTIFY channel [ , payload ]
  ```

* ```sql
  pg_notify(channel, payload)
  ```

This two commands send a notification event together with an optional “payload” string to each client application that has previously executed LISTEN channel for the specified channel name in the current database. Notifications are visible to all users.

For Listen ([documentation here](https://www.postgresql.org/docs/current/sql-listen.html)), the command to register the current session as a listener on the notification channel named channel :

```sql
LISTEN channel
```

#### Create trigger

The [PostgreSQL documentation to create trigger](https://www.postgresql.org/docs/current/sql-createtrigger.html) describe the creation like that :

```sql
CREATE [ OR REPLACE ] [ CONSTRAINT ] TRIGGER name { BEFORE | AFTER | INSTEAD OF } { event [ OR ... ] }
    ON table_name
    [ FROM referenced_table_name ]
    [ NOT DEFERRABLE | [ DEFERRABLE ] [ INITIALLY IMMEDIATE | INITIALLY DEFERRED ] ]
    [ REFERENCING { { OLD | NEW } TABLE [ AS ] transition_relation_name } [ ... ] ]
    [ FOR [ EACH ] { ROW | STATEMENT } ]
    [ WHEN ( condition ) ]
    EXECUTE { FUNCTION | PROCEDURE } function_name ( arguments )

where event can be one of:

    INSERT
    UPDATE [ OF column_name [, ... ] ]
    DELETE
    TRUNCATE
```

Therefore, to create a trigger who execute a function after insertion in our input table, we write that :

```sql
CREATE OR REPLACE TRIGGER new_trigger 
AFTER INSERT ON hrwsi.input
REFERENCING NEW TABLE AS new_table 
FOR EACH STATEMENT EXECUTE FUNCTION function_name();
```

As we can see, we used **FOR EACH STATEMENT** to execute the function only after the end of a transaction who insert rows in input table. Contrariwise, **FOR EACH ROW** execute the function after each insertion in input table and you can access to the row information by using **NEW** in the executing function. But, using **FOR EACH STATEMENT** need to add **REFERENCING NEW TABLE AS new_table** if you need to access to the informations of the rows insert in the table in the function *function_name()*.

The following example is a trigger who sent notification after insert rows in input table and the associated function :

```sql
CREATE OR REPLACE TRIGGER notify_input_trigger 
AFTER INSERT ON hrwsi.input 
REFERENCING NEW TABLE AS new_table 
FOR EACH STATEMENT EXECUTE FUNCTION notify_trigger();
```

```sql
CREATE OR REPLACE function notify_trigger()
RETURNS trigger as $$
BEGIN
  perform pg_notify('input_table_change', 'Input insertion')
  FROM new_table;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

The function *notify_trigger()* sent a notification on the 'input_table_chane' channel with the message "Input insertion"

### Asynchronous programming

We use asynchronus programming in python code to listen database notification. For that, we used the **asyncio** and the **nest_asyncio** library.

The **asyncio** module provides infrastructure for writing single-threaded concurrent code using coroutines, multiplexing I/O access over sockets and other resources, running network clients and servers, and other related primitives. The installation is done with:

```batch
asyncio_version=3.4.3
pip install asyncio==${asyncio_version}
```

**nest_asyncio** solve the “RuntimeError: This event loop is already running” of the **asyncio** module. Indeed, by design **asyncio** does not allow its event loop to be nested. This presents a practical problem: When in an environment where the event loop is already running it’s impossible to run tasks and wait for the result. Trying to do so will give the RuntimeError. The installation is done with:

```batch
nest_asyncio_version=1.5.8
pip install nest_asyncio==${nest_asyncio_version}
```

Thanks to **asyncio**, we can listen to database notification and execute task in the background ([documentation](https://docs.python.org/3/library/asyncio.html)).

To use **asyncio**, we have to create a loop :

```python
loop = asyncio.get_event_loop()
```

Then, add the connexion to database with the listener on and a function to execute when a notification pop :

```python
loop.add_reader(connexion, function, *args)
```

Create a task in the loop :

```python
task = loop.create_task(coroutine)
```

A coroutine is a function that can be suspended and resumed. It's defined with the keyword "async" and it can used awaitable object in an await expression. Awaitable objects are coroutines, Tasks, and Futures.

* Python coroutines are awaitables and therefore can be awaited from other coroutines.

* Tasks are used to schedule coroutines concurrently. When a coroutine is wrapped into a Task with functions like asyncio.create_task() the coroutine is automatically scheduled to run soon.

* A Future is a special low-level awaitable object that represents an eventual result of an asynchronous operation. When a Future object is awaited it means that the coroutine will wait until the Future is resolved in some other place.

Here is a coroutine example :

```python
async def main():
    task1 = asyncio.create_task(
        say_after(1, 'hello'))

    task2 = asyncio.create_task(
        say_after(2, 'world'))

    # Wait until both tasks are completed
    await task1
    await task2
```

To run and close the loop we execute that :

```python
try:
    loop.run_forever() # To execute the loop forever until interruption
# When keyboard interruption occurs
except KeyboardInterrupt:
    pass
finally:
    # Cancel task
    task.cancel()
    loop.run_until_complete(loop.shutdown_asyncgens())
    # Ended the loop
    loop.close()
```
