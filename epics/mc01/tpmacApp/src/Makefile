TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application
#STATIC_BUILD=YES
#SHARED_LIBRARIES=NO

PROD_IOC = tpmac
# tpmac.dbd will be created and installed
DBD += tpmac.dbd

# tpmac.dbd will be made up from these files:
tpmac_DBD += base.dbd

# Include dbd files from all support applications:
#tpmac_DBD += system.dbd
tpmac_DBD += devIocStats.dbd
tpmac_DBD += caPutLog.dbd


# Include dbd files from all support applications:
tpmac_DBD += asyn.dbd
tpmac_DBD += motorSupport.dbd
tpmac_DBD += drvAsynIPPort.dbd
tpmac_DBD += drvAsynSerialPort.dbd
tpmac_DBD += pmacAsynMotor.dbd
tpmac_DBD += pmacAsynIPPort.dbd
tpmac_DBD += pmacAsynCoord.dbd
tpmac_DBD += asSupport.dbd
tpmac_DBD += busySupport.dbd
tpmac_DBD += calcSupport.dbd
tpmac_DBD += system.dbd
tpmac_DBD += stream.dbd
tpmac_DBD += devSoft.dbd
tpmac_DBD += devSoftMotor.dbd
tpmac_DBD += devIocStats.dbd
tpmac_DBD += caPutLog.dbd

# Add all the support libraries needed by this IOC
tpmac_LIBS += devIocStats
tpmac_LIBS += caPutLog

# Add all the support libraries needed by this IOC
tpmac_LIBS += pmacAsynMotorPort
tpmac_LIBS += pmacAsynMotor
tpmac_LIBS += pmacAsynIPPort
tpmac_LIBS += pmacAsynCoord
tpmac_LIBS += motor
tpmac_LIBS += softMotor
tpmac_LIBS += asyn
tpmac_LIBS += autosave
tpmac_LIBS += busy
tpmac_LIBS += calc
tpmac_LIBS += stream
tpmac_LIBS += sscan
tpmac_LIBS += devIocStats
tpmac_LIBS += caPutLog

# tpmac_registerRecordDeviceDriver.cpp derives from tpmac.dbd
tpmac_SRCS += tpmac_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
tpmac_SRCS_DEFAULT += tpmacMain.cpp
tpmac_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#tpmac_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
tpmac_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

