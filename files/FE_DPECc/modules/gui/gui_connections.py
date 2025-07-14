# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 17:38:27 2023
@author: pschw

Adapted to CAN bus on Mai 7 2024 by Eric Reusser
"""

''' DONE: 
        - get init values from external file with init_stats
        - connected permanent and when pushed for s and pressure
        - changed name of spinB_fine/coarse to dspinB...
        - added connections for absolute pos for legs (commented)
        - added connections for set_0 for legs and x (commented, see TODO)
        - added connections for halt (commented, see TODO)
        - changed print statement to "terminal" output in gui'''
    

import sys, time, threading

from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QKeyEvent, QFont
from PyQt5.QtCore import Qt
from modules.gui.main_window_ui import Ui_MainWindow

# import package for external file management 
import pandas as pd 

from modules.config import Config
from modules.canbus import CanBus
from modules.motor  import AllMotors, MotorGroup


### Configuration, Initialization of all motors

conf = Config('fedpecc.config')
bus  = CanBus(conf.bus_params)
net  = bus.connect()

all_motors  = AllMotors(net, conf)

mot_msg = "Motors available & initialized: "
for i in range(conf.global_params['number_of_motors']):
    if all_motors.get_motor_list()[i].is_active():
        mot_msg += all_motors.get_motor_names()[i] + " "

### Heartbeat, Autosave

heartbeat = 1./conf.global_params['heartbeat_freq']
autosave  =  conf.global_params['autosave']

### Active single motor, active motor group, all motors
motor = None                    # Single motor
motor_group_list = []           # List of leg motor numbers (see config-file)
motor_group = None              # Motor group
motor_list  = all_motors.motor_list
mode        = True
direction   = True
halt        = False
speed       = 1.
abs_pos     = [0., 0., 0., 0., 0.]  # Absolute target positions:
                                    # legs, x, pr, cr, s

# read position backup matrix from external file # TODO: make work 
backup = pd.read_csv("/home/pi2mpp/Desktop/3105_HEIDELBERG/FE_DPECc/modules/gui/backup_positions", delimiter = '\t')

### Setup GUI, handle all GUI widgets

class Window(QMainWindow, Ui_MainWindow):
    '''This custom class inherits from QMainWindow class and the custom 
    Ui_MainWindow class from main_window_ui.py file. That file is created 
    from main_window.ui using the pyuic5 command line program, e.g.:
    pyuic5 -x main_window.ui -o main_window_ui.py
    '''

    def __init__(self, parent=None):
        global conf, all_motors
        self.nleg = conf.global_params['number_of_leg_motors']
        super().__init__(parent)

        self.active_label_list = []
        # Values of positions in LCD display: shadow variable
        self.lcd_val = [[0. for k in range(6)] for i in range(8)]

        self.setupUi(self)
        self.setWindowTitle('FE_DPECc_GUI')
        self.setup_default_values()
        self.setup_default_buttons()
        #self.refresh_lcd_displays(False)
        self.connectSignalsSlots()
        self.show()

        ### Turn all motors ON
        self.terminal.appendPlainText(mot_msg)
        all_motors.set_status('OPERATIONAL')
        self.terminal.appendPlainText("All motors OPERATIONAL")

    ### Setup defaults
    
    def setup_default_values(self):
        global conf, motor_list
        ### User input values (with allowed min-max range)
        self.radioB_permanent_when_pushed.setChecked(True)
        self.radioB_all_motors.setChecked(True)
        # set Min's for Keyboard control
        self.dspinB_fine.setMinimum(conf.global_params['step_fine_min'])
        self.dspinB_coarse.setMinimum(conf.global_params['step_coarse_min'])
        # set Min, Max, Default value for speed and for aboslute position
        self.set_speed_params(motor_list[0])
        self.set_abs_pos_params(0, motor_list[0])
        self.set_abs_pos(0)
        # Store lists for checkboxes and radioButtons:
        self.legs_boxlist = [self.checkB_zbr, self.checkB_zbc, self.checkB_zdr, self.checkB_zdc]
        self.legs_radioBlist = [self.radioB_all_motors, self.radioB_single_motor]
        # list of all labels:
        self.label_list = [self.label_zbr, self.label_zbc, self.label_zdr, self.label_zdc,
                           self.label_x, self.label_pr, self.label_cr, self.label_s]
        # list of all LCD`s:
        self.lcd_matrix =  [[self.lcd_current_zbr, self.lcd_beam_zbr,   self.lcd_transport_zbr, 0, 0, 0],
                            [self.lcd_current_zbc, self.lcd_beam_zbc,   self.lcd_transport_zbc, 0, 0, 0],
                            [self.lcd_current_zdr, self.lcd_beam_zdr,   self.lcd_transport_zdr, 0, 0, 0],
                            [self.lcd_current_zdc, self.lcd_beam_zdc,   self.lcd_transport_zdc, 0, 0, 0],
                            [self.lcd_current_x,   self.lcd_working_x,  self.lcd_test_x,        0, 0, 0],
                            [self.lcd_current_pr,  self.lcd_working_pr, self.lcd_test_pr,       0, 0, 0],
                            [self.lcd_current_cr,  self.lcd_ion_cr,     self.lcd_raman_cr, self.lcd_3_cr,
                             self.lcd_4_cr,        self.lcd_5_cr,       self.lcd_6_cr],
                            [self.lcd_current_s,   self.lcd_1_s,        self.lcd_2_s,      self.lcd_3_s,
                             self.lcd_4_s,         self.lcd_cal_1_s,    self.lcd_cal_2_s]]
        # create motor_pos_matrix as df to facilitate the interaction with the positions/backup df
        # holds all the positions of the motors 
        #self.motor_pos_matrix = pd.DataFrame()
        # set up 0 matrix with up to 6 positions for every motor in motor_list  
        for i in range(6):
            pass
            #self.motor_pos_matrix[f'position: {i}'] = [0 for i in range(len(motor_list))] 

        # Set default motor(s) that is active initially:
        self.reset_active_motors()
        self.all_legs_setup()

    def set_speed_params(self, motor):
        global speed
        velocity = motor.get_velocity_params()
        speed = velocity[0]
        print(velocity[0], velocity[1], velocity[2])
        self.dspinB_speed.setMinimum(velocity[1])
        self.dspinB_speed.setMaximum(velocity[2])
        self.dspinB_speed.setValue(velocity[0])
        
    def set_abs_pos_params(self, idx, motor):
        pos = motor.get_abs_pos_params()
        if idx == 0:
            self.dspinB_mm_axis_legs.setMinimum(pos[1])
            self.dspinB_mm_axis_legs.setMaximum(pos[2])
            self.dspinB_mm_axis_legs.setSingleStep(pos[3])
            self.dspinB_mm_axis_legs.setValue(pos[0])
        elif idx == 1:
            self.dspinB_mm_axis_x.setMinimum(pos[1])
            self.dspinB_mm_axis_x.setMaximum(pos[2])
            self.dspinB_mm_axis_x.setSingleStep(pos[3])
            self.dspinB_mm_axis_x.setValue(pos[0])
        elif idx == 2:
            self.dspinB_deg_axis_pr.setMinimum(pos[1])
            self.dspinB_deg_axis_pr.setMaximum(pos[2])
            self.dspinB_deg_axis_pr.setSingleStep(pos[3])
            self.dspinB_deg_axis_pr.setValue(pos[0])
        elif idx == 3:
            self.dspinB_deg_axis_cr.setMinimum(pos[1])
            self.dspinB_deg_axis_cr.setMaximum(pos[2])
            self.dspinB_deg_axis_cr.setSingleStep(pos[3])
            self.dspinB_deg_axis_cr.setValue(pos[0])
        elif idx == 4:
            self.dspinB_mm_axis_s.setMinimum(pos[1])
            self.dspinB_mm_axis_s.setMaximum(pos[2])
            self.dspinB_mm_axis_s.setSingleStep(pos[3])
            self.dspinB_mm_axis_s.setValue(pos[0])


    def setup_default_buttons(self):
        self.radioB_permanent_when_pushed.setChecked(True)
        self.radioB_all_motors.setChecked(True)
    
    ###   BUTTON SIGNAL AND SLOT CONNECTIONS
    
    def connectSignalsSlots(self):
        
        ##  GENERAL GUI BEHAVIOUR  ##
        # Leg motors checkability: single_motor active -> checkboxes enabled 
        self.radioB_single_motor.clicked.connect(self.enable_motor_selection)
        # All_motors active -> checkboxes for individual legs: uncheckable
        self.radioB_all_motors.clicked.connect(self.all_legs_setup)
        # refresh speed when value is changed:
        self.dspinB_speed.valueChanged.connect(self.change_velocity)
        # quit application and end program:
        self.pushB_quit.clicked.connect(self.closing)

        ##  MOTOR SELECTION  ##
        # Activate correct motor(s) on tab change:
        self.tabWidget.currentChanged.connect(self.reset_active_motors)
        # Leg motor selection:
        # all_motors radioB clicked -> all leg motors selected
        self.radioB_all_motors.clicked.connect(lambda: self.refresh_motor_list(0))
        # active_motor list refreshed: single_motor radioB and 
        # single_motor checkBoxes are clicked:
        self.checkB_zbr.toggled.connect(lambda: self.refresh_motor_list(1))
        self.checkB_zbc.toggled.connect(lambda: self.refresh_motor_list(1))
        self.checkB_zdr.toggled.connect(lambda: self.refresh_motor_list(1))
        self.checkB_zdc.toggled.connect(lambda: self.refresh_motor_list(1))

        ##  STORE BUTTONS  ##
        # store_pos argument represents the column index of the store_lcd matrix:
        self.pushB_store_A.clicked.connect(lambda: self.store_pos(1))
        self.pushB_store_B.clicked.connect(lambda: self.store_pos(2))
        self.pushB_store_C.clicked.connect(lambda: self.store_pos(3))
        ## SAVE AND LOAD POSITIONS TO FILE BUTTONS ##
        self.pushB_savepos.clicked.connect(self.save_pos)
        self.pushB_loadpos.clicked.connect(self.load_pos)
        
        ##  GOTO BUTTONS  ##
        # goto argument represents the coulmn index of the store_lcd matrix:
        self.pushB_go_to_0.clicked.connect(lambda: self.goto(0))
        self.pushB_go_to_A.clicked.connect(lambda: self.goto(1))
        self.pushB_go_to_B.clicked.connect(lambda: self.goto(2))
        self.pushB_go_to_C.clicked.connect(lambda: self.goto(3))
       
        ##  ABSOLUTE POSITION BUTTONS  ##
        self.dspinB_mm_axis_legs.valueChanged.connect(lambda: self.set_abs_pos(0))
        self.dspinB_mm_axis_x.valueChanged.connect(lambda: self.set_abs_pos(1))
        self.dspinB_deg_axis_pr.valueChanged.connect(lambda: self.set_abs_pos(2))
        self.dspinB_deg_axis_cr.valueChanged.connect(lambda: self.set_abs_pos(3))
        self.dspinB_mm_axis_s.valueChanged.connect(lambda: self.set_abs_pos(4))

        # move to abs position
        self.pushB_start_legs.clicked.connect(lambda: self.abs_pos(0))
        self.pushB_start_x.clicked.connect(lambda: self.abs_pos(1))
        self.pushB_start_pr.clicked.connect(lambda: self.abs_pos(2))
        self.pushB_start_cr.clicked.connect(lambda: self.abs_pos(3))
        self.pushB_start_s.clicked.connect(lambda: self.abs_pos(4))
        
        ## HALT
        self.pushB_halt.clicked.connect(self.halt)

        ##  PERMANENT MOVE  ##
        # Z: Not allowed!
        # X: 
        self.pushB_forwards_x1.clicked.connect(self.permanent_right)
        self.pushB_backwards_x1.clicked.connect(self.permanent_left)
        self.pushB_stop_x.clicked.connect(self.stop_motor)
        # PR:
        self.pushB_clockwise_pr1.clicked.connect(self.permanent_right)
        self.pushB_counterclockwise_pr1.clicked.connect(self.permanent_left)
        self.pushB_stop_pr.clicked.connect(self.stop_motor)
        # CR:
        self.pushB_clockwise_cr1.clicked.connect(self.permanent_right)
        self.pushB_counterclockwise_cr1.clicked.connect(self.permanent_left)
        self.pushB_stop_cr.clicked.connect(self.stop_motor)
        # S:
        self.pushB_forwards_s1.clicked.connect(self.permanent_right)
        self.pushB_backwards_s1.clicked.connect(self.permanent_left)
        self.pushB_stop_s.clicked.connect(self.stop_motor)
        # Pressure:
        self.pushB_forwards_pressure1.clicked.connect(self.permanent_right)
        self.pushB_backwards_pressure1.clicked.connect(self.permanent_left)
        self.pushB_stop_pressure.clicked.connect(self.stop_motor)

        ##  WHEN PUSHED MOVE  ##
        # Z: Not allowed!
        # X:
        self.pushB_forwards_x2.pressed.connect(self.permanent_right)
        self.pushB_forwards_x2.released.connect(self.stop_motor)
        self.pushB_backwards_x2.pressed.connect(self.permanent_left)
        self.pushB_backwards_x2.released.connect(self.stop_motor)
        # PR:
        self.pushB_clockwise_pr2.pressed.connect(self.permanent_right)
        self.pushB_clockwise_pr2.released.connect(self.stop_motor)
        self.pushB_counterclockwise_pr2.pressed.connect(self.permanent_left)
        self.pushB_counterclockwise_pr2.released.connect(self.stop_motor)
        # CR:
        self.pushB_clockwise_cr2.pressed.connect(self.permanent_right)
        self.pushB_clockwise_cr2.released.connect(self.stop_motor)
        self.pushB_counterclockwise_cr2.pressed.connect(self.permanent_left)
        self.pushB_counterclockwise_cr2.released.connect(self.stop_motor)
        # S:
        self.pushB_forwards_s2.pressed.connect(self.permanent_right)
        self.pushB_forwards_s2.released.connect(self.stop_motor)
        self.pushB_backwards_s2.pressed.connect(self.permanent_left)
        self.pushB_backwards_s2.released.connect(self.stop_motor)
        # Pressure:
        self.pushB_forwards_pressure2.pressed.connect(self.permanent_right)
        self.pushB_forwards_pressure2.released.connect(self.stop_motor)
        self.pushB_backwards_pressure2.pressed.connect(self.permanent_left)
        self.pushB_backwards_pressure2.released.connect(self.stop_motor)
       
        ## SET to 0
        self.pushB_set_0_legs.clicked.connect(self.set_zero)
        self.pushB_set_0_x.clicked.connect(self.set_zero)
        self.pushB_set_0_pr.clicked.connect(self.set_zero)
        self.pushB_set_0_cr.clicked.connect(self.set_zero)
        self.pushB_set_0_s.clicked.connect(self.set_zero)
        self.pushB_set_0_pressure.clicked.connect(self.set_zero)
        
    ###   KEYBOARD CONTROL   ###
    
    def keyPressEvent(self, event: QKeyEvent) -> None: 
        # event gets defined and keys are specified below 
        if self.radioB_key_control.isChecked() == True:
            key_pressed = event.key()
            if key_pressed == Qt.Key_S:
                self.fine_step_left()
            if key_pressed == Qt.Key_A:
                self.coarse_step_left()
            if key_pressed == Qt.Key_W:
                self.fine_step_right()
            if key_pressed == Qt.Key_D:
                self.coarse_step_right()
            
    ###   LCD TABLE FUNCTIONS   ###
    
    def motor_group_is_ready(self, message):
        global motor_group
        if motor_group.is_active():
            if motor_group.get_group_length() == self.nleg:
                if motor_group.is_same_position():
                    return True
                else:
                    msg  = "Not all leg motors at same position! -> "
                    msg += message
                    self.terminal.appendPlainText(msg)
                    print(msg)
                    return False
            else:
                msg  = "Not all leg motors selected! -> "
                msg += message
                self.terminal.appendPlainText(msg)
                print(msg)
                return False
        else:
            msg  = "Not all leg motors active! -> "
            msg += message
            self.terminal.appendPlainText(msg)
            print(msg)
            return False
        
    def store_pos(self, pos_idx):
        global motor, motor_group, all_motors
        if motor_group:
            if self.motor_group_is_ready("Store position disabled"):
                if pos_idx == 1 or pos_idx == 2:
                    for i in range(4):
                        self.lcd_val[i][pos_idx] = self.lcd_val[i][0]
                        self.lcd_matrix[i][pos_idx].display(self.lcd_val[i][0])
        if motor:
            if motor.name == 'X' and (pos_idx == 1 or pos_idx == 2):
                self.lcd_val[4][pos_idx] = self.lcd_val[4][0]
                self.lcd_matrix[4][pos_idx].display(self.lcd_val[4][0])
            elif motor.name == 'PR' and (pos_idx == 1 or pos_idx == 2):
                self.lcd_val[5][pos_idx] = self.lcd_val[5][0]
                self.lcd_matrix[5][pos_idx].display(self.lcd_val[5][0])
            elif motor.name == 'CR':
                self.lcd_val[6][pos_idx] = self.lcd_val[6][0]
                self.lcd_matrix[6][pos_idx].display(self.lcd_val[6][0])
            elif motor.name == 'S':
                self.lcd_val[7][pos_idx] = self.lcd_val[7][0]
                self.lcd_matrix[7][pos_idx].display(self.lcd_val[7][0])
            # elif motor.name == 'Oil':
            #     self.lcd_val[8][pos_idx] = self.lcd_val[8][0]
            #     self.lcd_matrix[8][pos_idx].display(self.lcd_val[8][0])



    def refresh_lcd_displays(self, save):
        '''Update the status LCDs.'''
        global all_motors
        position = all_motors.get_position()
        print("Position: ", position)
        QApplication.processEvents()
        # override current position of active motor (active tab)
        idx_list = []
        if motor_group:
            idx_list = [0, 1, 2, 3]
        if motor:
            idx_list = [motor_list.index(motor)]
        for i in idx_list:
            self.lcd_val[i][0] = position[i]
            self.lcd_matrix[i][0].display(position[i])
        ## Save positions to file
        if save: # TODO yields: segmentation fault due to termial display issues
            for i in range(8):
                backup.iloc[i] = self.lcd_val[i]
            backup.to_csv('/home/pi2mpp/Desktop/3105_HEIDELBERG/FE_DPECc/modules/gui/backup_positions', sep='\t', index= False)
            # self.terminal.appendPlainText('conducted position backup to file!')
            
    ###   CHECKABILITY   ###
 
    def enable_motor_selection(self):
        # uncheck the checkBoxes for individual motor selection and 
        # make checkboxes for leg motors checkable
        for box in self.legs_boxlist:
            box.setChecked(False)
            box.setCheckable(True)
            box.setEnabled(True) 

    def all_legs_setup(self):
        # unchecking the checkBoxes of the individual motor selection and
        # setting checkBoxes uncheckable 
        for box in self.legs_boxlist:
            box.setChecked(True)
            box.setEnabled(False)

    ###   MODULE MANAGEMENT   ###

    def reset_active_motors(self):
        '''Reset list of active motors to tab default.'''
        if self.tabWidget.currentIndex() == 0:          # Legs
            # set buttons correctly:
            self.radioB_all_motors.setChecked(True)
            self.radioB_single_motor.setChecked(False)
            self.all_legs_setup()
            # refresh active module list:
            self.refresh_motor_list(0)
        elif self.tabWidget.currentIndex() == 1:        # X
            self.refresh_motor_list(2)
        elif self.tabWidget.currentIndex() == 2:        # PR
            self.refresh_motor_list(3)
        elif self.tabWidget.currentIndex() == 3:        # CR
            self.refresh_motor_list(4)
        elif self.tabWidget.currentIndex() == 4:        # S
            self.refresh_motor_list(5)
        elif self.tabWidget.currentIndex() == 5:        # Pressure
            self.refresh_motor_list(6)
        
    def refresh_motor_list(self, select):
        global motor, motor_group
        for label in self.label_list:
            label.setFont(QFont('Arial', 20, weight=QFont.Normal))
            label.setStyleSheet('color: black')
        self.active_label_list = []
        
        if select == 0:
            motor = None
            motor_group_list = [0, 1, 2, 3]
            motor_group = MotorGroup(net, conf, motor_list, motor_group_list)
            self.active_label_list = [self.label_zbr, self.label_zbc, 
                                      self.label_zdr, self.label_zdc]
            self.set_speed_params(motor_list[0])
            self.set_abs_pos_params(0, motor_list[0])
            self.set_abs_pos(0)
            self.terminal.appendPlainText('Leg motors selected')

        if select == 1:
            motor = None
            motor_group_list = []
            self.active_label_list = []
            for box in self.legs_boxlist:
                if box.isChecked() == True:
                     if box == self.checkB_zbr:
                         motor_group_list.append(0)
                         self.active_label_list.append(self.label_zbr)
                     if box == self.checkB_zbc:  
                         motor_group_list.append(1)
                         self.active_label_list.append(self.label_zbc)
                     if box == self.checkB_zdr:                   
                         motor_group_list.append(2)
                         self.active_label_list.append(self.label_zdr)
                     if box == self.checkB_zdc:
                         motor_group_list.append(3)
                         self.active_label_list.append(self.label_zdc)
            motor_group = MotorGroup(net, conf, motor_list, motor_group_list)
            self.set_speed_params(motor_list[0])
            self.set_abs_pos_params(0, motor_list[0])
            self.set_abs_pos(0)
            if len(motor_group.group) < self.nleg:
                self.terminal.appendPlainText('ATTENTION! ' + \
                                              'Not all leg motors selected')

        if select == 2:
            motor = motor_list[4]
            motor_group = None
            self.active_label_list = [self.label_x]
            self.set_speed_params(motor)
            self.set_abs_pos_params(1, motor)
            self.set_abs_pos(1)
            self.terminal.appendPlainText('Motor X selected')
        if select == 3:
            motor = motor_list[5]
            motor_group = None
            self.active_label_list = [self.label_pr]
            self.set_speed_params(motor)
            self.set_abs_pos_params(2, motor)
            self.set_abs_pos(2)
            self.terminal.appendPlainText('Motor PR selected')
        if select == 4:
            motor = motor_list[6]
            motor_group = None
            self.active_label_list = [self.label_cr]
            self.set_speed_params(motor)
            self.set_abs_pos_params(3, motor)
            self.set_abs_pos(3)
            self.terminal.appendPlainText('Motor CR selected')
        if select == 5:
            motor = motor_list[7]
            motor_group = None
            self.active_label_list = [self.label_s]
            self.set_speed_params(motor)
            self.set_abs_pos_params(4, motor)
            self.set_abs_pos(4)
            self.terminal.appendPlainText('Motor S selected')
        if select == 6:
            motor = motor_list[8]
            motor_group = None 
            # self.active_label_list = [self.label_oil]
            self.set_speed_params(motor)
            self.terminal.appendPlainText('Motor Pressure selected')
        for label in self.active_label_list:
            label.setFont(QFont('Arial', 20, weight=QFont.Bold))
            label.setStyleSheet('color: yellow')

    ### MOVEMENT CONTROL
    
    def wait_end_rotation(self):
        global halt, mode, autosave
        for label in self.active_label_list:    
            label.setStyleSheet('color: red')
        cnt = 0
        if motor:
            print("Thread started")
            while motor.is_rotating():
                time.sleep(heartbeat)
                cnt += 1
                if cnt == autosave:
                    self.refresh_lcd_displays(True)
                    cnt = 0
                else:
                    self.refresh_lcd_displays(False)
            self.refresh_lcd_displays(True)
        elif motor_group:
            print("Thread started")
            while motor_group.is_rotating():
                time.sleep(heartbeat)
                cnt += 1
                if cnt == autosave:
                    self.refresh_lcd_displays(True)
                    cnt = 0
                else:
                    self.refresh_lcd_displays(False)
            self.refresh_lcd_displays(True)
            if halt:
                motor_group.set_same_position()
                halt = False
        for label in self.active_label_list:    
            label.setStyleSheet('color: yellow')
            
    ### POSITION MODE
    
    def goto(self, pos_idx):
        '''Motor moves to the stored module_position on index pos_idx.'''
        global motor, motor_group, mode, speed, heartbeat
        mode = True
        if speed < 0.:
            speed = -speed
        if motor_group and motor_group.is_active():
            if self.motor_group_is_ready("Movement disabled"):
                if pos_idx == 0:
                    position = 0.
                elif pos_idx == 1 or pos_idx == 2:
                    position = self.lcd_val[0][pos_idx]
                motor_group.move_position(position, speed)
                threading.Thread(target = self.wait_end_rotation).start()
                motor_group.move_end()
        if motor and motor.is_active():
            if pos_idx == 0:
                position = 0.
            elif motor.name == 'X' and (pos_idx == 1 or pos_idx == 2):
                position = self.lcd_val[4][pos_idx]
            elif motor.name == 'PR' and (pos_idx == 1 or pos_idx == 2):
                position = self.lcd_val[5][pos_idx]
            elif motor.name == 'CR':
                position = self.lcd_val[6][pos_idx]
            elif motor.name == 'S':
                position = self.lcd_val[7][pos_idx]
            else: return
            motor.move_position(position, speed)
            threading.Thread(target = self.wait_end_rotation).start()
            motor.move_end()
        
    def set_zero(self):
        if motor:
            motor.set_zero()
        elif motor_group:
            if motor_group.get_group_length() == self.nleg:
                motor_group.set_zero()
            else:
                msg = "Set to 0: Only available, if all leg motors active!"
                self.terminal.appendPlainText(msg)
        self.refresh_lcd_displays(True)
        
    def set_abs_pos(self, index):
        global abs_pos
        if index == 0:
            abs_pos[0] = self.dspinB_mm_axis_legs.value()
        elif  index == 1:
            abs_pos[1] = self.dspinB_mm_axis_x.value()
        elif  index == 2:
            abs_pos[2] = self.dspinB_deg_axis_pr.value()
        elif  index == 3:
            abs_pos[3] = self.dspinB_deg_axis_cr.value()
        elif  index == 4:
            abs_pos[4] = self.dspinB_mm_axis_s.value()
    
    def abs_pos(self, index):
        global abs_pos, speed, mode
        mode = True
        if index == 0:
            if motor_group and motor_group.is_active():
                if self.motor_group_is_ready("Movement disabled"):
                    motor_group.move_position(abs_pos[0], speed)
                    threading.Thread(target = self.wait_end_rotation).start()
                    motor_group.move_end()
        else:
            if motor and motor.is_active():
                motor.move_position(abs_pos[index], speed)
                threading.Thread(target = self.wait_end_rotation).start()
                motor.move_end()

    def halt(self):
        global mode, halt
        if not mode:
            self.stop_motor()
            return
        if motor and motor.is_active():
            motor.move_halt()
        elif motor_group and motor_group.is_active():
            motor_group.move_halt()
            halt = True
        threading.Thread(target = self.wait_end_rotation).start()
        
        
    def fine_step_right(self):
        global motor, motor_group, mode
        mode = True
        step = self.dspinB_fine.value()
        if motor and motor.is_active():
            motor.move_steps(step)
        elif motor_group and motor_group.is_active():
            motor_group.move_steps(step)
        threading.Thread(target = self.wait_end_rotation).start()
        
    def coarse_step_right(self):
        global motor, motor_group, mode
        mode = True
        step = self.dspinB_coarse.value()
        if motor and motor.is_active():
            motor.move_steps(step)
        elif motor_group and motor_group.is_active():
            motor_group.move_steps(step)
        threading.Thread(target = self.wait_end_rotation).start()
        
    def fine_step_left(self):
        global motor, motor_group, mode
        mode = True
        step = self.dspinB_fine.value()
        if motor and motor.is_active():
            motor.move_steps(-step)
        elif motor_group and motor_group.is_active():
            motor_group.move_steps(-step)
        threading.Thread(target = self.wait_end_rotation).start()
        
    def coarse_step_left(self):
        global motor, motor_group, mode
        mode = True
        step = self.dspinB_coarse.value()
        if motor and motor.is_active():
            motor.move_steps(-step)
        elif motor_group and motor_group.is_active():
            motor_group.move_steps(-step)
        threading.Thread(target = self.wait_end_rotation).start()

    ### VELOCITY MODE
    
    def stop_motor(self):
        global motor, mode
        for label in self.active_label_list:    
            label.setStyleSheet('color: yellow')
        if not mode:
            if motor and motor.is_active():
                motor.move_stop()
                threading.Thread(target = self.wait_end_rotation).start()
                print(f"STOP requested for active motor: {motor.name}")     #TODO: added print statement, see if works
        print("Rotation is ending")

    def permanent_right(self):
        global motor, motor_group, mode, direction
        if self.radioB_permanent_when_pushed.isChecked() == True:
            mode       = False
            direction  = True
            if motor and motor.is_active():
                motor.move_velocity(speed)
                threading.Thread(target = self.wait_end_rotation).start()

    def permanent_left(self):
        global motor, mode, direction
        if self.radioB_permanent_when_pushed.isChecked() == True:
            mode       = False
            direction  = False
            if motor and motor.is_active():
                motor.move_velocity(-speed)
                threading.Thread(target = self.wait_end_rotation).start()

    def change_velocity(self):
        global motor, speed, direction
        speed = self.dspinB_speed.value()
        if motor and motor.is_active():
            if motor.is_rotating():
                if mode:
                    motor.change_velocity(speed)
                else:
                    if direction:
                        motor.change_velocity(speed)
                    else:
                        motor.change_velocity(-speed)
        elif motor_group and motor_group.is_active():
            if motor_group.is_rotating():
                motor_group.change_velocity(speed)

    ###   SAVE AND LOAD POSITIONS   ###
    
    def save_pos(self):           
        # save all positions for all to file 
        positions = pd.DataFrame(self.lcd_val)
        positions.to_csv('/home/pi2mpp/Desktop/3105_HEIDELBERG/FE_DPECc/modules/gui/saved_positions', sep='\t', index=False)
        self.terminal.appendPlainText('saved positions of all motors to file!')
    
    def load_pos(self):             
        # load positions from file, then refresh lcd's
        positions = pd.read_csv('/home/pi2mpp/Desktop/3105_HEIDELBERG/FE_DPECc/modules/gui/saved_positions', delimiter = '\t')
        for i in range(8):
            for j in range(6):
                self.lcd_val[i][j] = positions.iloc[i][j]
                try: 
                    self.lcd_matrix[i][j].display(self.lcd_val[i][j]) 
                except AttributeError:
                    pass
        self.terminal.appendPlainText('loaded all positions from file!')
       
    
    # def save_pos(self):
    #     '''Save stored module positions (displayed in lcd_matrix) to external file.'''
    #     with open('saved_positions.txt', 'w') as f:
    #         for row in self.lcd_matrix:
    #             for col in row:
    #                 # print(col.value())
    #                 f.write("%s " % int(col.value()))
    #             f.write("\n")
    #     print('Saved all positions to file!') #TODO: fix store to save msteps, not mm/deg!
        
    # def load_pos(self):
    #     '''Load module positions from external file:'''
    #     with open('saved_positions.txt', 'r') as f:
    #         i = 0
    #         for row in f:
    #             rowlist = row[:-2].split() # drop trailing '\n' and split at '\s'
    #             for j in range(0, len(self.lcd_matrix[0])):
    #                 self.lcd_matrix[i][j].display(rowlist[j]) # update lcd
    #             i += 1 # set counter for next module_idx
    #     # update module positions from the values in lcd_matrix:
    #     for pos_idx in range (0, len(self.lcd_matrix[0])):
    #         self.update_pos(pos_idx)
    #     # Status message:
    #     print('Loaded all saved positions from file!')
        
    # def update_pos(self, pos_idx):
    #     '''Update module positions from lcd_matrix values.'''
    #     #for module in module_list:
    #     #TODO: when connected motors are changed
    #     #TODO: store module_positions as msteps, not in real units
    #     # if module.motor == module_zbr.motor:
    #     #     module.module_positions[pos_idx] = int(self.lcd_matrix[0][pos_idx].value())
    #     # elif module.motor == module_zbc.motor:
    #     #     module.module_positions[pos_idx] = int(self.lcd_matrix[1][pos_idx].value())
    #     # elif module.motor == module_zdr.motor:
    #     #     module.module_positions[pos_idx] = int(self.lcd_matrix[2][pos_idx].value())
    #     # elif module.motor == module_zdc.motor:
    #     #     module.module_positions[pos_idx] = int(self.lcd_matrix[3][pos_idx].value())
    #     # elif module.motor == module_x.motor:
    #     #    module.module_positions[pos_idx] = int(self.lcd_matrix[4][pos_idx].value())
    #     # elif module.motor == module_pr.motor:
    #     #     module.module_positions[pos_idx] = int(self.lcd_matrix[5][pos_idx].value())
    #     # elif module.motor == module_cr.motor:
    #     #     module.module_positions[pos_idx] = int(self.lcd_matrix[6][pos_idx].value())
    #     # elif module.motor == module_s.motor:
    #     #     module.module_positions[pos_idx] = int(self.lcd_matrix[7][pos_idx].value())
    #     # for testing:
    #     # print(self.active_modules, module.module_positions[pos_idx])
            
    def closing(self):
        global all_motors
        ### Turn all motors OFF
        all_motors.set_status('PRE-OPERATIONAL')
        net.disconnect()
        print("Can bus: Disconnected")
        self.close()


def run_app():   
    app = 0
    '''Initialize GUI control flow management. Requires passing argument 
    vector (sys.argv) or empty list [] as arg; the former allows to pass 
    configuration commands on startup to the program from the command 
    line, if such commands were implemented. If app is already open, 
    use that one, otherwise open new app:'''
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    # Create main window (= instance of custom Window Class):
    main_win = Window()
    # Open GUI window on screen:
    main_win.show()
    # Return an instance of a running QApplication = starts event handling
    return app.exec()


