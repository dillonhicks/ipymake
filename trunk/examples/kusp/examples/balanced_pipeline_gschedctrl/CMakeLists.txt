PROJECT( BALANCED-PIPELINE-GSCHEDCTRL )

LINK_LIBRARIES(gsched kusp pthread dsui m)

#
# This is the equivalent of -I.
#
INCLUDE_DIRECTORIES(${CMAKE_CURRENT_BINARY_DIR})

SET(CMAKE_C_FLAGS "-DCONFIG_DSUI -Wall")

ADD_CUSTOM_COMMAND(
	OUTPUT bp_gschedctrl_dsui.c bp_gschedctrl_dsui.h
	COMMAND ${CMAKE_COMMAND} -E echo_append "Generating DSUI template"
	COMMAND dsui-header --prefix bp_gschedctrl
)

ADD_EXECUTABLE(bp_gschedctrl
	bp_gschedctrl.c
	bp_gschedctrl_dsui.h
	bp_gschedctrl_dsui.c
)

INSTALL(TARGETS bp_gschedctrl RUNTIME DESTINATION bin)
