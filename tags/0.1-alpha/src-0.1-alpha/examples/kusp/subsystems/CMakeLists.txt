# $KUSPROOT/subsystems/CMakeLists.txt
# ORDER MATTERS!  
#
# The dependecies aren't explicitly stated in the
# code, but they are in the comments.
#

# Depends On : None
#
IF(IS_RPM_BUILD)
    IF((DEFINED COMMON_RPM) OR (ALL_RPMS))
        ADD_SUBDIRECTORY( common )
    ENDIF()
ELSE()
	ADD_SUBDIRECTORY( common )
ENDIF()

# Depends on: common
#
IF(IS_RPM_BUILD)
    IF((DEFINED DATASTREAMS_RPM) OR (ALL_RPMS))
        ADD_SUBDIRECTORY( datastreams )
    ENDIF()
ELSE()
	ADD_SUBDIRECTORY( datastreams )
ENDIF()


# Depends on: common
#
IF(IS_RPM_BUILD)
    IF((DEFINED GSCHED_RPM) OR (ALL_RPMS))
        ADD_SUBDIRECTORY( gsched )
    ENDIF()
ELSE()
	ADD_SUBDIRECTORY( gsched )
ENDIF()


# Depends on: common
#
IF(IS_RPM_BUILD)
    IF((DEFINED CCSM_RPM) OR (ALL_RPMS))
        ADD_SUBDIRECTORY( ccsm )
    ENDIF()
ELSE()
	ADD_SUBDIRECTORY( ccsm )
ENDIF()


# Depends on: common datastreams
#
IF(IS_RPM_BUILD)
    IF((DEFINED DISCOVERY_RPM) OR (ALL_RPMS))
        ADD_SUBDIRECTORY( discovery )
    ENDIF()
ELSE()
	ADD_SUBDIRECTORY( discovery )
ENDIF()

# Depends on: common
#
IF(IS_RPM_BUILD)
    IF((DEFINED CLKSYNC_RPM) OR (ALL_RPMS))
        ADD_SUBDIRECTORY( clksync )
    ENDIF()
ELSE()
	ADD_SUBDIRECTORY( clksync )
ENDIF()


# Depends on: common
#
IF(IS_RPM_BUILD)
    IF((DEFINED NETSPEC_RPM) OR (ALL_RPMS))
        ADD_SUBDIRECTORY( netspec )
    ENDIF()
ELSE()
	ADD_SUBDIRECTORY( netspec )
ENDIF()

