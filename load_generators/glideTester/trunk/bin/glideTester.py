#!/bin/env python
########################################
#
# Description:
#  This program creates a glidein pool for
#  use as a large scale parallel test framework
#
# Author:
#  Igor Sfiligoi @ UCSD
#
########################################

import random
import sys,os,os.path
import time
import condorMonitor
import condorManager
STARTUP_DIR=sys.path[0]
sys.path.append(os.path.join(STARTUP_DIR,"../lib"))

############################
# Configuration class
class ArgsParser:
    def __init__(self,argv):
        # define defaults
        self.config='glideTester.cfg' #just a random default
        self.runId=None

        # parse arguments
        idx=1
        while idx<len(argv):
            el=argv[idx]
            if el=='-config':
                idx+=1
                el=argv[idx]
                if not os.path.exists(el):
                    raise RuntimeError,"Config file '%s' not found!"%el
                self.config=el
            elif el=='-runId':
                idx+=1
                el=argv[idx]
                self.runId=el
            else:
                raise RuntimeError, "Unknown argument '%s' at position %i"%(el, idx)
            idx+=1

        # check and fix the attributes
        if self.runId==None:
            # not defined, create a random one
            self.runId="glideTester_%s_%i_%i"%(os.uname()[1],os.getpid(),random.randint(1000,9999))
        
        # load external values
        self.load_config()

        # set search path
        sys.path.append(os.path.join(self.glideinWMSDir,"lib"))
        sys.path.append(os.path.join(self.glideinWMSDir,"creation/lib"))
        sys.path.append(os.path.join(self.glideinWMSDir,"frontend"))

        self.load_config_dir()
        

    def load_config(self):
        # first load file, so we check it is readable
        fd=open(self.config,'r')
        try:
            lines=fd.readlines()
        finally:
            fd.close()

        # reset the values
        self.glideinWMSDir=None
        self.configDir=None
        self.proxyFile=None
        self.gfactoryNode=None
        self.gfactoryConstraint=None
        self.gfactoryClassadID=None

        # read the values
        for line in lines:
            line=line.strip()
            if line[0:1] in ('#',''):
                continue # ignore comments and empty lines
            arr=line.split('=',1)
            if len(arr)!=2:
                raise RuntimeError,'Invalid config line, missing =: %s'%line
            key=arr[0].strip()
            val=arr[1].strip()
            if key=='glideinWMSDir':
                if not os.path.exists(val):
                    raise RuntimeError, "%s '%s' is not a valid dir"%(key,val)
                self.glideinWMSDir=val
            elif key=='configDir':
                if not os.path.exists(val):
                    raise RuntimeError, "%s '%s' is not a valid dir"%(key,val)
                self.configDir=val
            elif key=='proxyFile':
                if not os.path.exists(val):
                    raise RuntimeError, "%s '%s' is not a valid dir"%(key,val)
                self.proxyFile=val
            elif key=='gfactoryNode':
                self.gFactoryNode=val
            elif key=='gfactoryConstraint':
                self.gFactoryConstraint=val
            elif key=='gfactoryClassadID':
                self.gfactoryClassadID=val
            else:
                raise RuntimeError, "Invalid config key '%s':%s"%(key,line)

        # make sure all the needed values have been read,
        # and assign defaults, if needed
        if self.glideinWMSDir==None:
            raise RuntimeError, "glideinWMSDir was not defined!"
        if self.configDir==None:
            raise RuntimeError, "configDir was not defined!"
        #if self.proxyFile==None:
        #    if os.environ.has_key('X509_USER_PROXY'):
        #        self.proxyFile=os.environ['X509_USER_PROXY']
        #    else:
        #        self.proxyFile='/tmp/x509us_u%i'%os.getuid()
        #    if not os.path.exists(self.proxyFile):
        #        raise RuntimeError, "proxyFile was not defined, and '%s' does not exist!"%self.proxyFile
        if self.gfactoryClassadID==None:
            raise RuntimeError, "gfactoryClassadID was not defined!"
        # it would be wise to verify the signature here, but will not do just now
        # to be implemented
        
    def load_config_dir(self):
        import cgkWDictFile
        self.frontend_dicts=cgkWDictFile.glideKeeperDicts(self.configDir)
        self.frontend_dicts.load()

        self.webURL=self.frontend_dicts.dicts['frontend_descript']['WebURL']
        self.descriptSignature,self.descriptFile=self.frontend_dicts.dicts['summary_signature']['main']


def run(config):
    import glideKeeper
    gktid=glideKeeper.glideKeeperThread(config.webUrl,self.descriptName,config.descriptSignature,
                                        config.runId,
                                        config.gfactoryClassadID,
                                        [config.gfactoryNode],config.gFactoryConstraint,
                                        config.proxyFile)
    gktid.start()
    try:
        # most of the code goes here
	
	# first load the file, so we check it is readable
	fd=open('parameters.config', 'r')
	try:
		lines=fd.readlines()
	finally:
		fd.close()

	# reset the values
	executable=None
	arguments=None
	concurrency=None
	owner=None

	# read the values
	for line in lines:
		line=line.strip()
		if line[0:1] in ('#',''):
			continue # ignore comments and empty lines
		arr=line.split('=',1)
		if len(arr)!=2:
			raise RuntimeError, 'Invalid parameter line, missing =: %s'%line
		key=arr[0].strip()
		val=arr[1].strip()
		if key=='executable':
			if not os.path.exists(val):
				raise RuntimeError, "%s '%s' is not a valid executable"%(key,val)
			executable=val
		elif key=='owner':
			owner=val
		elif key=='arguments':
			arguments=val
		elif key='concurrency':
			concurrency=val
	concurrencyLevel=concurrency.split()

	# make sure all the needed values have been read,
	# and assign defaults, if needed
	universe='vanilla'
	if executable==None:
		raise RuntimeError, "executable was not defined!"
		executable=raw_input("Enter executable: ");
	transfer_executable="True"
	when_to_transfer_output="ON_EXIT"
	requirements='(GLIDEIN_Site =!= "UCSD12") && (Arch=!="abc")'
	if owner==None:
		owner='Undefined'
	notification='Never'

	# Create a testing loop for each concurrency
	for i in range(0, len(concurrencyLevel), 1):

		# request the glideins
		# we want 10% more glideins than the concurrency level
		totalGlideins=int(int(concurrencyLevel[i]) + .1*int(concurrencyLevel[i]))
#		gktid.request_glideins(totalGlideins)
		
		# now we create the directories for each job and a submit file
		loop=0
		for k in range(0, len(concurrencyLevel), 1):
			dir1 = './' + 'test' + concurrencyLevel[k] + '/'
			os.makedirs(dir1)
			logfile='test' + concurrencyLevel[k] + '.log'
			outputfile='test' + concurrencyLevel[k] + '.out.$(Cluster)'
			errorfile='test' + concurrencyLevel[k] + '.err.$(Cluster)'
			filename=dir1 + 'submit' + '.condor'
			FILE=open(filename, "w")
			FILE.write('universe=' + universe + '\n')
			FILE.write('executable=' + executable' '\n')
			FILE.write('transfer_executable=' + transfer_executable + '\n')
			FILE.write('when_to_transfer_output=' + when_to_transfer_output + '\n')
			FILE.write('Requirements=' + requirements + '\n')
			FILE.write('+Owner=' + owner + '\n')
			FILE.write('log=' + logfile + '\n')
			FILE.write('output=' + outputfile + '\n')
			FILE.write('error=' + errorfile + '\n')
			FILE.write('notification=' + notification + '\n' + '\n')
			if arguments!=None:
				FILE.write('Arguments =' + arguments + '\n')
			for j in range(0, int(concurrencyLevel[k]), 1):
				FILE.write('Initialdir = ' + 'job' + str(loop) + '\n')
				FILE.write('Queue' + '\n' + '\n')
				loop=loop+1
			for i in range(0, int(concurrencyLevel[k]), 1):
				dir2='./' + dir1 + '/' + 'job' + str(i) + '/'
				os.makedirs(dir2)

		# now we begin submission and monitoring
		start=time.time()

		# Need to figure this part out
 		submission=condorManager.condorSubmitOne
		check1=condorMonitor.CondorQ

		# Cleanup all the directories and files made
#        pass
    finally:
        gktid.soft_kill()
        gktid.join()
    
    return



###########################################################
# Functions for proper startup
def main(argv):
    config=ArgsParser(argv)
    run(config)

if __name__ == "__main__":
    main(sys.argv)
