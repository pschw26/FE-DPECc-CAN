# FE-DPECc-CAN

Fast Exchange Diamond Paris-Edinbourgh Cell control (based on CANopen protocol)

Written by Peter Schwörer (Universität Heidelberg) and Eric Reusser (ETH-Zürich), 2024

This repositiory is the adaptation from the former version, working with USB-connection, to CAN using the CANopen protocoll.
The CAN functionality is designed for use with Linux-based system software.
Therefore see also: https://github.com/silandkyan/FE-DPECc for USB-based connection network.

This Python program offers a graphical user interface (GUI) for manipulating the 8 motor axes of a Paris-Edinbourgh Cell platform. 
The motors are stepper motors of the company Trinamic, which are set up and controlled by the Trinamic's open-source PyTrinamic Python library. 
The communication between the PC and the motor control modules is achieved via CANopen protocoll.


# Folder/File Structure 

Relevant files after fullfilling (hardware) prerequisites (coming soon).

├── /FE-DPECc-CAN/files                  
│   ├── /CAN_traffic                     (CAN initiation and traffic on bus in command promt)
│   │   ├── candown                      (disable CAN bus)
│   │   ├── candump                      (show CAN bus traffic)
│   │   ├── canup                        (enable CAN bus)
│   ├── /FE-DPECc                        (holds the code files for functionality)                   
│   │   ├── /modules                     (modules and raw files)
│   │   │   ├── /gui                     (user interface for operation based on pyqt)
│   │   │   │   ├── gui_connections.py   (connect widgets with functions)
│   │   │   │   ├── main_window.ui       (raw window .ui file w.o. functionality)
│   │   │   │   ├── main_window_ui.py    (converted raw window file to .py)
│   │   │   ├── canbus.py                (CAN bus driver classes)
│   │   │   ├── config.py                (creates bus parameter dictionary from input file: fedpecc.config)
│   │   │   ├── motor.py                 (Wrapper for driver classes)
│   │   │   ├── TMCM-1260.eds            (CANopen configuration for steppermotor)
│   │   ├── fedpecc.config               (bus parameter for network)
│   │   ├── fedpecc.py                   (acutal code to run the gui and operate with motors (after canup initialisation))
│   ├── Erklärungen_Mai24.txt            (Descriptions for changes in files in may)
