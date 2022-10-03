# -*- coding: utf-8 -*-
import multiprocessing
import subprocess
import sys
import os
import time
import logging
import threading

#Processer class for running multiple processes simultaneously.
class processer():
    def __init__(self, number_of_processes = None):
        self.processes = None
        self.logger = logging.getLogger('Error')
        #Sets the number of processes base on user input.
#        print(number_of_processes, range(number_of_processes), [None for n in range(number_of_processes)])
        if number_of_processes is not None:
            self.processes = [None for n in range(number_of_processes)]
        #Defaults to eight processes.
        else:
            self.processes = [None, None, None, None, None, None, None, None]
    #Returns any empty or finished processes.
    def find_availble_process(self, action):
        while True:
            for p in range(len(self.processes)):
                if self.processes[p] is None:
                    return p
                if type(action) is subprocess.Popen and self.processes[p].poll() is not None:
                    self.processes[p] = None
                    return p
                elif type(action) is multiprocessing.Process and self.processes[p].is_alive() is not None:
                    self.processes[p] = None
                    return p
#                elif type(action) is threading.Thread and self.processes[p].is_alive() is not None:
                elif action is threading.Thread and not self.processes[p].is_alive():
#                    print(self.processes[p].is_alive(), self.processes)
                    self.processes[p] = None
                    return p
#                print(type(action))
#                if action is threading.Thread:
#                    print(p, self.processes[p].is_alive() is not None)
    '''def wait(self):
        while True:
            for p in range(len(self.processes)):
#                print(p, self.processes[p])
#                if self.processes[p] is not None:
#                    print(self.processes[p] is threading.Thread, type(self.processes[p]), self.processes[p])
                if self.processes[p] is None:
                    return p
                elif type(self.processes[p]) is threading.Thread and self.processes[p].is_alive():
#                    print(p, not self.processes[p].is_alive(), self.processes[p])
                    return p
                if type(self.processes[p]) is subprocess.Popen and self.processes[p].poll() is not None:
                    return p
                elif type(self.processes[p]) is multiprocessing.Process and self.processes[p].is_alive() is not None:
                    return p'''
    def wait(self):
        alive = True
        while alive:
            alive = False
            for p in range(len(self.processes)):
                if type(self.processes[p]) is threading.Thread and self.processes[p].is_alive():
                    alive = True
                if type(self.processes[p]) is subprocess.Popen and self.processes[p].poll() is not None:
                    alive = True
                elif type(self.processes[p]) is multiprocessing.Process and self.processes[p].is_alive() is not None:
                    alive = True
    #Processes any remaining processes in the processer.
    def complete(self):
        while True:
           terminate = True
           for p in range(len(self.processes)):
               terminate = terminate and self.processes[p] is None
               if self.processes[p] is not None and self.processes[p].poll() is not None:
                   self.processes[p] = None
           if terminate:
               break
    #Adds a process to the processer and runs it.
    def process(self, action, action_attributes = None):
#        print(self.processes)
        p = self.find_availble_process(action)
#        print(action)
        if action_attributes is not None:
            if type(action_attributes) is dict:
                self.processes[p] = action(**action_attributes)
                self.processes[p].start()
            elif type(action_attributes) is list or type(action_attributes) is tuple:
                self.processes[p] = action(*action_attributes)
        else:
            self.processes[p] = action()
    def kill(self):
        for p in range(len(self.processes)):
            if self.processes[p] is not None and self.processes[p].poll() is None:
                try:
                    if self.processes[p].poll() is None:
                        self.processes[p].kill()
                except AttributeError:
                    try:
                        if self.processes[p].is_alive() is None:
                            self.processes[p].kill()
                    except AttributeError:
                        print('Encountered unknown process.  Terminating process')
                        sys.exit()
                self.processes[p] = None