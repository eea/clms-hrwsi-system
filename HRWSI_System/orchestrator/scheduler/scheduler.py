#!/usr/bin/env python3
"""
Scheduler module is used to schedule processing tasks and to provide the resulting plan to the
Worker Pool Manager.
"""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

import json
import logging
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from utils.logger import LogUtil
from HRWSI_System.orchestrator.scheduler.encoder import Encoder
from HRWSI_System.orchestrator.processing_task.processing_task import ProcessingTask
from HRWSI_System.orchestrator.orchestrator_exceptions.impossible_plan import ImpossiblePlan
from HRWSI_System.orchestrator.orchestrator_exceptions.false_plan import FalsePlan

class Scheduler():
    """Schedule processing tasks"""

    LOGGER_LEVEL = logging.DEBUG

    def __init__(self, t_max: int,
                 cpu_max: int,
                 ram_max: int,
                 storage_space_max: int,
                 vm_max: int,
                 task_list: list[ProcessingTask],
                 json_path: str = None
                 ):

        self.t_max = t_max
        self.cpu_max = cpu_max
        self.ram_max = ram_max
        self.storage_space_max = storage_space_max
        self.vm_max = vm_max
        self.task_list = task_list
        self.json_path = json_path
        self.attribution_plan = None
        self.logger = LogUtil.get_logger('Log_scheduler', self.LOGGER_LEVEL, "log_scheduler/logs.log")

    def plan(self) -> None:
        """Set t0 of tasks in task_list"""
        raise NotImplementedError

    def export_to_json(self) -> None:
        """Writes plan to json file"""
        self.logger.info("Begin export to json")

        try :
            assert self.json_path is not None
        except AssertionError:
            self.logger.error("No json_path provided")
            self.json_path = "plan.json"

        with open(self.json_path, "w", encoding='UTF-8') as f:
            json.dump(self.attribution_plan, f, cls=Encoder, indent=2)

        self.logger.info("End export to json")

    def check_plan(self) -> bool:
        """Calls all checking fonctions"""

        self.logger.info("Begin check plan")

        # Dico of {task_id : task}
        task_by_id={}
        for task in self.task_list:
            task_by_id[task.task_id] = task

        # List of resources
        cpu_per_time=[0 for i in range(self.t_max)]
        ram_per_time=[0 for i in range(self.t_max)]
        storage_space_per_time=[0 for i in range(self.t_max)]
        vm_per_time=[0 for i in range(self.t_max)]

        for task in self.task_list:

            # Unplanned task
            if task.t0 is None:
                self.logger.critical("Task %s is unplanned", task.task_id)
                raise FalsePlan("Incomplete plan")

            # Task begin before starting time
            if task.t0 < 0:
                self.logger.critical("Task %s begin before starting time", task.task_id)
                raise FalsePlan("Task begin before starting time")

            # Task end after t_max
            if task.t0 + task.processing_routine.duration > self.t_max:
                self.logger.critical("Task %s end after t_max", task.task_id)
                raise FalsePlan("Task end after t_max")

            # Verification of dependency
            if task.depends_on is not None :
                for task_depend_id in task.depends_on:
                    if task.t0 < task_by_id[task_depend_id].t0 + task_by_id[task_depend_id].processing_routine.duration :
                        self.logger.critical("Task %s begin before the end of it's dependency (task %s)", task.task_id, task_by_id[task_depend_id].task_id)
                        raise FalsePlan("No respect of dependency")

            # Add resources
            cpu_per_time[task.t0:task.t0+task.processing_routine.duration] = [i + task.processing_routine.cpu for i in cpu_per_time[task.t0:task.t0+task.processing_routine.duration]]
            ram_per_time[task.t0:task.t0+task.processing_routine.duration] = [i + task.processing_routine.ram for i in ram_per_time[task.t0:task.t0+task.processing_routine.duration]]
            storage_space_per_time[task.t0:task.t0+task.processing_routine.duration] = [i + task.processing_routine.storage_space for i in storage_space_per_time[task.t0:task.t0+task.processing_routine.duration]]
            vm_per_time[task.t0:task.t0+task.processing_routine.duration] = [i + 1 for i in vm_per_time[task.t0:task.t0+task.processing_routine.duration]]

        # Check resources
        for time in range(self.t_max):
            if cpu_per_time[time] > self.cpu_max:
                self.logger.critical("CPU exceed the limit at %s", time)
                raise FalsePlan("No respect of CPU limit")
            if ram_per_time[time] > self.ram_max:
                self.logger.critical("RAM exceed the limit at %s", time)
                raise FalsePlan("No respect of RAM limit")
            if storage_space_per_time[time] > self.storage_space_max:
                self.logger.critical("Storage Space exceed the limit at %s", time)
                raise FalsePlan("No respect of Storage Space limit")
            if vm_per_time[time] > self.vm_max:
                self.logger.critical("VM exceed the limit at %s", time)
                raise FalsePlan("No respect of VM limit")

        # Check attribution_plan
        if self.attribution_plan is not None:

            # Check task planned only once
            sum_task_planned = 0
            for worker in self.attribution_plan:
                sum_task_planned += len(self.attribution_plan[worker][4])
            if sum_task_planned > len(self.task_list):
                self.logger.critical("Task are planned more than one time in attribution plan")
                raise FalsePlan("Task over planification")

            # No task overlap in attribute_plan
            for worker in self.attribution_plan:
                self.attribution_plan[worker][4].sort(key=lambda x: x.t0)
                for i in range(len(self.attribution_plan[worker][4])-1):
                    task_i = self.attribution_plan[worker][4][i]
                    task_j = self.attribution_plan[worker][4][i+1]
                    if task_i.t0 + task_i.processing_routine.duration > task_j.t0 :
                        self.logger.critical("There is a task overlape in worker %s in attribution plan", worker)
                        raise FalsePlan("Task overlap")

        self.logger.info("End check plan")
        return True

    def check_feasibility(self) -> bool:
        """Checks whether the plan can be made"""

        self.logger.info("Begin check feasibility")

        nb_task_for_each_routine = {}
        info_routine=[]
        for task in self.task_list:

            # Check limit of meterials resources
            if task.processing_routine.name not in nb_task_for_each_routine:
                nb_task_for_each_routine[task.processing_routine.name] = 1
                info_routine.append((task.processing_routine))
                if task.processing_routine.cpu > self.cpu_max:
                    self.logger.critical("Routine %s requires more CPU than the limit", task.processing_routine.name)
                    raise ImpossiblePlan("Not enough CPU")
                if task.processing_routine.ram > self.ram_max:
                    self.logger.critical("Routine %s requires more RAM than the limit", task.processing_routine.name)
                    raise ImpossiblePlan("Not enough RAM")
                if task.processing_routine.storage_space > self.storage_space_max :
                    self.logger.critical("Routine %s requires more Storage space than the limit", task.processing_routine.name)
                    raise ImpossiblePlan("Not enough Storage Space")
                if self.vm_max == 0 :
                    self.logger.critical("VM max is equal to 0")
                    raise ImpossiblePlan("Not enough VM")
            else:
                nb_task_for_each_routine[task.processing_routine.name] += 1

        # Check limit of time
        list_time_min = [np.ceil((nb_task_for_each_routine[routine] /
                                 min(self.cpu_max // info_routine[i].cpu,
                                        self.ram_max // info_routine[i].ram,
                                        self.storage_space_max // info_routine[i].storage_space,
                                        self.vm_max))) * info_routine[i].duration for i, routine in enumerate(nb_task_for_each_routine)]
        time_min = sum(list_time_min)

        if time_min > self.t_max:
            self.logger.critical("Time required (%s) is greater than the time limit", time_min)
            raise ImpossiblePlan(f"Not enough time, t_max >= {time_min}")

        self.logger.info("End check feasibility")
        return True

    def visualization(self) -> None:
        """Prints plan"""

        self.logger.info("Begin visualization")

        # Initialize figures
        plt.figure()
        ax1 = plt.subplot2grid((8, 3), (0, 0), rowspan=4, colspan=3)
        ax2 = plt.subplot2grid((8, 3), (4, 0), colspan=3)
        ax3 = plt.subplot2grid((8, 3), (5, 0), colspan=3)
        ax4 = plt.subplot2grid((8, 3), (6, 0), colspan=3)
        ax5 = plt.subplot2grid((8, 3), (7, 0), colspan=3)
        ax1.grid(True)
        ax1.set_xticklabels([])
        ax2.set_xticklabels([])
        ax3.set_xticklabels([])
        ax4.set_xticklabels([])

        # Set information
        ax1.set_title(f"Solution with time = {self.t_max}")
        ax1.set_yticks(np.arange(len(self.attribution_plan)))
        ax1.set_yticklabels([keys for keys in self.attribution_plan.keys()])
        ax1.set_xlim(0, self.t_max)

        nb_routine = len(set([task.processing_routine.name for task in self.task_list]))
        self.logger.info("Nb of routine : %s", nb_routine)
        colors = sns.color_palette("magma", self.vm_max)

        # Create task in the figure
        color_dico = {}
        n = 0
        for i, key in enumerate(self.attribution_plan):
            for job in self.attribution_plan[key][4]:
                if job.processing_routine.name not in color_dico:
                    color_dico[job.processing_routine.name] = n
                    n += 1
                ax1.barh([i], [job.processing_routine.duration], left=[job.t0], height=0.5, align='center', color=colors[color_dico[job.processing_routine.name]])

        # Creation of resources list
        ram_per_time = [0 for i in range(self.t_max)]
        storage_space_per_time = [0 for i in range(self.t_max)]
        vm_per_time = [0 for i in range(self.t_max)]
        cpu_per_time = [0 for i in range(self.t_max)]

        for i, key in enumerate(self.attribution_plan):
            for job in self.attribution_plan[key][4]:
                ram_per_time[job.t0:job.t0+job.processing_routine.duration] = [l + job.processing_routine.ram for l in ram_per_time[job.t0:job.t0+job.processing_routine.duration]]
                storage_space_per_time[job.t0:job.t0+job.processing_routine.duration] = [l + job.processing_routine.storage_space for l in storage_space_per_time[job.t0:job.t0+job.processing_routine.duration]]
                vm_per_time[job.t0:job.t0+job.processing_routine.duration] = [l + 1 for l in vm_per_time[job.t0:job.t0+job.processing_routine.duration]]
                cpu_per_time[job.t0:job.t0+job.processing_routine.duration] = [l + job.processing_routine.cpu for l in cpu_per_time[job.t0:job.t0+job.processing_routine.duration]]
                cpu_per_time[job.t0:job.t0+job.processing_routine.duration] = [l + job.processing_routine.cpu for l in cpu_per_time[job.t0:job.t0+job.processing_routine.duration]]

        # Calculate percentage of resources used
        dict_resources={}
        dict_resources["CPU"] = [(cpu/self.cpu_max)*100 for cpu in cpu_per_time]
        dict_resources["RAM"] = [(ram/self.ram_max)*100 for ram in ram_per_time]
        dict_resources["Storage"] = [(storage_space/self.storage_space_max)*100 for storage_space in storage_space_per_time]
        dict_resources["VM"] = [(vm/self.vm_max)*100 for vm in vm_per_time]

        x = np.array([t for t in range(self.t_max)])
        width = 1
        multiplier = 0
        colors = sns.color_palette("mako", 4)
        axes=[ax2,ax3,ax4,ax5]

        # Plot figure of resources
        for name_resource, measurement in dict_resources.items():
            axes[multiplier].bar(x + width/2, measurement, width, label=name_resource, color=colors[multiplier])
            axes[multiplier].set_ylim(0, 100)
            axes[multiplier].set_xlim(0, self.t_max)
            axes[multiplier].legend(loc='lower left', ncols=1)
            axes[multiplier].grid(True)
            multiplier += 1

        plt.show()
        self.logger.info("End visualization")
