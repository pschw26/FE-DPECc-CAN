#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
All CAN bus driver classes

Created on Sun Mar 31 18:31:57 2024

@author: Eric Reusser
"""

import time
import canopen
from canopen import SdoCommunicationError, SdoAbortedError
from pytrinamic.modules.canopen_node import TmcmNode

#-----------------------------------------------------------------------------

class CanBus:
    """
    CanBus:
        Connect & disconnect to a CAN bus using CANOPEN protocoll

    Use:
        from canbus import CanBus
        ...
        bus = CanBus(config.bus_params)     [CAN bus instance]
        ...
        net = bus.connect()                 [CAN bus network]
        net.disconnect()
    """

    def __init__(self, bus_params):
        self.bus_params = bus_params

    def connect(self):
        net = canopen.Network()
        net.connect(channel=self.bus_params['channel'],
                    bustype=self.bus_params['bustype'],
                    bitrate=self.bus_params['bitrate'])
        print("CAN bus: Connected to " + self.bus_params['channel'] + 
              ", bitrate = " + str(self.bus_params['bitrate']),"\n")
        return net

#-----------------------------------------------------------------------------

class MotorDriver:
    """
    MotorDriver:  Always initialized by subclass 'Motor'!
        Handles all basic functions for a single motor based on internal units

    Use:
        Only used by wrapper class (subclass) 'Motor'
    """

    def __init__(self, net, sdo, params, v, a):
        self.net = net
        self.sdo = sdo
        self.params = params
        self.name     = self.params['name']
        self.node_id  = self.params['node']
        self.node     = None
        self.active   = False
        self.status   = 0
        self.position = 0
        self.velocity = v
        self.acceleration = a

        # Add node to network
        self.node = TmcmNode(self.node_id, self.params['eds'])
        net.add_node(self.node)
        print("Motor " + self.name + " assigned to node " +
              str(self.node_id) + " added to network")

        # Is motor active?
        try:
            self.node.sdo[0x1000].raw
            self.active = True
        except SdoCommunicationError:
            self.active = False
            print("Motor " + self.name + " is inactive!")
            return

        # Load SDO parameters
        try:
            for i in range(len(self.sdo)):
                if self.sdo[i] in self.params:
                    self.node.sdo[self.sdo[i]].raw = self.params[self.sdo[i]]
        except SdoAbortedError:
            self.active = False
            print("Motor " + self.name + 
                  ": SDO aborted due to device state! -> Reset controller")
            return

        print("Motor " + self.name + " is active")

        # Load default velocity & acceleration
        self.node.sdo['Profile Velocity in pp-mode 1'].raw = self.velocity
        self.node.sdo['Profile Acceleration 1'].raw = self.acceleration
        self.node.sdo['Profile Deceleration 1'].raw = self.acceleration
        print("Motor " + self.name + ": SDO parameters configured")

        # Load PDO maps & communication parameters
        self.node.load_configuration()

        # RPDO re-configuration:
        # 1: Control word
        # 2: Operation mode
        # 3: Target position
        # 4: Target velocity

        self.node.sdo[0x1401][1].raw = 0xC0000300 + self.node_id
        self.node.sdo[0x1601][0].raw = 0
        self.node.sdo[0x1601][1].raw = 0x60600008
        self.node.sdo[0x1601][0].raw = 1
        self.node.sdo[0x1401][1].raw = 0x40000300 + self.node_id

        self.node.sdo[0x1402][1].raw = 0xC0000400 + self.node_id
        self.node.sdo[0x1602][0].raw = 0
        self.node.sdo[0x1602][1].raw = 0x607A0020
        self.node.sdo[0x1602][0].raw = 1
        self.node.sdo[0x1402][1].raw = 0x40000400 + self.node_id

        self.node.sdo[0x1403][1].raw = 0xC0000500 + self.node_id
        self.node.sdo[0x1603][0].raw = 0
        self.node.sdo[0x1603][1].raw = 0x60FF0020
        self.node.sdo[0x1603][0].raw = 1
        self.node.sdo[0x1403][1].raw = 0x40000500 + self.node_id

        # TPDO configuration:
        # 1: Status word
        # 2: Operation mode: Inactive
        # 3: Actual position
        # 4: Actual velocity: Inactive

        self.node.sdo[0x1801][1].raw = 0xC0000280 + self.node_id
        self.node.sdo[0x1802][1].raw = 0xC0000380 + self.node_id
        self.node.sdo[0x1802][2].raw = 0x1
        self.node.sdo[0x1A02][0].raw = 0
        self.node.sdo[0x1A02][1].raw = 0x60640020
        self.node.sdo[0x1A02][0].raw = 1
        self.node.sdo[0x1802][1].raw = 0x40000380 + self.node_id
        self.node.sdo[0x1803][1].raw = 0xC0000480 + self.node_id

        self.node.sdo[0x1010][2].raw = 0x65766173
        print("Motor " + self.name + ": PDO channels configured")

        # Add callback functions
        def add_callback(self):
            def status_callback(message):
                self.status = message['Statusword 1'].raw

            def position_callback(message):
                self.position = message['Position Actual Value 1'].raw
            self.node.tpdo[1].add_callback(status_callback)
            self.node.tpdo[3].add_callback(position_callback)

        add_callback(self)
        print("Motor " + self.name + ": Callback functions added\n")

    def is_active(self):
        return self.active

    def is_rotating(self):
        self.node.sdo
        time.sleep(0.2)
        state = self.status & 0x4000   # Check if motor rotates
        return state
    
    def get_internal_position(self):
        self.net.sync.transmit()
        time.sleep(0.1)
        return self.position

    # Position mode ----------

    def move_position_internal(self, position, velocity = None,
                               acceleration = None):
        if velocity:
            if velocity != self.velocity:
                self.velocity = velocity
                self.node.sdo['Profile Velocity in pp-mode 1'].raw = velocity
        if acceleration:
            if acceleration != self.acceleration:
                self.acceleration = acceleration
                self.node.sdo['Profile Acceleration 1'].raw = acceleration
                self.node.sdo['Profile Deceleration 1'].raw = acceleration
        print("Motor " + self.name + ": Position mode")
        self.node.rpdo[2]['Modes of Operation 1'].raw = 1
        self.node.rpdo[2].transmit()
        self.node.rpdo[3]['Target Position 1'].raw = position
        self.node.rpdo[3].transmit()
        self.node.rpdo[1]['Controlword 1'].raw = 0x1F
        # Start rotation
        self.node.rpdo[1].transmit()
       
    def change_velocity_pp(self, velocity):
        self.velocity = velocity
        self.node.sdo['Profile Velocity in pp-mode 1'].raw = velocity

    def move_end(self):
        self.node.rpdo[1]['Controlword 1'].raw = 0x0F
        self.node.rpdo[1].transmit()

    def move_steps_internal(self, steps):
        self.net.sync.transmit()
        time.sleep(0.1)
        pos = self.position + steps
        self.node.rpdo[2]['Modes of Operation 1'].raw = 1
        self.node.rpdo[2].transmit()
        self.node.rpdo[3]['Target Position 1'].raw = pos
        self.node.rpdo[3].transmit()
        self.node.rpdo[1]['Controlword 1'].raw = 0x1F
        self.node.rpdo[1].transmit()
        while self.is_rotating(): pass
        self.move_end()

    def move_halt(self):
        # Stops rotation immediately
        self.node.rpdo[1]['Controlword 1'].raw = 0x10F
        self.node.rpdo[1].transmit()
        print("Motor " + self.name + ": HALT")
        while self.is_rotating(): pass
        self.net.sync.transmit()
        time.sleep(0.1)
        self.node.rpdo[3]['Target Position 1'].raw = self.position
        self.node.rpdo[3].transmit()
        self.node.rpdo[1]['Controlword 1'].raw = 0x1F
        self.node.rpdo[1].transmit()
        self.move_end()
    
    # Velocity mode ----------

    def move_velocity_internal(self, velocity, acceleration = None):
        if acceleration:
            if acceleration != self.acceleration:
                self.acceleration = acceleration
                self.node.sdo['Profile Acceleration 1'].raw = acceleration
        print("Motor " + self.name + ": Velocity mode")
        #self.node.sdo['Modes of Operation 1'].raw = 3
        #self.node.sdo[0x6060].raw = 3
        self.node.rpdo[2]['Modes of Operation 1'].raw = 3
        self.node.rpdo[2].transmit()
        self.node.rpdo[4]['Target Velocity 1'].raw = velocity
        self.node.rpdo[4].transmit()

    def change_velocity_pv(self, velocity):
        self.node.rpdo[4]['Target Velocity 1'].raw = velocity
        self.node.rpdo[4].transmit()

    def move_stop(self):
        self.node.sdo['Target Velocity 1'].raw = 0

#-----------------------------------------------------------------------------

class MotorGroupDriver:
    """
    MotorGroupDriver:  Always initialized by subclass 'MotorGroup'!
        Handles all basic functions for a group of motor based on
        internal units.
        Only position mode!

    Use:
        Only used by wrapper class (subclass) 'MotorGroup'
    """

    def __init__(self, net, conf, motor_list):
        self.net = net
        self.active = False
        self.velocity = conf.motor_params[0]['default_velocity_pp']
        self.acceleration = conf.motor_params[0]['default_acceleration']
        self.group = []
        self.group_len = 0
        if len(motor_list) == 0:
            print("Motor group is empty")
            return
        for mot in motor_list:
            if mot.is_active():
                self.group.append(mot)
        if len(motor_list) == len(self.group):
            self.active = True
            self.velocity = self.group[0].velocity
            self.acceleration = self.group[0].acceleration
            self.group_len = len(self.group)
            print("Motor group contains", self.group_len, "active motors")
        else:
            print("Motor group is inactive!")

    def is_active(self):
        return self.active
    
    def get_group_length(self):
        return self.group_len

    def is_rotating(self):
        time.sleep(0.2)
        state = False
        for mot in self.group:
            if mot.status & 0x4000:
                state = True
                break
        return state
    
    def get_internal_position(self):
        self.net.sync.transmit()
        time.sleep(0.1)
        position = []
        for mot in self.group:
            position.append(mot.position)
        return position

    def move_position_internal(self, position, velocity = None,
                               acceleration = None):
        if velocity:
            if velocity != self.velocity:
                self.velocity = velocity
                obj = 'Profile Velocity in pp-mode 1'
                for mot in self.group:
                    mot.node.sdo[obj].raw = velocity
        if acceleration:
            if acceleration != self.acceleration:
                self.acceleration = acceleration
                obj1 = 'Profile Acceleration 1'
                obj2 = 'Profile Deceleration 1'
                for mot in self.group:
                    mot.node.sdo[obj1].raw = acceleration
                    mot.node.sdo[obj2].raw = acceleration
        print("Motor group: Position mode")
        k = 0
        for mot in self.group:
            mot.node.rpdo[2]['Modes of Operation 1'].raw = 1
            mot.node.rpdo[2].transmit()
            mot.node.rpdo[3]['Target Position 1'].raw = position[k]
            mot.node.rpdo[3].transmit()
            mot.node.rpdo[1]['Controlword 1'].raw = 31
            k += 1
        # Start rotation
        for mot in self.group:
            mot.node.rpdo[1].transmit()

    def change_velocity_internal(self, velocity):
        self.velocity = velocity
        for mot in self.group:
            mot.node.sdo['Profile Velocity in pp-mode 1'].raw = velocity

    def move_end(self):
        for mot in self.group:
            mot.node.rpdo[1]['Controlword 1'].raw = 0x0F
            mot.node.rpdo[1].transmit()

    def move_steps_internal(self, steps):
        self.net.sync.transmit()
        time.sleep(0.1)
        for mot in self.group:
            pos = mot.position + steps
            mot.node.rpdo[2]['Modes of Operation 1'].raw = 1
            mot.node.rpdo[2].transmit()
            mot.node.rpdo[3]['Target Position 1'].raw = pos
            mot.node.rpdo[3].transmit()
            mot.node.rpdo[1]['Controlword 1'].raw = 0x1F
        for mot in self.group:
            mot.node.rpdo[1].transmit()
        while self.is_rotating(): pass
        self.move_end()
 
    def move_halt(self):
        # Stops rotation immediately
        for mot in self.group:
            mot.node.rpdo[1]['Controlword 1'].raw = 0x10F
        for mot in self.group:
            mot.node.rpdo[1].transmit()
        print("Motor group: HALT")
        while self.is_rotating(): pass
        self.net.sync.transmit()
        time.sleep(0.1)
        for mot in self.group:
            mot.node.rpdo[3]['Target Position 1'].raw = mot.position
            mot.node.rpdo[1]['Controlword 1'].raw = 0x1F
            mot.node.rpdo[3].transmit()
            mot.node.rpdo[1].transmit()
        self.move_end()

#-----------------------------------------------------------------------------

class AllMotorsDriver:
    """
    AllMotorsDriver:  Always initialized by subclass 'AllMotors'!
        Basic methods concerning all motors
        
    Use:
        Only used by wrapper class (subclass) 'AllMotors'
    """

    def __init__(self, net):
        self.net = net
    
    def set_status(self, state, motor_list):
        if state == 'OPERATIONAL':
            self.net.nmt.state = state
            for mot in motor_list:
                if mot.is_active():
                    mot.node.go_to_operation_enabled()
            print("All motors OPERATIONAL")
        elif state == 'PRE-OPERATIONAL':
            for mot in motor_list:
                if mot.is_active():
                    mot.node.shutdown()
                    mot.node.sdo[0x6041].raw
            self.net.nmt.state = state
            print("All motors PRE-OPERATIONAL")
    
    def get_internal_position(self, motor_list):
        self.net.sync.transmit()
        time.sleep(0.1)
        positions = []
        for mot in motor_list:
            if mot.is_active():
                positions.append(mot.position)
            else:
                positions.append(0)
        return positions

#-----------------------------------------------------------------------------

class PGauge:
    """
    PGauge:
        Methods for reading Pressure gauge values
        
    Use:
        from canbus import PGauge
        ...
        pg = PGauge(net,config)
        ...
        pg.start()         - Starts P gauge values transmission
        pg.stop()          - Stops P gauge values transmission
        
        pg.is_running()    [BOOLEAN]
        pg.get_pvalue()    [INT]
        ...
        pg.end_pgauge()    - Ending the P gauge communication (mandatory!)
    """
 
    def __init__(self, net, conf):
        self.net      = net
        self.bus      = None
        self.node     = conf.pgauge_params['node']
        self.eds      = conf.pgauge_params['eds']
        self.digit    = conf.pgauge_params['dec_digits']
        self.offset   = conf.pgauge_params['offset']
        self.type     = conf.pgauge_params['pdo_type']
        self.timer    = conf.pgauge_params['pdo_timer']
        self.active   = False
        self.running  = False
        self.pdo_id   = 0
        
        # Add node to network
        self.pg = canopen.RemoteNode(self.node, self.eds)
        net.add_node(self.pg)
        print("P gauge assigned to node " + str(self.node) + 
              " added to network ")
        
        # Can bus instance
        self.bus = self.net.bus

        # Is P gauge active?
        try:
            self.pg.sdo[0x1000].raw
            self.active = True
        except SdoCommunicationError:
            self.active = False
            print("No communication with P gauge!")

        # Load SDO parameters
        if self.active == True:
            self.pg.sdo['Decimal digits PV'][1].raw      = self.digit
            self.pg.sdo['Transmit PDO parameter'][2].raw = self.type
            self.pg.sdo['Transmit PDO parameter'][5].raw = self.timer
            self.pdo_id = self.pg.sdo[0x1800][1].raw
        time.sleep(0.1)

        def receive_PDO(self, data, timestamp):
            b = data[:4] 
            val = int.from_bytes(b, byteorder = 'little')
            sign = data[3] & 0x80
            if sign == 0x80:
                val -= 4294967296
            f = open("dummy", "w")
            f.write(str(val))
            f.close()

        net.subscribe(self.pdo_id, receive_PDO)
        
    def is_active(self):
        return self.active

    def start(self):
        self.pg.nmt.state = 'OPERATIONAL'
        self.running  = True
        print("PDO enabled")
              
    def stop(self):
        self.pg.nmt.state = 'PRE-OPERATIONAL'
        self.running = False
        print("PDO disabled")
           
    def is_running(self):
        return self.running
    
    def get_pvalue(self):
        f = open("dummy","r")
        val = f.read()
        f.close()
        val = int(val) + self.offset
        return val

    def end_pgauge(self):
        self.net.unsubscribe(self.pdo_id)

