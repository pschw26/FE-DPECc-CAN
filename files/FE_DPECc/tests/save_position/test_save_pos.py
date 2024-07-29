# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 12:33:41 2024

@author: pschw
"""

import pandas as pd 



# positions = pd.read_csv("test_positions", delimiter = '\t')

positions = pd.DataFrame()

module_positions = [[0 for i in range(6)] for i in range(9)]
# print(module_positions)
#three postions 0, 1, 2 for module A, B, C

def safe_position(index_list): # safe position(s) specified with index_list for all modules
    for position_idx in index_list:
        positions[f"position: {position_idx}"] = [module[position_idx] for module in module_positions]
    positions.to_csv('test_positions', sep='\t', index=False)
    
def load_positions(): # load position for every module from external file
    for i in positions.index:
        for j, value in enumerate(positions.columns):
            module_positions[i][j] = positions[f"position: {j}"][i]
    return module_positions

def update_lcd():
    pass
      
safe_position([0, 1, 2, 3, 4, 5])

# load_positions()

# print(module_positions)



