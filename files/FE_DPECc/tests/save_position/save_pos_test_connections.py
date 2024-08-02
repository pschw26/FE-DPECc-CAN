# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 13:19:24 2024

@author: pschw
"""

# TODO: - See refresh function
#       - maybe change motor- and lcd-matrix to non instances 
#       - Test GUI with more lcd`s (adjust refresh function accordingly)
#       - Test (with motors): how to add new row for new motor instance in motor-matrix df
#       - make backup positions listen to store, or load?

from PyQt5.QtWidgets import (QMainWindow, QApplication)
from PyQt5.QtCore import QTimer
import sys

import pandas as pd 




from save_pos_test_py import Ui_MainWindow

backup = pd.read_csv("backup_positions", delimiter = '\t')

class Window(QMainWindow, Ui_MainWindow):
    '''Generally: motor_pos_matrix (pd Dataframe) acts as "middleman" for communication between actual motor 
    position stored in the module controller, the external file which has the saved positions as backup
    and the LCD's in the GUI. self.motor_pos_matrix holds instance vars (6 Positions for each
    motor). classvariables later inherit values from the different motors (their config file respectively) 
    in init.'''
    
    def __init__(self, parent=None):  
        super().__init__(parent)
        self.setupUi(self)
        # setup buttons in gui 
        self.store_buttons = [self.button_store0, self.button_store1]
        # lcd matirx: rows: modules, columns: positions 
        self.lcd_matrix = [[self.lcdNumber,   self.lcdNumber_2, self.lcdNumber_3],
                                   [self.lcdNumber_4, self.lcdNumber_5, self.lcdNumber_6],
                                   [self.lcdNumber_7, self.lcdNumber_8, self.lcdNumber_9],
                                   [self.lcdNumber_10, self.lcdNumber_11, self.lcdNumber_12],
                                   [self.lcdNumber_13, self.lcdNumber_14, self.lcdNumber_15],
                                   [self.lcdNumber_16, self.lcdNumber_17, self.lcdNumber_18],
                                   [self.lcdNumber_19, self.lcdNumber_20, self.lcdNumber_21],
                                   [self.lcdNumber_22, self.lcdNumber_23, self.lcdNumber_24, self.lcdNumber_25, self.lcdNumber_26, self.lcdNumber_27],
                                   [self.lcdNumber_28, self.lcdNumber_29, self.lcdNumber_30, self.lcdNumber_31, self.lcdNumber_32, self.lcdNumber_33]]
        # place every element in lcd_matrix in one 1D array(needed for refresh_lcd)
        # self.flat_lcd_matrix = self.lcd_matrix.flatten()
        # motor_pos_matrix and factor list are getting extracted later from config file
        # create motor_pos_matrix as df to facilitate the interaction with the positions/backup df
        self.motor_pos_matrix = pd.DataFrame()
        # LATER: ranges get replaced by lengths of instance lists 
        for i in range(6):
            self.motor_pos_matrix[f'position: {i}'] = [0 for i in range(9)] 
        # LATER: self.factor = objectfromconfigfile, Window.factor_list.append(self.factor)
        # self.factor_list = [1+i for i in range(9)]
        self.factor_list = [1 for i in range(9)]
        self.counter = 0
        # call connection functions
        self.connect()
        
    def connect(self):
        # simulate motor movement in when pushed mode
        self.timer = QTimer()
        self.button_drive.pressed.connect(self.start_timer)
        self.button_drive.released.connect(self.stop_timer)
        self.timer.timeout.connect(self.drive)
        # load position for every module and every position in motor_pos_matrix
        self.button_load.clicked.connect(self.load_position)
        # save position for every module and every position
        self.button_save.clicked.connect(self.save_position)
        # store buttons for positions 
        self.button_store0.clicked.connect(lambda: self.store_position(1))
        self.button_store1.clicked.connect(lambda: self.store_position(2))
        self.button_store2.clicked.connect(lambda: self.store_position(3))
        self.button_store3.clicked.connect(lambda: self.store_position(4))
        self.button_store4.clicked.connect(lambda: self.store_position(5))
        # close application 
        self.button_quit.clicked.connect(self.close)
        
    def start_timer(self):
        # this later corresponds to heartbeat frequence for the position backup 
        self.timer.start(10)
    
    def stop_timer(self):
        self.timer.stop()
    
    def drive(self):
        self.counter = (self.counter+1)%10  
        # dummy drive function to simulate motor movement 
        self.motor_pos_matrix['position: 0'] = self.motor_pos_matrix['position: 0']+1 
        # position backup, currently connected to drive function. 
        # Later: separate function, called frequently as long as motor hasnt reached position?
        self.refresh_lcd([(i, 0) for i in range(9)])
        if self.counter == 0:
            backup = self.motor_pos_matrix
            backup.to_csv('backup_positions', sep='\t', index=False)

    def refresh_lcd(self, idx_list):
        '''show current motor positions: drive, load_position, store_position call this function.
        designed to only iterate over necessary lcd's to maximise efficiency.drive-function will 
        be working with something like "until position reached" thus, refresh_lcd gets called 
        repeatedly until condition fullfilled.'''
        # iterate over lcd_list given as argument in calling functions 
        # for lcd in lcd_list:
        #     # get index of lcd in flattened list of lcd_matrix
        #     idx = np.where(self.flat_lcd_matrix == lcd)[0]
        #     idx = idx[0]
        #     # print(idx ,idx%6, idx//6)
        #     # every extracted index can be matched with indexpair corresponding to the motor/position 
        #     # the lcd should display. This index pair (idx%3, idx//3) allows extraction of the right value 
        #     # from the motor_pos_matrix. For scaling, the right factor from factor_list for the motor gets used.
        #     # TODO: -(adjust index-pair expression, corresponding to lcd_matrix dimensions)
        #     #       -call if store_pos is activated?
        #     try:
        #         lcd.display(self.factor_list[idx//6]*self.motor_pos_matrix[f'position: {idx%6}'][idx//6])
        #     except AttributeError:
        #         pass
        for tupel in idx_list:
            try:
                self.lcd_matrix[tupel[0]][tupel[1]].display(self.motor_pos_matrix[f'position: {tupel[1]}'][tupel[0]])
            except IndexError:
                pass
                
        
    def load_position(self):
        # load positions from file and override motor_pos_matrix with values, then refresh lcd's
        positions = pd.read_csv("test_positions", delimiter = '\t')
        self.motor_pos_matrix = positions 
        # print('loaded all positions from file!')
        self.terminal.appendPlainText('loaded all positions from file!')
        self.refresh_lcd([(i, j) for i in range(9) for j in range(6)])
        
    def save_position(self): 
        # save all positions for all to file 
        positions = self.motor_pos_matrix
        positions.to_csv('test_positions', sep='\t', index=False)
        # print('saved positions of all motors to file!')
        self.terminal.appendPlainText('saved positions of all motors to file!')
    
                
    def store_position(self, pos_idx):
        # store position temporary in column over the corresponding store button
        self.motor_pos_matrix[f'position: {pos_idx}'] = self.motor_pos_matrix['position: 0']
        # print(f'current pos. of all motors stored on position: {pos_idx}')
        self.terminal.appendPlainText(f'current pos. of all motors stored on position: {pos_idx}')
        self.refresh_lcd([(i, pos_idx) for i in range(9)])
    

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
            