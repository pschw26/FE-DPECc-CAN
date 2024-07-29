# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 13:37:20 2024

@author: pschw
"""

from save_pos_test_connections import run_app 


#####   Main GUI program starts here   #####
if __name__ == "__main__":
    # Start main program with event handling loop:
    try:
        app = run_app()
    except Exception:
        #pass
        print('ERROR')
