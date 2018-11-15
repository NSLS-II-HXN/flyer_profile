#!../../bin/linux-x86_64/tpmac

< envPaths

epicsEnvSet("ENGINEER",  "__ENGINEER__ @__EXT__")
epicsEnvSet("LOCATION",  "__CELL____TYPE____HUTCH__-hutch __RACK__")
epicsEnvSet("STREAM_PROTOCOL_PATH", ".:../protocols:$(PMACUTIL)/protocol:/$(PMACCOORD)/protocol")

epicsEnvSet("SYS",           "__SYS__")
epicsEnvSet("IOC_ASYN",      "$(SYS){__IOCASYN__}")
epicsEnvSet("IOC_PREFIX",    "$(SYS){IOC:__MCNAME__}")
epicsEnvSet("CONTROLLER_IP", "__CONTROLLER__")

epicsEnvSet("EPICS_CA_AUTO_ADDR_LIST", "NO")
epicsEnvSet("EPICS_CA_ADDR_LIST", "__CA_ADDR_LIST__")

cd ${TOP}

## Register all support components
dbLoadDatabase("dbd/tpmac.dbd",0,0)
tpmac_registerRecordDeviceDriver(pdbbase) 

# pmacAsynIPConfigure() is a wrapper for drvAsynIPPort::drvAsynIPPortConfigure() and
# pmacAsynIPPort::pmacAsynIPPortConfigureEos().
# See pmacAsynIPPort.c
pmacAsynIPConfigure("P0", "__CONTROLLER_IP__:1025")

# WARNING: a trace-mask of containing 0x10 will TRACE_FLOW (v. noisy!!)
#asynSetTraceMask("P0",-1,0x9)
#asynSetTraceIOMask("P0",-1,0x2)

# pmacAsynMotorCreate(port,addr,card,nAxes)
# see pmacAsynMotor.c
pmacAsynMotorCreate("P0", 0, 1, 8)

# Setup the motor Asyn layer (port, drvet name, card, nAxes+1)
drvAsynMotorConfigure("M0", "pmacAsynMotor", 1, 9)

# Initialize the coord-system(port,addr,cs,ref,prog#)
# pmacAsynCoordCreate("P0",0,1,1,10)
# pmacAsynCoordCreate("P0",0,2,2,10)

# setup the coord-sys(portName,drvel-name,ref#(from create),nAxes+1)
# drvAsynMotorConfigure("CS1","pmacAsynCoord",1,9)
# drvAsynMotorConfigure("CS2","pmacAsynCoord",2,9)

# change poll rates (card, poll-period in ms)
pmacSetMovingPollPeriod(1, 100)
pmacSetIdlePollPeriod(1, 1000)
pmacSetCoordMovingPollPeriod(5,200)
pmacSetCoordIdlePollPeriod(5,2000)

#Set scale factor (int ref, int axis, double stepsPerUnit)
#pmacSetCoordStepsPerUnit(0, 6, 10000.0)
#pmacSetCoordStepsPerUnit(0, 7, 10000.0)

## Load record instances
dbLoadTemplate("db/motor.substitutions")
dbLoadTemplate("db/motorstatus.substitutions")
dbLoadTemplate("db/pmacStatus.substitutions")
dbLoadTemplate("db/pmac_asyn_motor.substitutions")
dbLoadTemplate("db/pmacaux.substitutions", PORT=P0)
dbLoadTemplate("db/pmac_physical_limit.substitutions", PORT=P0)
dbLoadTemplate("db/autohome.substitutions")
dbLoadTemplate("db/cs.substitutions")
dbLoadRecords("db/asynComm.db","P=$(IOC_ASYN),PORT=P0,ADDR=0")

## autosave/restore machinery
save_restoreSet_Debug(0)
save_restoreSet_IncompleteSetsOk(1)
save_restoreSet_DatedBackupFiles(1)

set_savefile_path("${TOP}/as","/save")
set_requestfile_path("${TOP}/as","/req")

system("install -m 777 -d ${TOP}/as/save")
system("install -m 777 -d ${TOP}/as/req")

set_pass0_restoreFile("info_positions.sav")
set_pass0_restoreFile("info_settings.sav")
set_pass1_restoreFile("info_settings.sav")

dbLoadRecords("$(EPICS_BASE)/db/save_restoreStatus.db","P=$(IOC_PREFIX)")
dbLoadRecords("$(EPICS_BASE)/db/iocAdminSoft.db","IOC=$(IOC_PREFIX)")
save_restoreSet_status_prefix("$(IOC_PREFIX)")
# asSetFilename("/cf-update/acf/default.acf")

iocInit()

# caPutLogInit("__ARCHIVER__:7004", 1)

## more autosave/restore machinery
cd ${TOP}/as/req
makeAutosaveFiles()
create_monitor_set("info_positions.req", 5 , "")
create_monitor_set("info_settings.req", 15 , "")

cd ${TOP}
dbl > ./records.dbl
system "cp ./records.dbl /cf-update/__HOSTNAME__.__IOCNAME__.dbl"
