# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 18:57:00 2024

@author: Eric Reusser
"""

class Config:
    """
    Config:
        Reads the configuration file 'filename'.
        Creates dictionaries of bus-specific and motor-specific parameters.
    
    Use:
        from config import Config
        ...
        c = Config(filename)   [Configuration file]
        ...
        c.headers              [list]
        c.global_params        [dictionary]
        c.bus_params           [dictionary]
        c.sdo                  [list]
        c.motor_params         [list of dictionaries]
    """
    
    def __init__(self, filename):

        self.headers = []
        self.global_params = {}
        self.bus_params = {}
        self.sdo = []
        self.motor_params = []

            
        def extract(line):
            l = line.split('#')
            return l[0].strip()
        
        def header(f):
            for line in f:
                s = extract(line)
                if s == '' or s.startswith(';'): continue
                if s.startswith('['): break
            s = s.strip('[]')
            return s.strip()

        def conf_list(f):
            params = []
            for line in f:
                s = extract(line)
                if s == "": break
                params.append(s)
            return params
        
        def conf_dict(f):
            params = {}
            for line in f:
                s = extract(line)
                if s == "": break
                s = s.split('=')
                key = s[0].strip()
                val = s[1].strip()
                if val.isdigit():
                    val = int(val)
                elif val.isascii():
                    try:
                        val = float(val)
                    except ValueError: pass
                params[key] = val
            return params

        f = open(filename,"r")
        self.headers.append(header(f))
        self.global_params = conf_dict(f)
        self.headers.append(header(f))
        self.bus_params = conf_dict(f)
        self.headers.append(header(f))
        self.sdo = conf_list(f)
        n = self.global_params['number_of_motors']
        for i in range(n):
            self.headers.append(header(f))
            self.motor_params.append(conf_dict(f))
        f.close()
        print("Configuration processed")
