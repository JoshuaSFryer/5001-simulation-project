import random
from queue import PriorityQueue

from buffer import Buffer
from component import ComponentType, ProductType
from event import *
from fel import FutureEventList
from inspector import Inspector, OutputPolicy
from rng import generate_exp
from workstation import Workstation

rng_seed = None

END_TIME = 1000.00

# Lambda values for the various distributions
IN1_LAM = 0.0965
IN2_LAM_C2 = 0.0644
IN2_LAM_C3 = 0.0485

WS1_LAM = 0.2172
WS2_LAM = 0.09015
WS3_LAM = 0.1137

class System():
    def __init__(self):
        print('Simulation Start')
        self.running = True

        self.clock = 0
        # Track number of products output in order to calculate throughput
        self.num_outputs = 0
        # Track time inspectors (either, or both) spend blocked
        self.blocked_time = 0

        # Seed RNG if desired
        if not rng_seed is None:
            random.seed(rng_seed)

        # Setup FEL
        self.event_list = PriorityQueue()

        # Create workstations
        ws_1 = Workstation(self, 'WS1', WS1_LAM, [ComponentType.C1], ProductType.P1)
        ws_2 = Workstation(self, 'WS2', WS2_LAM, [ComponentType.C1, ComponentType.C2], ProductType.P2)
        ws_3 = Workstation(self, 'WS3', WS3_LAM, [ComponentType.C1, ComponentType.C3], ProductType.P3)
        self.workstations = [ws_1, ws_2, ws_3]

        # Create inspectors
        ins_1_lambdas = {ComponentType.C1: IN1_LAM}
        ins_1 = Inspector(self, 'IN1', ins_1_lambdas, [ComponentType.C1], [ws_1, ws_2, ws_3], OutputPolicy.SHORTEST_QUEUE)

        ins_2_lambdas = {ComponentType.C2: IN2_LAM_C2, ComponentType.C3: IN2_LAM_C3}
        ins_2 = Inspector(self, 'IN2', ins_2_lambdas, [ComponentType.C2, ComponentType.C3], [ws_2, ws_3], OutputPolicy.NAIVE)
        self.inspectors = [ins_1, ins_2]

        # Generate initial events
        # These should be the two inspectors' first component selections
        self.schedule_inspection(ins_1, ins_1.generate_time(0, ins_1.component))
        self.schedule_inspection(ins_2, ins_2.generate_time(0, ins_2.component))

        # As well as an end-simulation event
        self.schedule_event(EndSimulationEvent(END_TIME))

        self.print_current_state(None)


    def time_advance(self):
        """
        Find the next event in the event list and advance clock to its time.
        """
        next_event = self.event_list.get()
        self.clock = next_event.time
        self.print_current_state(next_event)

        if isinstance(next_event, EndInspectionEvent):
            self.event_inspection(next_event)
        elif isinstance(next_event, EndAssemblyEvent):
            self.event_assembly(next_event)
        elif isinstance(next_event, EndSimulationEvent):
            self.event_end()
        
    
    def schedule_event(self, event):
        self.event_list.put(event)

    
    def schedule_inspection(self, inspector, time):
        self.schedule_event(EndInspectionEvent(time, inspector.id))

    
    def schedule_workstation(self, workstation, time):
        self.schedule_event(EndAssemblyEvent(time, workstation.id))


    def event_inspection(self, event):
        """
        Event subroutine for an end-of-inspection event.
        """
        ins = self.get_inspector_by_id(event.id)
        # If the inspector is blocked, do nothing
        if ins.is_blocked():
            pass
        # Otherwise, have the inspector draw a new part and schedule an
        # end-of-inspection event normally.
        else:
            ins.output_component()
            comp = ins.choose_input()
            ins.component = comp
            time = ins.generate_time(self.clock, comp)
            self.schedule_inspection(ins, time)


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
        if wrk.all_components_ready():
            wrk.assemble()
            self.num_outputs += 1

            ws_types = wrk.buffers.keys()
            
            blocked_inspectors = [i for i in self.inspectors if i.is_blocked() and i.component in ws_types]
            for i in blocked_inspectors:
                i.output_component()
        # Otherwise, do nothing. This situation may occur if too many assembly
        # events are scheduled in the FEL (e.g. two events are scheduled, but
        # the buffers contain 2 of one component and 1 of the other).
        else:
            print('Assembly aborted: missing components.')

    
    def event_end(self):
        """
        Event subroutine for an end-of-simulation event.
        """
        print('Simulation End')
        self.running = False
        self.print_final_statistics()


    def generate_statistics(self):
        """
        Calculate important statistics and output them to file.
        """
        ...

    
    def print_event_list(self):
        tuples = list()
        for e in sorted(self.event_list.queue):
            tuples.append((e.time, e.id))
        print(f'Event list: {tuples}')
    

    def print_inspectors(self):
        tuples = list()
        for i in self.inspectors:
            tuples.append((i.id, i.component.name))
        print(f'Inspectors: {tuples}')

    
    def print_workstations(self):
        tuples = list()
        for w in self.workstations:
            for t in w.buffers.keys():
                buffer = w.buffers[t]
                tuples.append((w.id, buffer.component_type.name, f'In queue: {buffer.get_length()}'))
        print(f'Workstations: {tuples}')


    def print_current_state(self, curr_event):
        print(f'Time: {self.clock}')
        if curr_event:
            print(f'Current event: ({curr_event.time}, {curr_event.id})')
        self.print_event_list()
        self.print_inspectors()
        self.print_workstations()
        print('------')


    def print_final_statistics(self):
        print(f'Total products: {self.num_outputs}')


    def get_inspector_by_id(self, id):
        for i in self.inspectors:
            if i.id == id:
                return i

    
    def get_workstation_by_id(self, id):
        for w in self.workstations:
            if w.id == id:
                return w

    
    def determine_next_departure(self, comp):
        # Build a list of stations that can handle the specified component
        station_ids = list()
        for w in self.workstations:
            if w.can_accept(comp):
                station_ids.append(w.id)

        # Find the first assembly event that involves any of these stations
        # The inspector can try again the tick after that assembly is scheduled
        # If it is still blocked, the inspector can run this function again
        for event in sorted(self.event_list.queue):
            id = event.id
            if id in station_ids:
                return event.time + 1

        return None


    def determine_next_arrival(self, comp):
        """
        Determine the next event where an inspector that handles the specified
        component type will output a component.
        """
        inspector_ids = list()
        for i in self.inspectors:
            if comp in i.input_types:
                inspector_ids.append(i.id)
        
        # Find the first inspeciton event that involves any of these stations
        for event in sorted(self.event_list.queue):
            id = event.id
            if id in inspector_ids:
                return event.time + 1



if __name__ == '__main__':
    # Initialize a system
    sys = System()

    while(sys.running):
        sys.time_advance()
