#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper for Driver classes

Created on Tue Apr  9 09:11:08 2024

@author: Eric Reusser
"""

from modules.canbus import MotorDriver, MotorGroupDriver, AllMotorsDriver

#-----------------------------------------------------------------------------

class Motor(MotorDriver):
    """
    Motor:  Inherits class 'MotorDriver'
        Handles all motor functions for a single motor
        
    Use:
        from motor import Motor
        ...
        motor = Motor(motor_num, network, config)
                      motor_num:    Motor number (see Configuration file)
                      network:      CAN bus network
                      config:       Configuration

    Methods based on physical units:
        is_active()                 [BOOLEAN]
        is_rotating()               [BOOLEAN]
        set_zero()                  - Set motor position to zero
        get_position()              [FLOAT]
        get_default_velocity        [FLOAT]

      Position mode:
        move_position(position, velocity [opt], acceleration [opt])
        change_velocity(velocity)
        move_end()                  - End of position mode
        move_steps(step)
        move_halt()                 - Interrupt rotation during position mode

      Velocity mode:
        move_velocity(velocity, acceleration [opt])
        change_velocity(velocity)
        move_stop()                 - Stops velocity mode
    
    Methods based on internal units:
        get_internal_position()     [INT]
        
        move_position_internal(position, velocity [opt], acceleration [opt])
        change_velocity_pp(velocity)
        move_end()                  - End of position mode
        move_steps_internal(nsteps)
        move_halt()                 - Interrupt rotation during position mode
        
        move_velocity_internal(velocity, acceleration [opt])
        change_velocity_pv(velocity)
        move_stop()                 - Stops velocity mode
    """
    
    def __init__(self, n, net, conf):
        self.param = conf.motor_params[n]
        self.f  = self.param['full_step']
        self.f *= 2**self.param['Microstep Resolution 1']
        self.offset = 0
        self.pitch  = self.param['pitch']
        self.vdef   = self.param['default_velocity_pp']
        v = int(self.f * self.vdef)
        self.vdef  *= self.pitch
        self.vmin   = conf.global_params['velocity_min'] * self.pitch
        self.vmax   = conf.global_params['velocity_max'] * self.pitch
        self.factor = float(self.f) / self.pitch
        self.pmin   = self.param['pos_limit_min']
        self.pmax   = self.param['pos_limit_max']
        self.pdef   = self.param['pos_default_value']
        self.pstp   = self.param['pos_step']
        self.mode   = True    # True: posisition mode, False: velocity mode
        a = int(self.f * self.param['default_acceleration'])
        super().__init__(net, conf.sdo, self.param, v, a)

    def get_velocity_params(self):
        return self.vdef, self.vmin, self.vmax
    
    def get_abs_pos_params(self):
        return self.pdef, self.pmin, self.pmax, self.pstp
        
    def set_zero(self):
        self.offset = self.position
        print("Set ZERO position")
    
    #TODO
    # def set_value(self, pos):
    #     # pos is in steps, thus pos has to be calculated: f(spinB.value(), axis_specific_param)
    #     pos = self.position
    #     print(f"Set position to {pos}")
        

    def get_position(self):
        self.get_internal_position()
        return float(self.position - self.offset) / self.factor
    
    def move_position(self, pos, v = None):
        pos = int(pos * self.factor) + self.offset
        if v: v = int(v * self.factor)
        self.mode = True
        self.move_position_internal(pos, v)

    def move_steps(self, step):
        print("Motor " + self.name + ": Step =", step)
        steps = int(step * self.f)
        self.move_steps_internal(steps)

    def move_velocity(self, v):
        v = int(v * self.factor)
        self.mode = False
        self.move_velocity_internal(v)
    
    def change_velocity(self, v):
        print("Motor " + self.name + ": Change v =", v)
        v = int(v * self.factor)
        if self.mode:
            self.change_velocity_pp(v)
        else:
            self.change_velocity_pv(v)
            
#-----------------------------------------------------------------------------

class MotorGroup(MotorGroupDriver):
    """
    MotorGroup:  Inherits class 'MotorGroupDriver'
        Handles all functions for a group motors
        Only position mode!

    Use:
        from motor import Motor
        ...
        motor = Motor(network, config, motor_list, motor_group_names)
                      network:      CAN bus network
                      config:       Configuration
                      motor_list:   List of all motors (from class AllMotors)
                      motor_group_names: List of grouped motor names

    Methods based on physical units:
        is_active()                 [BOOLEAN]
        is_rotating()               [BOOLEAN]
        is_same_position()          [BOOLEAN]  - All motors have same position
        set_zero()                             - Set group position to zero
        get_position()              [List of FLOAT]
        get_group_length()          [INT]

      Position mode:
        move_position(position, velocity [opt], acceleration [opt])
        change_velocity(velocity)
        move_end()                  - End of position mode
        move_steps(step)
        move_halt()                 - Interrupt rotation during position mode

    Methods based on internal units:
        get_internal_position()     [List of INT]

        move_position_internal(position, velocity [opt], acceleration [opt])
        change_velocity_internal(velocity)
        move_end()                  - End of position mode
        move_steps_internal(nsteps)
        move_halt()                 - Interrupt rotation during position mode
    """
    
    def __init__(self, net, conf, motor_all, motor_group):
        motor_list = []
        for i in range(len(motor_group)):
            motor_list.append(motor_all[motor_group[i]])
        super().__init__(net, conf, motor_list)

    def get_position(self):
        self.get_internal_position()
        position = []
        for mot in self.group:
            pos = float(mot.position - mot.offset) / mot.factor
            position.append(pos)
        return position
    
    def is_same_position(self):
        pos0 = self.group[0].position - self.group[0].offset
        for mot in self.group:
            pos = mot.position - mot.offset
            if abs(pos-pos0) > 1:
                return False
        return True

    def set_same_position(self):
        mean = 0
        for mot in self.group:
            mean += mot.position - mot.offset
        mean = int(float(mean) / float(len(self.group)))
        for mot in self.group:
            mot.offset = mot.position - mean

    def set_zero(self):
        print("Set ZERO position")
        for mot in self.group:
            mot.offset = mot.position

    def move_position(self, pos, v = None):
        position = []
        for mot in self.group:
            position.append(int(pos * mot.factor) + mot.offset)
        if v: v = int(v * self.group[0].factor)
        self.move_position_internal(position, v)

    def change_velocity(self, v):
        print("Motor group: Change v =", v)
        v = int(v * self.group[0].factor)
        self.change_velocity_internal(v)

    def move_steps(self, step):
        print("Motor group: Step =", step)
        steps = int(step * self.group[0].f)
        self.move_steps_internal(steps)
            
#-----------------------------------------------------------------------------

class AllMotors(AllMotorsDriver):
    """
    AllMotors:  Inherits class 'AllMotorsDriver'
        Functions that adress all motors

    Use:
        from motor import AllMotors
        ...
        all = AllMotors(network, config)
                      network:      CAN bus network
                      config:       Configuration

    Methods:
        set_status(status)          Status: 'PRE-OPERATIONAL, 'OPERATIONAL'
        get_motor_names()           [List of Strings]
        get_motor_list()            [List of Motor]
        get_position()              [List of FLOAT]     (physical units)
        get_internal_position()     [List of INT]       (internal units)
    """

    def __init__(self, net, conf):
        self.n = conf.global_params['number_of_motors']
        super().__init__(net)
        self.motor_names = []
        self.motor_list  = []
        for i in range(self.n):
            mot = Motor(i, net, conf)
            self.motor_names.append(mot.name)
            self.motor_list.append(mot)
        print("All motors INITIALIZED")

    def set_status(self, state):
        super().set_status(state, self.motor_list)
    
    def get_motor_names(self):
        return self.motor_names
    
    def get_motor_list(self):
        return self.motor_list

    def get_internal_position(self):
        pos = super().get_internal_position(self.motor_list)
        return pos

    def get_position(self):
        self.get_internal_position()
        positions = []
        for mot in self.motor_list:
            pos = float(mot.position - mot.offset) / mot.factor
            positions.append(pos)
        return positions
        
        
        
        
