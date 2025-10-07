#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P gauge communication configuration:
    - Node ID  [1-127]
    - Bitrate  [kbaud]
    
Created on Mon Jul 28 15:18:45 2025

@author: Eric Reusser
"""

import sys, time
import canopen

# List of valid bitrates
KBAUD  = {10:8, 20:7, 50:6, 100:5, 125:4, 250:3, 500:2}
KBAUDI = {2:500, 3:250, 4:125, 5:100, 6:50, 7:20, 8:10}


def numerical_input(prompt):
    while(True):
        s = input(prompt)
        try:
            n = int(s)
        except ValueError:
            print("Not a number!")
            continue
        break
    if n == 0:
        sys.exit()
    return n
    
# Make sure that P-gauge is unique in the network

print("\nP gauge communication configuration")
s = input("Is the DS-CAN-01 P-gauge the only device " +
          "attached to the CAN bus? [y/n] > ")
if not (s == 'y') and not (s == 'Y'):
    print("For communication configuration, it MUST be the only device\n" +
          "attached to the CAN bus!!!")
    sys.exit()

# Enter actual values for NODE_ID and BITRATE

while(True):
    nid_act = numerical_input("Enter actual NODE_ID. 0 to exit > ")
    if (nid_act < 1) or (nid_act > 127):
        print("Invalid NODE ID: must be 1 ... 127!")
        continue
    break
    
while(True):
    br = numerical_input("Enter actual BITRATE [kbaud]. 0 to exit > ")
    if not (br in KBAUD):
        print("Invalid bitrate!")
        continue
    break
kb_act = KBAUD[br]

# Enter new values

nid = nid_act
while(True):
    nid = numerical_input("Enter NEW NODE ID > ")
    if (nid < 1) or (nid > 127):
        print("Invalid NODE ID: must be 1 ... 127!")
        continue
    break

kb = kb_act
while(True):
    br = numerical_input("Enter NEW BITRATE > ")
    if not (br in KBAUD):
        print("Invalid bitrate!")
        continue
    break
kb = KBAUD[br]
print("")

if (nid == nid_act) and (kb == kb_act):
    print("No changes required. Bye")
    sys.exit()

# Connect to P-gauge

net = canopen.Network()
net.connect(channel = 'can0',
            bustype = 'socketcan',
            bitrate = 1000*kb_act)
pg = net.add_node(nid_act,'modules/DSCAN42.eds')


# Switch to CONFIGURATION state

net.lss.send_switch_state_global(net.lss.CONFIGURATION_STATE)
time.sleep(0.1)

# Change NODE_ID

if nid == nid_act:
    print("No need to change NODE_ID")
else:
    net.lss.configure_node_id(nid)
    time.sleep(0.1)
    print("NODE_ID updated. New NODE_ID = " + str(nid))
    
# Change BITRATE

if kb == kb_act:
    print("No need to change BITRATE")
else:
    net.lss.configure_bit_timing(kb)
    time.sleep(0.1)
kb = KBAUDI[kb]
print("BITRATE updated. New BITRATE = " + str(kb) + " kbaud")
    
# Save changes & switch to OPERATION state

net.lss.store_configuration()
time.sleep(0.2)
net.lss.send_switch_state_global(net.lss.WAITING_STATE)
    
net.disconnect()
print("CAN bus disconnected")
