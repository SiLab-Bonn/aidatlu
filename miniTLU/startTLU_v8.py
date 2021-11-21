# miniTLU test script

#from PyChipsUser import *
from FmcTluI2c import *
import uhal
import sys
import time
# from ROOT import TFile, TTree
# from ROOT import gROOT
from datetime import datetime

from miniTLU import MiniTLU
# Use to have interactive shell
import cmd

class MyPrompt(cmd.Cmd):


    def do_startRun(self, args):
	"""Starts the TLU run"""
	print "COMMAND RECEIVED: STARTING TLU RUN"
	startTLU( uhalDevice = self.hw, pychipsBoard = self.board,  writeTimestamps = ( options.writeTimestamps == "True" ) )
	#print self.hw

    def do_stopRun(self, args):
	"""Stops the TLU run"""
	print "COMMAND RECEIVED: STOP TLU RUN"
	#stopTLU( uhalDevice = hw, pychipsBoard = board )

    def do_quit(self, args):
        """Quits the program."""
        print "COMMAND RECEIVED: QUITTING SCRIPT."
        #raise SystemExit
	return True

# # Override methods in Cmd object ##
#     def preloop(self):
#         """Initialization before prompting user for commands.
#            Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
#         """
#         cmd.Cmd.preloop(self)  # # sets up command completion
#         self._hist = []  # # No history yet
#         self._locals = {}  # # Initialize execution namespace for user
#         self._globals = {}
#         print "\nINITIALIZING"
#         now = datetime.now().strftime('%Y-%m-%dT%H_%M_%S')
#         default_filename = './rootfiles/tluData_' + now + '.root'
#         print "SETTING UP AIDA TLU TO SUPPLY CLOCK AND TRIGGER TO TORCH READOUT\n"
#         self.manager = uhal.ConnectionManager("file://./connection.xml")
#         self.hw = self.manager.getDevice("minitlu")
#         self.device_id = self.hw.id()
#
#         # Point to TLU in Pychips
#         self.bAddrTab = AddressTable("./aida_mini_tlu_addr_map.txt")
#
#         # Assume DIP-switch controlled address. Switches at 2
#         self.board = ChipsBusUdp(self.bAddrTab,"192.168.200.32",50001)


#################################################
if __name__ == "__main__":
    miniTLU= MiniTLU("minitlu", "file://./connection.xml")
    miniTLU.initialize()

    logdata= False
    miniTLU.start(logdata)
    miniTLU.stop()
    # prompt = MyPrompt()
    # prompt.prompt = '>> '
    # prompt.cmdloop("Welcome to miniTLU test console.\nType HELP for a list of commands.")
