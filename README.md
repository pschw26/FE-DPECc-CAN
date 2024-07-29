# FE-DPECc-CAN

Fast Exchange Diamond Paris-Edinbourgh Cell control (based on CANopen protocol)

Written by Peter Schwörer (Universität Heidelberg) and Eric Reusser (ETH-Zürich), 2024

This repositiory is the adaptation from the former version, working with USB-connection, to CAN using the CANopen protocoll.
Therefore see also: https://github.com/silandkyan/FE-DPECc for USB-based connection network.

This Python program offers a graphical user interface (GUI) for manipulating the 8 motor axes of a Paris-Edinbourgh Cell platform. The motors are stepper motors of the company Trinamic, which are set up and controlled by the Trinamic's open-source PyTrinamic Python library. The communication between the PC and the motor control modules is achieved via CANopen protocoll.
