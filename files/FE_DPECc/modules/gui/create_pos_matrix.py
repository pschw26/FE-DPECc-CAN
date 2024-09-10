
import pandas as pd 

df = pd.DataFrame([[0. for k in range(6)] for i in range(8)])

df.to_csv('/home/pi2mpp/Desktop/3105_HEIDELBERG/FE_DPECc/modules/gui/blank_positions', sep = '\t', index = False)

