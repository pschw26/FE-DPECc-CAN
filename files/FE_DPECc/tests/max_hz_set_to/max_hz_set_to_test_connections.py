# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 18:32:36 2024

@author: pschw
"""

'''ToDo:
    - adjust motor class for set_val:
        - write something for multi motor
    - add min max values for set value in config file for each motor 
    - set min max for spinB accordingly 
    - check bug: radiobutton for keyboard control has to be pressed last:
                 maybe not clicked outside of the box?
    - make connections ready esp. for set to value

    Done:
    - Cap frequency of keyboard commands 
    - define map for unit conversion for pos: f(value_spinBox,
                                   internal to physical unit conversion
                                   from config file)'''




from PyQt5.QtWidgets import (QMainWindow, QApplication)
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt
import sys
import time 

from config import Config

# import pandas as pd 

from max_hz_set_to_test import Ui_MainWindow

class Window(QMainWindow, Ui_MainWindow):
    
    
    def __init__(self, parent=None):  
        super().__init__(parent)
        self.setupUi(self)
        self.setup()
        self.connect()
    
    def setup(self):
        self.conf = Config('fedpecc.config')
        # print(conf.motor_params[5]['pitch']) #mm/rotation val for motor 5
        self.t_0 = time.time()
        self.overflow = False
        # conversion from physical to internal units (steps)
        self.conversion_factors = [2**self.conf.motor_params[i]['Microstep Resolution 1']*self.conf.motor_params[i]['full_step']/self.conf.motor_params[i]['pitch']
                      for i in range(8)]
          
    def counter(self):
        # prevents overflow due to keyboard spam 
        if time.time() - self.t_0 < 0.3:
            self.overflow = True
            self.terminal.appendPlainText('overflow!')
        else:
            self.overflow = False
        self.t_0 = time.time()
        
    def connect(self):
        # set internal motor position to step value calculated from physical value 
        self.button_set.clicked.connect(lambda: self.set_value())
        # close application
        self.button_quit.clicked.connect(self.close)
        
    def set_value(self):
        # calculate the step value for this according to the axis params from config file 
        steps = self.conversion_factors[1]*self.spinB_set.value()
        # set_value(steps)
        self.terminal.appendPlainText(f'internal motor position got changed to {self.spinB_set.value()}({steps})')
        
    def keyPressEvent(self, event: QKeyEvent) -> None: 
        # event gets defined and keys are specified below 
        self.counter()
        key_pressed = event.key()
        if not self.overflow:
            if key_pressed == Qt.Key_S:
                self.terminal.appendPlainText(f'fine right: {self.spinB_small.value()} ')
            if key_pressed == Qt.Key_A:
                self.terminal.appendPlainText(f'large left: {self.spinB_large.value()} ')
            if key_pressed == Qt.Key_W:
                self.terminal.appendPlainText(f'fine left: {self.spinB_small.value()} ')
            if key_pressed == Qt.Key_D:
                self.terminal.appendPlainText(f'large right: {self.spinB_large.value()} ')


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
    #TODO implement predefine function here 
    # Return an instance of a running QApplication = starts event handling
    return app.exec()
            