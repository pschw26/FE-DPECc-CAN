# FE-DPECc-CAN

Fast Exchange Diamond Paris-Edinbourgh Cell control (based on CANopen protocol)

Written by Peter Schwörer (Universität Heidelberg), Eric Reusser (ETH-Zürich) and Philip Groß, 2023/2024

This repositiory is the adaptation from the former version, working with USB-connection, to CAN using the CANopen protocoll.
The CAN functionality is designed for use with Linux-based system software.
Therefore see also: https://github.com/silandkyan/FE-DPECc for USB-based connection network.

This Python program offers a graphical user interface (GUI) for manipulating the 8 motor axes of a Paris-Edinbourgh Cell platform. 
The motors are stepper motors of the company Trinamic, which are set up and controlled by the Trinamic's open-source PyTrinamic Python library. 
The communication between the PC and the motor control modules is achieved via CANopen protocoll.


# Folder/File Structure 

Relevant files after fullfilling (hardware) prerequisites (coming soon).
```
├── /FE-DPECc-CAN/files                  
│   ├── /CAN_traffic                                    (CAN initiation and traffic on bus in command promt)
│   │   ├── candown                                     (disable CAN bus)
│   │   ├── candump                                     (show CAN bus traffic)
│   │   ├── canup                                       (enable CAN bus)
│   ├── /FE-DPECc                                       (holds the code files for functionality)                   
│   │   ├── /modules                                    (modules and raw files)
│   │   │   ├── /gui                                    (user interface class for operation based on pyqt)
│   │   │   │   ├── gui_connections.py                  (connect widgets with functions)
│   │   │   │   ├── main_window.ui                      (raw window .ui file w.o. functionality)
│   │   │   │   ├── main_window_ui.py                   (converted raw window file to .py)
│   │   │   ├── canbus.py                               (CAN bus driver classes)
│   │   │   ├── config.py                               (creates bus parameter dictionary from input file: fedpecc.config)
│   │   │   ├── motor.py                                (Wrapper for driver classes)
│   │   │   ├── TMCM-1260.eds                           (CANopen configuration for steppermotor)
│   │   ├── /test                                       (test gui along with connection files and miscellaneous  files)
│   │   │   ├── /max_hz_set_to                          (test for frequence cap for keyboard commands and set to val button)
│   │   │   │   ├── max_hz_set_to_test.py               (user interface class for operation based on pyqt)
│   │   │   │   ├── max_hz_set_to_test.ui               (raw window .ui file w.o. functionality)
│   │   │   │   ├── max_hz_set_to_test_connections.py   (connect widgets with functions)
│   │   │   │   ├── set_to_motorcls_test.py             (manipulated motor class for set_value function)
│   │   │   │   ├── start_app_max_hz_set_to.py          (acutal code to run the gui for this test)
│   │   │   ├── /save_position                          (test for save/load/store positions of motors)
│   │   │   │   ├── save_pos_test_py.py                 (user interface class for operation based on pyqt)
│   │   │   │   ├── save_pos_test.ui                    (raw window .ui file w.o. functionality)
│   │   │   │   ├── save_pos_test_connections.py        (connect widgets with functions)
│   │   │   │   ├── start_app_save_test.py              (acutal code to run the gui for this test)
│   │   │   │   ├── test_positions                      (Matrix holding position values: index i is position, j is motor)
│   │   │   │   ├── backup_positions                    (Matrix holding position values: index i is position, j is motor)
│   │   ├── fedpecc.config                              (bus parameter for network)
│   │   ├── fedpecc.py                                  (acutal code to run the gui and operate with motors (after canup initialisation))
│   │   ├── TODO.txt                                    (recent errors and resolved ones)
│   ├── Erklärungen_Mai24.txt                           (Descriptions for changes in files in may)
```
