# -*- coding: utf-8 -*-
# miniTLU test script

#from PyChipsUser import *
#from FmcTluI2c import *
import uhal
import sys
import time
from datetime import datetime
import threading
# from ROOT import TFile, TTree
# from ROOT import gROOT
from datetime import datetime

from TLU_v1e import TLU
# Use to have interactive shell
import cmd

# Use to have config file parser
import ConfigParser

# Use root
from ROOT import TFile, TTree, gROOT, AddressOf
from ROOT import *
import numpy as numpy


## Define class that creates the command user inteface
class MyPrompt(cmd.Cmd):

    # def do_initialise(self, args):
    #     """Processes the INI file and writes its values to the TLU. To use a specific file type:\n
    #     parseIni path/to/filename.ini\n
    #     (without quotation marks)"""
    # 	print "COMMAND RECEIVED: PARSE INI"
    # 	parsed_cfg= self.open_cfg_file(args, "/users/phpgb/workspace/myFirmware/AIDA/TLU_v1e/scripts/localIni.ini")
    #     try:
    #         theID = parsed_cfg.getint("Producer.fmctlu", "initid")
    #         print theID
    #         theSTRING= parsed_cfg.get("Producer.fmctlu", "ConnectionFile")
    #         print theSTRING
    #         #TLU= TLU("tlu", theSTRING, parsed_cfg)
    #     except IOError:
    #         print "\t Could not retrieve INI data."
    #         return


    def do_configure(self, args):
        """Processes the CONF file and writes its values to the TLU. To use a specific file type:\n
        parseIni path/to/filename.conf\n
        (without quotation marks)"""
        print "==== COMMAND RECEIVED: PARSE CONFIG"
    	#self.testme()
        parsed_cfg= self.open_cfg_file(args, "./localConf.conf")
        try:
            theID = parsed_cfg.getint("Producer.fmctlu", "confid")
            print "\t", theID
            TLU.configure(parsed_cfg)
        except IOError:
            print "\t Could not retrieve CONF data."
            return

    def do_i2c(self, args):
	arglist = args.split()
        if len(arglist) == 0:
            print "\tno command specified"
        else:
            i2ccmd= arglist[0]
            results = list(map(int, arglist))
	    TLU.DISP.writeSomething(results)
	    print "Sending i2c command to display"
	return

    def do_id(self, args):
        """Interrogates the TLU and prints it unique ID on screen"""
        TLU.getSN()
        return

    def do_triggers(self, args):
        """Interrogates the TLU and prints the number of triggers seen by the input discriminators"""
        TLU.getChStatus()
        TLU.getAllChannelsCounts()
        TLU.getPostVetoTrg()
        return

    def do_startRun(self, args):
        """Starts the TLU run. If a number is specified, this number will be appended to the file name as Run_#"""
    	print "==== COMMAND RECEIVED: STARTING TLU RUN"
    	#startTLU( uhalDevice = self.hw, pychipsBoard = self.board,  writeTimestamps = ( options.writeTimestamps == "True" ) )
        arglist = args.split()
        if len(arglist) == 0:
            print "\tno run# specified, using 1"
            runN= 1
        else:
            runN= arglist[0]

        logdata= True

        #TLU.start(logdata)
        if (TLU.isRunning): #Prevent double start
            print "  Run already in progress"
            return
        else:
            now = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = "./datafiles/"+ now + "_tluData_" + str(runN) + ".root"
            rootFname= default_filename
            print "OPENING ROOT FILE:", rootFname
            self.root_file = TFile( rootFname, 'RECREATE' )
            # Create a root "tree"
            root_tree = TTree( 'T', 'TLU Data' )
            #highWord =0
            #lowWord =0
            #evtNumber=0
            #timeStamp=0
            #evtType=0
            #trigsFired=0
            #bufPos = 0

            #https://root-forum.cern.ch/t/long-integer/1961/2
            gROOT.ProcessLine(
            "struct MyStruct {\
               UInt_t     raw0;\
               UInt_t     raw1;\
               UInt_t     raw2;\
               UInt_t     raw3;\
               UInt_t     raw4;\
               UInt_t     raw5;\
               UInt_t     evtNumber;\
               ULong64_t     tluTimeStamp;\
               UChar_t     tluEvtType;\
               UChar_t     tluTrigFired;\
            };" );

            mystruct= MyStruct()


            # Create a branch for each piece of data
            root_tree.Branch('EVENTS', mystruct, 'raw0/i:raw1/i:raw2/i:raw3/i:raw4/i:raw5/i:evtNumber/i:tluTimeStamp/l:tluEvtType/b:tluTrigFired/b' )
            # root_tree.Branch( 'tluHighWord'  , highWord  , "HighWord/l")
            # root_tree.Branch( 'tluLowWord'   , lowWord   , "LowWord/l")
            # root_tree.Branch( 'tluExtWord'   , extWord   , "ExtWord/l")
            # root_tree.Branch( 'tluTimeStamp' , timeStamp , "TimeStamp/l")
            # root_tree.Branch( 'tluBufPos'    , bufPos    , "Bufpos/s")
            # root_tree.Branch( 'tluEvtNumber' , evtNumber , "EvtNumber/i")
            # root_tree.Branch( 'tluEvtType'   , evtType   , "EvtType/b")
            # root_tree.Branch( 'tluTrigFired' , trigsFired, "TrigsFired/b")
            #self.root_file.Write()

            daq_thread= threading.Thread(target = TLU.start, args=(logdata, runN, mystruct, root_tree))
            daq_thread.start()

    def do_endRun(self, args):
    	"""Stops the TLU run"""
    	print "==== COMMAND RECEIVED: STOP TLU RUN"
        if TLU.isRunning:
            TLU.isRunning= False
            TLU.stop(False, False)
            self.root_file.Write()
            self.root_file.Close()
        else:
            print "  No run to stop"


    def do_quit(self, args):
        """Quits the program."""
        print "==== COMMAND RECEIVED: QUITTING TLU CONSOLE"
        if TLU.isRunning:
            TLU.isRunning= False
            TLU.stop(False, False)
            self.root_file.Write()
            self.root_file.Close()
            print "Terminating run"
	return True

    def testme(self):
        print "This is a test"

    def open_cfg_file(self, args, default_file):
        # Parse the user arguments, attempts to opent the file and performs a (minimal)
        # check to verify the file exists (but not that its content is correct)

        arglist = args.split()
        if len(arglist) == 0:
            print "\tno file specified, using default"
            fileName= default_file
            print "\t", fileName
        else:
            fileName= arglist[0]
        if len(arglist) > 1:
            print "\tinvalid: too many arguments. Max 1."
            return

        parsed_file = ConfigParser.RawConfigParser()
        try:
            with open(fileName) as f:
                parsed_file.readfp(f)
                print "\t", parsed_file.sections()
        except IOError:
            print "\t Error while parsing the specified file."
            return
        return parsed_file

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
    print "TLU v1E MAIN"
    prompt = MyPrompt()
    prompt.prompt = '>> '

    parsed_ini= prompt.open_cfg_file("", "./localIni.ini")
    TLU= TLU("tlu", "file://./TLUconnection.xml", parsed_ini)

    ###TLU.configure(parsed_cfg)
    ###logdata= True
    ###TLU.start(logdata)
    ###time.sleep(5)
    ###TLU.stop(False, False)

    # Start interactive prompt
    print "===================================================================="
    print "==========================TLU TEST CONSOLE=========================="
    print "===================================================================="
    prompt.cmdloop("Type 'help' for a list of commands.")
