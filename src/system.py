# _*_ coding: utf-8 _*_
import time

import xlwt


import os
import random
from queue import PriorityQueue
import sys

from buffer import Buffer
from component import ComponentType, ProductType
from event import *
from fel import FutureEventList
from inspector import Inspector, OutputPolicy
from logger import Logger
from rng import generate_exp
from workstation import Workstation

rng_seed = None

END_TIME = 1000.00

# Lambda values for the various distributions
# Inspectors
IN1_LAM = 0.0965
IN2_LAM_C2 = 0.0644
IN2_LAM_C3 = 0.0485
# Workstations
WS1_LAM = 0.2172
WS2_LAM = 0.09015
WS3_LAM = 0.1137

LOG_DIR = 'log'


class System():
    def __init__(self, replication_id):  # BS: class constructor
        print('Simulation Start')
        self.running = True
        # Track current time
        self.clock = 0

        # Instantiate logger
        os.makedirs(LOG_DIR, exist_ok=True)
        OUT_PATH = os.path.join(LOG_DIR, f'rep{replication_id}.log')
        self.log = Logger(OUT_PATH)
        self.log.write_header()
        # Track number of products output in order to calculate throughput
        self.num_P1 = 0
        self.num_P2 = 0
        self.num_P3 = 0
        # Track time inspectors (either, or both) spend blocked
        self.blocked_time = 0
        # blocked inspectors list
        self.blocked_inspectors = list()
        # Setup FEL
        self.event_list = PriorityQueue()

        # Create workstations
        ws_1 = Workstation(self, 'WS1', WS1_LAM, [ComponentType.C1], ProductType.P1)
        ws_2 = Workstation(self, 'WS2', WS2_LAM, [ComponentType.C1, ComponentType.C2], ProductType.P2)
        ws_3 = Workstation(self, 'WS3', WS3_LAM, [ComponentType.C1, ComponentType.C3], ProductType.P3)
        # LBS: without need to declare workstations as list
        self.workstations = [ws_1, ws_2, ws_3]

        # Create inspectors
        # LBS: ins_1_lambdas is a dict formatted as �� key: value...��
        ins_1_lambdas = {ComponentType.C1: IN1_LAM}
        ins_1 = Inspector(self, 'IN1', ins_1_lambdas, [ComponentType.C1], 
                            [ws_1, ws_2, ws_3], OutputPolicy.SHORTEST_QUEUE)

        ins_2_lambdas = {ComponentType.C2: IN2_LAM_C2, ComponentType.C3: IN2_LAM_C3}
        ins_2 = Inspector(self, 'IN2', ins_2_lambdas, 
                            [ComponentType.C2, ComponentType.C3], [ws_2, ws_3],
                            OutputPolicy.NAIVE)
        self.inspectors = [ins_1, ins_2]

        # Generate initial events
        # These should be the two inspectors' first component selections
        self.schedule_inspection(ins_1, ins_1.generate_time(0, ins_1.component))
        self.schedule_inspection(ins_2, ins_2.generate_time(0, ins_2.component))

        # As well as an end-simulation event
        self.schedule_event(EndSimulationEvent(END_TIME))

        # Open Excel log

        self.TimeColumn = 0
        self.CurrentEventColumn = 1
        self.EventListColumn = 2
        self.Inspector1Column = 3
        self.Inspector2Column = 4
        self.WS1_C1_Q_Column = 5
        self.WS2_C1_Q_Column = 6
        self.WS2_C2_Q_Column = 7
        self.WS3_C1_Q_Column = 8
        self.WS3_C3_Q_Column = 9
        self.BLOCKED_IN1 = 10
        self.BLOCKED_IN2 = 11
        self.NUM_P1 = 12
        self.NUM_P2 = 13
        self.NUM_P3 = 14
        self.BLOCK_INS_LIST = 15
        self.WS1_BUSY = 16
        self.WS2_BUSY = 17
        self.WS3_BUSY = 18

        self.now = time.strftime("%H-%M-%S")
        self.logfile = "Log" + str(replication_id) + ".xls"
        print("new file:" + self.logfile)
        self.workbook = xlwt.Workbook(self.logfile)
        self.worksheet = self.workbook.add_sheet(
            'log1', cell_overwrite_ok=True)
        # cell_overwrite_ok = True
        # self.worksheet.write("infoPlist", cell_overwrite_ok) # allow to overwrite
        # self.rows_old = self.worksheet.nrows
        self.rows_old = 0
        self.write_excel_xls_append("Time", self.TimeColumn)
        self.write_excel_xls_append("CurrentEvent", self.CurrentEventColumn)
        self.write_excel_xls_append("EventList", self.EventListColumn)
        self.write_excel_xls_append("Inspector1", self.Inspector1Column)
        self.write_excel_xls_append("Inspector2", self.Inspector2Column)
        self.write_excel_xls_append("WS1_C1_Q", self.WS1_C1_Q_Column)
        self.write_excel_xls_append("WS2_C1_Q", self.WS2_C1_Q_Column)
        self.write_excel_xls_append("WS2_C2_Q", self.WS2_C2_Q_Column)
        self.write_excel_xls_append("WS3_C1_Q", self.WS3_C1_Q_Column)
        self.write_excel_xls_append("WS3_C3_Q", self.WS3_C3_Q_Column)

        self.write_excel_xls_append("blocked_IN1", self.BLOCKED_IN1)
        self.write_excel_xls_append("blocked_IN2", self.BLOCKED_IN2)
        self.write_excel_xls_append("num_P1", self.NUM_P1)
        self.write_excel_xls_append("num_P2", self.NUM_P2)
        self.write_excel_xls_append("num_P3", self.NUM_P3)
        self.write_excel_xls_append("blockInsList", self.BLOCK_INS_LIST)
        self.write_excel_xls_append("ws1Busy", self.WS1_BUSY)
        self.write_excel_xls_append("ws2Busy", self.WS2_BUSY)
        self.write_excel_xls_append("ws3Busy", self.WS3_BUSY)

        # self.write_excel_xls_append("111", 2)
        # self.write_excel_xls_save(self.logfile)

        # self.write_excel_xls_append("111", 2)

        # Print initial state to console
        self.print_current_state_beforeproc(None)
        self.print_inspectors()
        self.print_workstations()
        self.print_event_list()
        self.print_current_state_afterproc(None)

    def time_advance(self):
        """
        Find the next event in the event list and advance clock to its time.
        """
        next_event = self.event_list.get()
        self.clock = next_event.time
        self.print_current_state_beforeproc(next_event)

        if isinstance(next_event, EndInspectionEvent):
            self.event_inspection(next_event)
        elif isinstance(next_event, EndAssemblyEvent):
            self.event_assembly(next_event)
        elif isinstance(next_event, EndSimulationEvent):
            self.event_end()

        # Update blocked times
        for ins in self.blocked_inspectors:
            if ins.is_blocked():
                ins.time_blocked += (self.clock - ins.last_event_time)
                ins.last_event_time = self.clock

        self.print_inspectors()
        self.print_workstations()
        self.print_event_list()

        self.print_current_state_afterproc(None)

        stats = {
            'time': round(self.clock, 4),
            'blocked_IN1': round(self.get_inspector_by_id('IN1').time_blocked, 4),
            'blocked_IN2': round(self.get_inspector_by_id('IN2').time_blocked, 4),
            'total_P1': self.num_P1,
            'total_P2': self.num_P2,
            'total_P3': self.num_P3
        }

        self.log.write_data(stats)

    def schedule_event(self, event):
        """
        Put an event into the future event list.
        """
        self.event_list.put(event)

    def schedule_inspection(self, inspector, time):  # LBS： done
        """
        Schedule an end-of-inspection event for the given instructor at the
        specified time.
        """
        self.schedule_event(EndInspectionEvent(time, inspector.id))

    def schedule_workstation(self, workstation, time):  # LBS： Done
        """
        Schedule an end-of-assembly event for the given workstation at the
        specified time.
        """
        if workstation.all_components_ready() and workstation.busy == False:
            self.schedule_event(EndAssemblyEvent(time, workstation.id))
            workstation.busy = True

            # LBS： take required components from buffer
            for comp in workstation.buffers.keys():
                workstation.get_buffer(comp).dequeue()

            # LBS Modify
            released_inspectors = self.blocked_inspectors
            for i in self.blocked_inspectors:
                if i.output_component() == True:
                    comp = i.component
                    time = i.generate_time(self.clock, comp)
                    self.schedule_inspection(i, time)
                    released_inspectors.remove(i)

            # update the blocked_inspectors after output_component action LBS ADD
            self.blocked_inspectors = released_inspectors

    def event_inspection(self, event):
        """
        Event subroutine for an end-of-inspection event.
        LBS: 1) the event_inspection function may cause endassembly event and thus cause corresponding buffer Queue empty.
        """
        ins = self.get_inspector_by_id(event.id)
        # If the inspector is blocked, do nothing
        if ins.is_blocked():
            # ins.time_blocked += self.clock - ins.last_event_time
            self.blocked_inspectors.append(ins)  # LBS ADD

        # Otherwise, have the inspector draw a new part and schedule an
        # end-of-inspection event normally.
        else:
            ins.output_component()  # Inside the out_component, the Endassmbling event is scheduled
            comp = ins.component
            time = ins.generate_time(self.clock, comp)
            self.schedule_inspection(ins, time)

        ins.last_event_time = self.clock

    def event_assembly(self, event):
        """
        Event subroutine for an end-of-assembly event.
        """
        wrk = self.get_workstation_by_id(event.id)
        # If the workstation has all the needed parts available in its queues,
        # have it assemble and output a product.
        # The workstation will also alert blocked inspectors (that are holding a relevant component) that it has
        # consumed a component; the inspectors will push their component and
        # become unblocked.

        # if wrk.all_components_ready(): LBS delete， because the components were taken at the beginning of assebling rather then
        # the completion of assembling

        #  LBS delete: because blocked_inspectors = [i for i in self.inspectors if i.is_blocked(), that is enough. we need not to
        #  judge if "i.component in ws_types", because it will make things complex and may make mistakes
        #  Hint: blocked_inspectors can only be added when a INS found itself was blocked, and only be removed
        #  after output_component().
        # ws_types = list(wrk.buffers.keys())
        # blocked_inspectors = [i for i in self.inspectors if i.is_blocked() and i.component in ws_types]

        wrk.assemble()  # LBS: complete assembling

        if event.id == 'WS1':
            self.num_P1 += 1
        elif event.id == 'WS2':
            self.num_P2 += 1
        elif event.id == 'WS3':
            self.num_P3 += 1

        released_inspectors = self.blocked_inspectors
        for i in self.blocked_inspectors:
            if i.output_component() == True:
                comp = i.component
                time = i.generate_time(self.clock, comp)
                self.schedule_inspection(i, time)
                released_inspectors.remove(i)
            # Otherwise, do nothing LBS ADD

        # update the blocked_inspectors after output_component action LBS ADD
        self.blocked_inspectors = released_inspectors

        # Otherwise, do nothing. This situation may occur if too many assembly
        # events are scheduled in the FEL (e.g. two events are scheduled, but
        # the buffers contain 2 of one component and 1 of the other).
        # else:
        #     print('Assembly aborted: missing components.')

    def event_end(self):
        """
        Event subroutine for an end-of-simulation event.
        """
        print('Simulation End')
        self.running = False
        self.print_final_statistics()
        self.write_excel_xls_save(self.logfile)  # save logfile

    def generate_statistics(self):
        """
        Calculate important statistics and output them to file.
        """
        ...

    def print_event_list(self):
        tuples = list()
        tmpstr = ""
        for e in sorted(self.event_list.queue):
            tuples.append((e.time, e.id))
            tmpstr += "["+str(e.time) + ":" + str(e.id)+"] "

        print(f'Event list: {tuples}')
        self.write_excel_xls_append(tmpstr, self.EventListColumn)

    def print_inspectors(self):
        tuples = list()
        for i in self.inspectors:
            tuples.append((i.id, i.component.name))

        print(f'Inspectors: {tuples}')
        self.write_excel_xls_append(
            self.inspectors[0].component.name, self.Inspector1Column)
        self.write_excel_xls_append(
            self.inspectors[1].component.name, self.Inspector2Column)

    def print_workstations(self):
        tuples = list()
        for w in self.workstations:
            for t in w.buffers.keys():
                buffer = w.buffers[t]
                tuples.append((w.id, buffer.component_type.name,
                               f'In queue: {buffer.get_length()}'))

                if w.id == 'WS1' and buffer.component_type.name == 'C1':
                    self.write_excel_xls_append(
                        buffer.get_length(), self.WS1_C1_Q_Column)
                if w.id == 'WS2' and buffer.component_type.name == 'C1':
                    self.write_excel_xls_append(
                        buffer.get_length(), self.WS2_C1_Q_Column)
                if w.id == 'WS2' and buffer.component_type.name == 'C2':
                    self.write_excel_xls_append(
                        buffer.get_length(), self.WS2_C2_Q_Column)
                if w.id == 'WS3' and buffer.component_type.name == 'C1':
                    self.write_excel_xls_append(
                        buffer.get_length(), self.WS3_C1_Q_Column)
                if w.id == 'WS3' and buffer.component_type.name == 'C3':
                    self.write_excel_xls_append(
                        buffer.get_length(), self.WS3_C3_Q_Column)

        print(f'Workstations: {tuples}')

    def print_current_state_beforeproc(self, curr_event):
        print(f'Time: {self.clock}')

        self.rows_old = self.rows_old + 1

        self.write_excel_xls_append(str(self.clock), self.TimeColumn)

        if curr_event:
            print(f'Current event: ({curr_event.time}, {curr_event.id})')
            self.write_excel_xls_append(
                str(curr_event.time) + ":" + str(curr_event.id), self.CurrentEventColumn)

        # self.write_excel_xls_append(str(round(self.get_inspector_by_id('IN1').time_blocked, 4)), self.BLOCKED_IN1)
        # self.write_excel_xls_append(str(round(self.get_inspector_by_id('IN2').time_blocked, 4)), self.BLOCKED_IN2)
        # self.write_excel_xls_append(str(self.num_P1), self.NUM_P1)
        # self.write_excel_xls_append(str(self.num_P2), self.NUM_P2)
        # self.write_excel_xls_append(str(self.num_P3), self.NUM_P3)

    def print_current_state_afterproc(self, curr_event):
        self.write_excel_xls_append(
            str(round(self.get_inspector_by_id('IN1').time_blocked, 4)), self.BLOCKED_IN1)
        self.write_excel_xls_append(
            str(round(self.get_inspector_by_id('IN2').time_blocked, 4)), self.BLOCKED_IN2)
        self.write_excel_xls_append(str(self.num_P1), self.NUM_P1)
        self.write_excel_xls_append(str(self.num_P2), self.NUM_P2)
        self.write_excel_xls_append(str(self.num_P3), self.NUM_P3)
        tmpstr = ""
        if len(self.blocked_inspectors) > 0:
            for bi in self.blocked_inspectors:
                tmpstr = tmpstr + "[" + str(bi.get_id()) + "]"

        self.write_excel_xls_append(tmpstr, self.BLOCK_INS_LIST)

        self.write_excel_xls_append(
            str(self.workstations[0].busy), self.WS1_BUSY)
        self.write_excel_xls_append(
            str(self.workstations[1].busy), self.WS2_BUSY)
        self.write_excel_xls_append(
            str(self.workstations[2].busy), self.WS3_BUSY)
    print('------')

    def print_final_statistics(self):
        print(
            f'P1: {self.num_P1}, P2: {self.num_P2}, P3: {self.num_P3}, Total: {self.num_P1 + self.num_P2 + self.num_P3}')
        print(f'Total time blocked:')
        for i in self.inspectors:
            percentage = round(100 * i.time_blocked / END_TIME, 4)
            print(f'{i.id}: {i.time_blocked} seconds ({percentage}%)')

    def get_inspector_by_id(self, id):
        """
        Find and return an inspector with the given ID string
        """
        for i in self.inspectors:
            if i.id == id:
                return i

    def get_workstation_by_id(self, id):
        """
        Find and return an workstation with the given ID string
        """
        for w in self.workstations:
            if w.id == id:
                return w

    def write_excel_xls_append(self, value, j):
        self.worksheet.write(self.rows_old, j, value)

    def write_excel_xls_save(self, file):
        self.workbook.save(file)
        print("xls saved")

    # def determine_next_departure(self, comp):
    #     """
    #     Return the time right after the time of the next assembly event that
    #     will use up a component of the specified type.
    #     This is used to
    #     """
    #     # Build a list of stations that can handle the specified component
    #     station_ids = list()
    #     for w in self.workstations:
    #         if w.can_accept(comp):
    #             station_ids.append(w.id)

    #     # Find the first assembly event that involves any of these stations
    #     # The inspector can try again the tick after that assembly is scheduled
    #     # If it is still blocked, the inspector can run this function again
    #     for event in sorted(self.event_list.queue):
    #         id = event.id
    #         if id in station_ids:
    #             return event.time + 1.0

    #     return None

    # def determine_next_arrival(self, comp):
    #     """
    #     Determine the next event where an inspector that handles the specified
    #     component type will output a component.
    #     """
    #     inspector_ids = list()
    #     for i in self.inspectors:
    #         if comp in i.input_types:
    #             inspector_ids.append(i.id)

    #     # Find the first inspeciton event that involves any of these stations
    #     for event in sorted(self.event_list.queue):
    #         id = event.id
    #         if id in inspector_ids:
    #             return event.time + 1.0


# if __name__ == '__main__':
#
#     replication_number = sys.argv[1]
# 	for curr_replication in range(replication_number):
# 	    # Initialize a system
# 	    sys = System(replication_number)
# 	    # sys = System(50)
# 	    while (sys.running):
# 	        sys.time_advance()
if __name__ == '__main__':
    replication_number = int(sys.argv[1])

    for curr_replication in range(replication_number):
        # Initialize a system
        sys = System(curr_replication)

        while (sys.running):
            sys.time_advance()
