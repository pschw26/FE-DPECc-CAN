#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  1 11:06:39 2025

@author: pi
"""

import time
from modules.config import Config
from modules.canbus import CanBus, PGauge

### Configuration, Initialization of all motors

conf = Config('fedpecc.config')
bus  = CanBus(conf.bus_params)
net  = bus.connect()

pg = PGauge(net,conf)

pg.start()
for i in range(20):
    if pg.is_running():
        print("P value =", pg.get_pvalue(), "bar")
    time.sleep(1)  
pg.stop()
print("Is running", pg.is_running())
pg.end_pgauge()
net.disconnect()
print("CAN bus disconnected")

    