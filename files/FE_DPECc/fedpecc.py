#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 16:38:18 2023

@author: pgross

When running this program with Spyder, make sure that all variables are 
cleared before execution in the settings.
"""

#####   Importing Packages   #####

from modules.gui.gui_connections import run_app

#####   Main GUI program starts here   #####
if __name__ == "__main__":
    try:
        app = run_app()
    except Exception:
        print('ERROR')
