PROJECT( dstream_ui )

#
# Includes the datastream headers.
#
INCLUDE_DIRECTORIES( ${datastreams_SOURCE_DIR}/include )

#
# Includes the kusp-common headers (OLD kusp-base sources)
#
INCLUDE_DIRECTORIES( ${kusp-common_SOURCE_DIR}/include )

SET(CMAKE_C_FLAGS "-fPIC")

#
# Creates the dsui library. (libdsui.a, OLD libdsui.la)
# NOTE: CMake automatically prefixes libraries with lib. Thus, putting libdsui
# creates liblibdsui.a
#
ADD_LIBRARY(dsui STATIC ${dstream_ui_SOURCE_DIR}/libdsui/dstrm_buffer.c 
	${dstream_ui_SOURCE_DIR}/libdsui/dstrm_buffer.h 
	${dstream_ui_SOURCE_DIR}/libdsui/buffer_thread.c 
	${dstream_ui_SOURCE_DIR}/libdsui/buffer_thread.h 	
	${dstream_ui_SOURCE_DIR}/libdsui/logging_thread.c 
	${dstream_ui_SOURCE_DIR}/libdsui/logging_thread.h
	${dstream_ui_SOURCE_DIR}/libdsui/pool.c
	${dstream_ui_SOURCE_DIR}/libdsui/pool.h
	${dstream_ui_SOURCE_DIR}/libdsui/buffer_queue.c
	${dstream_ui_SOURCE_DIR}/libdsui/buffer_queue.h 
	${dstream_ui_SOURCE_DIR}/libdsui/dsui.c
	${dstream_ui_SOURCE_DIR}/libdsui/filters.h
	${dstream_ui_SOURCE_DIR}/libdsui/filters.c 
	${dstream_ui_SOURCE_DIR}/libdsui/entity.c
	${dstream_ui_SOURCE_DIR}/libdsui/entity.h 
	${dstream_ui_SOURCE_DIR}/libdsui/datastream.c
	${dstream_ui_SOURCE_DIR}/libdsui/datastream.h
	${dstream_ui_SOURCE_DIR}/libdsui/clksyncapi.c
	${dstream_ui_SOURCE_DIR}/libdsui/dstream_header.c
	${dstream_ui_SOURCE_DIR}/libdsui/log_functions.c )

ADD_LIBRARY(pydsui STATIC ${dstream_ui_SOURCE_DIR}/libdsui/pydsui.c 
	${dstream_ui_SOURCE_DIR}/libdsui/pydsui_dsui.h
	 ${dstream_ui_SOURCE_DIR}/libdsui/pydsui_dsui.c)



CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/libdsui/pydsui.i
				${CMAKE_CURRENT_BINARY_DIR}/pydsui.i COPYONLY )
CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/libdsui/pydsui.c
				${CMAKE_CURRENT_BINARY_DIR}/pydsui.c COPYONLY )		
CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/libdsui/pydsui_dsui.c
				${CMAKE_CURRENT_BINARY_DIR}/pydsui_dsui.c COPYONLY )		
CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/libdsui/pydsui_dsui.c
				${CMAKE_CURRENT_BINARY_DIR}/pydsui_dsui.h COPYONLY )		


ADD_CUSTOM_COMMAND( OUTPUT swig_setup 
                    COMMAND swig -python ${CMAKE_CURRENT_SOURCE_DIR}/libdsui/pydsui.i
                    COMMAND mv ${CMAKE_CURRENT_SOURCE_DIR}/libdsui/pydsui.py
                       ${CMAKE_CURRENT_SOURCE_DIR}/../pydstrm/pydsui.py
                    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                    COMMENT "Creating pydsui SWiG Python Wrappers." VERBATIM )

#
# Specifying the dsui library to be installed.
#
INSTALL(TARGETS dsui pydsui ARCHIVE DESTINATION lib)
INSTALL(FILES ${dstream_ui_SOURCE_DIR}/libdsui/libdsui_dsui.h
		DESTINATION include)

#
# Install the dsui-header python script 
# using the PROGRAM directive to give it executable
# permissions.
#
INSTALL( PROGRAMS ${dstream_ui_SOURCE_DIR}/tools/dsui-header
		DESTINATION bin )
