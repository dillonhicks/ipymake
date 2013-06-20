PROJECT(balanced-pipeline)

LINK_LIBRARIES(gsched kusp pthread dsui m)

#
# This is the equivalent of -I.
#
INCLUDE_DIRECTORIES(${CMAKE_CURRENT_BINARY_DIR})

SET(CMAKE_C_FLAGS "-DCONFIG_DSUI -Wall")

ADD_CUSTOM_COMMAND(
	OUTPUT pipeline_dsui.c pipeline_dsui.h
	COMMAND ${CMAKE_COMMAND} -E echo_append "Generating DSUI template"
	COMMAND dsui-header --prefix pipeline
)

ADD_EXECUTABLE(balanced-pipeline
	pipeline.c
	pipeline_dsui.h
	pipeline_dsui.c
)

INSTALL(TARGETS balanced-pipeline RUNTIME DESTINATION bin)
