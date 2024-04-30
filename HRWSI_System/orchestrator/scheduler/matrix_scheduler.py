#!/usr/bin/env python3
"""
Matrix_scheduler module implements a particular method to schedule processing tasks thanks to a matrix. 
The matrix is usefull to manage resources and dependencies.
"""
import sys
import os
from itertools import product
import uuid
import numpy as np

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from HRWSI_System.orchestrator.scheduler.scheduler import Scheduler
from HRWSI_System.orchestrator.processing_task.processing_task import ProcessingTask
from HRWSI_System.orchestrator.processing_routine.processing_routine import ProcessingRoutine

class MatrixScheduler(Scheduler):
    """Use a matrix to planify processing tasks"""

    def __init__(self, t_max: int,
                 cpu_max: int,
                 ram_max: int,
                 storage_space_max: int,
                 vm_max: int,
                 task_list: list[ProcessingTask],
                 json_path: str = None,
                 vm_name_list: list[str] = None,
                 vm_id_list: list[str] = None):

        super().__init__(t_max, cpu_max, ram_max, storage_space_max, vm_max, task_list, json_path)

        self.vm_name_list = vm_name_list
        self.vm_id_list = vm_id_list
        self.plan_matrix = np.zeros((self.cpu_max,self.t_max), int)

    def plan(self) -> None:
        """Set t0 of tasks in task_list"""

        self.logger.info("Begin plan")

        # Creation of necessary variables to place processing_task in plan_matrix
        task_by_routine={}
        routine_list=[]
        task_by_id={}
        task_0_by_routine=[]
        for task in self.task_list:
            task_by_id[task.task_id]=task
            if task.processing_routine.name not in task_by_routine:
                task_by_routine[task.processing_routine.name]=[task]
                routine_list.append(task.processing_routine)
                task_0_by_routine.append(task)
            else :
                task_by_routine[task.processing_routine.name].append(task)

        self.logger.debug("routine_list: %s", [i.name for i in routine_list])
        sorted_routine_list = self.sort_routine_list_by_dependencies(routine_list, task_0_by_routine, task_by_id)
        self.logger.debug("sorted_routine_list: %s", [sorted_routine.name for sorted_routine in sorted_routine_list ])

        list_time = self.calculate_list_of_time_max_for_each_routine(task_by_routine, sorted_routine_list)
        self.logger.debug("list_time= %s", list_time)

        self.place_tasks(task_by_routine, task_by_id, sorted_routine_list, list_time)
        self.logger.debug("Matrix plan : %s", self.plan_matrix)

        self.create_attribution_plan(sorted_routine_list, task_by_routine)
        self.logger.debug("Attribution plan : %s", self.attribution_plan)

        self.logger.info("End plan")

    def calculate_list_of_time_max_for_each_routine(self, task_by_routine: dict, sorted_routine_list: list[ProcessingRoutine]) -> list[int]:
        """Calculate the maximum time given to place the tasks for each routine"""

        self.logger.info("Begin calculate list of time max for each routine")

        # Check limit of time for each routine
        list_time_min = [np.ceil((len(task_by_routine[routine.name]) /
                                 min(self.cpu_max // routine.cpu,
                                        self.ram_max // routine.ram,
                                        self.storage_space_max // routine.storage_space,
                                        self.vm_max))) * routine.duration for i, routine in enumerate(sorted_routine_list)]
        self.logger.debug("list_time_min= %s", list_time_min)

        # Calculate the percentage of total time necessary to process all processing_task of each routine
        # Distribute the extra time (compared to the minimum time required) between routines according to their size
        time_routine = [routine.cpu * routine.duration * len(task_by_routine[routine.name]) for routine in sorted_routine_list]
        list_time = [int(np.round((rtime / sum(time_routine))*(self.t_max-sum(list_time_min))) + list_time_min[i]) for i, rtime in enumerate(time_routine)]

        self.logger.info("End calculate list of time max for each routine")

        return list_time

    def sort_routine_list_by_dependencies(self, routine_list: list[ProcessingRoutine], task_0_by_routine: dict, task_by_id: dict) -> list[ProcessingRoutine]:
        """Sorts routine by its dependencies"""

        self.logger.info("Begin sort routine list by dependencies")

        sorted_routine_list = []
        for id_routine, routine in enumerate(routine_list):
            # No task in the routine
            if task_0_by_routine[id_routine] is None:
                continue
            task_ids_dependency_list = task_0_by_routine[id_routine].depends_on

            # No dependency
            if task_ids_dependency_list is None and routine.name not in [sorted_routine.name for sorted_routine in sorted_routine_list]:
                sorted_routine_list = [routine] + sorted_routine_list
                continue
            if task_ids_dependency_list is None:
                continue
            routine_dependencies = [task_by_id[task_ids_dependency].processing_routine for task_ids_dependency in task_ids_dependency_list]

            # Dependencies processing
            for routine_i_depend_on in routine_dependencies:
                if routine_i_depend_on.name not in [sorted_routine.name for sorted_routine in sorted_routine_list]:

                    # If dependency and routine not in sorted_routine_list : we add dependency at the end of sorted_routine_list
                    if routine.name not in [sorted_routine.name for sorted_routine in sorted_routine_list]:
                        sorted_routine_list.append(routine_i_depend_on)

                    # If dependency not in sorted_routine_list but routine are in : we add dependency just before routine
                    else:
                        id_routine = [sorted_routine.name for sorted_routine in sorted_routine_list].index(routine.name)
                        sorted_routine_list = sorted_routine_list[:id_routine] + [routine_i_depend_on] + sorted_routine_list[id_routine:]

            # Routine processing
            if routine.name not in [sorted_routine.name for sorted_routine in sorted_routine_list]:
                best_id = max([[sorted_routine.name for sorted_routine in sorted_routine_list].index(routine_dependency.name)+1  for routine_dependency in routine_dependencies])
                sorted_routine_list = sorted_routine_list[:best_id] + [routine] + sorted_routine_list[best_id:]

        self.logger.info("End sort routine list by dependencies")

        return sorted_routine_list

    #@profile
    def check_routine_conditions_to_place_task(self, task: ProcessingTask, routine: ProcessingRoutine, time_max_for_the_routine: int, i: int, j: int, ram_per_time: list[int], storage_space_per_time: list[int], vm_per_time: list[int]) -> bool:
        """Checks routine-dependent conditions to place processing_task in plan_matrix"""

        self.logger.info("Begin check condition to place task")

        # No overlap between VMs
        if j%routine.cpu!=0:
            self.logger.debug("j mod routine.cpu %s", j%routine.cpu)
            return False
        self.logger.debug("No overlap between VMs check")

        # Limit time
        if i+routine.duration>time_max_for_the_routine:
            return False
        self.logger.debug("Limit time check")

        # Processing_task already placed or we don't have time and cpu to place it at this place
        if not (self.plan_matrix[j:j+routine.cpu,i:i+routine.duration].shape==(routine.cpu,routine.duration)) or task.t0 is not None :
            return False
        self.logger.debug("Processing_task not already placed and we have time and cpu to place it at this place check")

        # Free location
        if (self.plan_matrix[j:j+routine.cpu,i:i+routine.duration]!=0).any():
            return False
        self.logger.debug("Free location check")

        # Materials resources limit
        test_ram = [k + routine.ram > self.ram_max for k in ram_per_time[i:i+routine.duration]] # RAM use <= RAM max
        test_storage = [k + routine.storage_space > self.storage_space_max for k in storage_space_per_time[i:i+routine.duration]] # Storage_space use <= Storage_space max
        test_vm = [k + 1 > self.vm_max for k in vm_per_time[i:i+routine.duration]] # VM use <= VM max
        if any(test_ram) or any(test_storage) or any(test_vm):
            self.logger.debug("RAM %s", test_ram)
            self.logger.debug("Storage space %s", test_storage)
            self.logger.debug("VM %s", test_vm)
            return False
        self.logger.debug("Materials resources limit check")

        self.logger.info("End check condition to place task")
        return True

    def check_task_dependencies(self, task: ProcessingTask, task_by_id: dict, i: int) -> bool:
        """Check if all the dependencies of a task are respected : task-dependent condition"""

        # Dependencies
        if task.depends_on is not None and any([(task_by_id[task.depends_on[k]].t0 + task_by_id[task.depends_on[k]].processing_routine.duration) > i for k in range(len(task.depends_on))]):
            return False
        self.logger.debug("Dependencies check")

        return True

    #@profile
    def place_tasks(self, task_by_routine: dict, task_by_id: dict, sorted_routine_list: list[ProcessingRoutine], list_time: list[int]) -> None:
        """Place all tasks in the matrix"""

        self.logger.info("Begin place task")

        # Creation of resources list
        ram_per_time = [0 for i in range(self.t_max)]
        storage_space_per_time = [0 for i in range(self.t_max)]
        vm_per_time = [0 for i in range(self.t_max)]

        # Add a list of candidate to only test empty emplacement to planned processing_task
        current_routine_candidates = []
        useless_candidates_for_this_routine = []
        useless_candidates_for_this_task = []
        for id_routine, routine_to_placed in enumerate(sorted_routine_list):
            self.logger.info("Routine : %s", sorted_routine_list[id_routine].name)

            time_max_for_the_routine = sum(list_time[:id_routine+1])
            offset_previous_routines = 0

            # Modify offset if it's not the first routine
            if id_routine:
                offset_previous_routines = sum(list_time[:id_routine])
            leftovers_routine_candidates = []

            # Add leftovers if it's not the first routine
            if current_routine_candidates:
                leftovers_routine_candidates = current_routine_candidates

            # Create candidate for the routine
            current_routine_candidates = [offset_previous_routines + self.t_max*(i//list_time[id_routine]) + i%list_time[id_routine] for i in range(self.cpu_max*list_time[id_routine])]
            current_routine_candidates = useless_candidates_for_this_routine + leftovers_routine_candidates + current_routine_candidates
            current_routine_candidates.sort()

            # Planned all processing_task for the routine_to_placed
            useless_candidates_for_this_routine = []
            for task in task_by_routine[routine_to_placed.name]:
                for candidate in current_routine_candidates:
                    j = candidate//self.t_max
                    i = candidate%self.t_max

                    # If routine-dependent conditions are false, all the tasks of the routine cannot be place here : removes the candidate from the possibilities for this routine
                    if not self.check_routine_conditions_to_place_task(task, routine_to_placed,
                                      time_max_for_the_routine,
                                      i, j, ram_per_time,
                                      storage_space_per_time,
                                      vm_per_time) and candidate not in useless_candidates_for_this_routine:
                        useless_candidates_for_this_task.append(candidate)
                        continue

                    # If task-dependent are false, an other task of the routine can be place here, so just continue the iteration
                    if not self.check_task_dependencies(task, task_by_id, i):
                        continue

                    # In other case, place task
                    self.plan_matrix[j:j+routine_to_placed.cpu, i:i+routine_to_placed.duration] = id_routine+1
                    ram_per_time[i:i+routine_to_placed.duration] = [l + routine_to_placed.ram for l in ram_per_time[i:i+routine_to_placed.duration]]
                    storage_space_per_time[i:i+routine_to_placed.duration] = [l + routine_to_placed.storage_space for l in storage_space_per_time[i:i+routine_to_placed.duration]]
                    vm_per_time[i:i+routine_to_placed.duration] = [l + 1 for l in vm_per_time[i:i+routine_to_placed.duration]]
                    task.t0 = i

                    # Remove all index used to placed processing_task
                    remove_list = [jj*self.t_max+ii for jj,ii in product(range(j,j+routine_to_placed.cpu),range(i,i+routine_to_placed.duration))]
                    for to_remove_candidate in remove_list:
                        current_routine_candidates.remove(to_remove_candidate)

                    # Remove all index who cannot place task because of routine condition
                    if useless_candidates_for_this_task:
                        for useless_candidate in useless_candidates_for_this_task:
                            current_routine_candidates.remove(useless_candidate)

                    # Keep candidate not usefull for this routine in order to add these candidates in the next routine
                    useless_candidates_for_this_routine = useless_candidates_for_this_routine + useless_candidates_for_this_task
                    useless_candidates_for_this_task = []
                    break

        self.logger.info("End place task")

    #@profile
    def create_attribution_plan(self, sorted_routine_list: list[ProcessingRoutine], task_by_routine: dict) -> None:
        """Interpretation of plan_matrix and creation of attribution_plan"""

        self.logger.info("Begin creation of attribution plan")

        self.attribution_plan = {}
        for nb_routine, routine in enumerate(sorted_routine_list):
            self.logger.info("Routine : %s", sorted_routine_list[nb_routine].name)

            # Sort the task in ascending order of t0
            task_by_routine[routine.name].sort(key=lambda x: x.t0)
            i=0
            list_task_in_routine = list(task_by_routine[routine.name])
            list_task_not_placed = list_task_in_routine.copy()

            # Place task in VM for the routine
            while len(list_task_in_routine) != 0:
                vm_name = self.vm_name_list[i] if self.vm_name_list else f"{routine.name}_worker_{i+1}"
                vm_id = self.vm_id_list[i] if self.vm_id_list else str(uuid.uuid1())

                if vm_name not in self.attribution_plan:
                    self.attribution_plan[vm_name] = [vm_id,f"flavour{nb_routine+1}",None,None,[]]
                for _, task in enumerate(list_task_in_routine):

                    # Place the first task for this VM
                    if self.attribution_plan[vm_name][2] is None:
                        self.attribution_plan[vm_name][4].append(task)
                        self.attribution_plan[vm_name][2] = task.t0
                        self.attribution_plan[vm_name][3] = task.t0 + task.processing_routine.duration
                        list_task_not_placed.remove(task)

                    # Place the other task for this VM
                    else:
                        last_task = self.attribution_plan[vm_name][4][-1]

                        # If the time permitted to place the task
                        if last_task.t0 + last_task.processing_routine.duration <= task.t0: # Accepts that the worker can wait and do nothing for a while (if it's not accepted, replace by : ==)
                            self.attribution_plan[vm_name][4].append(task)
                            self.attribution_plan[vm_name][3] = task.t0 + task.processing_routine.duration
                            list_task_not_placed.remove(task)
                list_task_in_routine = list_task_not_placed.copy()
                i+=1

        self.logger.info("End creation of attribution plan")

if __name__ == "__main__":

    processing_routine_a = ProcessingRoutine(name="foo", cpu=2, ram=1, storage_space=2, duration=5, docker_image="bar")
    processing_routine_b = ProcessingRoutine(name="foo2", cpu=3, ram=2, storage_space=2, duration=2, docker_image="bar")

    list_of_task=[]
    NB_IMAGE = 2000
    for nb_img in range(NB_IMAGE*2):
        if nb_img < NB_IMAGE :
            list_of_task.append(ProcessingTask(processing_routine=processing_routine_a, task_id=nb_img, t0=None, depends_on=None))
        else :
            list_of_task.append(ProcessingTask(processing_routine=processing_routine_b, task_id=nb_img, t0=None, depends_on=[nb_img%NB_IMAGE]))

    planning = MatrixScheduler(t_max=5750, cpu_max=10, ram_max=10, storage_space_max=10, vm_max=4, task_list=list_of_task,json_path="plan.json"
                               ,vm_name_list=["1","2","3","4"], vm_id_list=["01","02","03","04"])

    planning.check_feasibility()
    planning.plan()
    planning.check_plan()
    planning.visualization()

    #planning.export_to_json()
