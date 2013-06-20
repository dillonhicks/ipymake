PROJECT( datastreams_regression )
ADD_SUBDIRECTORY( socketpipe )
CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/test.mk
		${CMAKE_CURRENT_BINARY_DIR}/test.mk COPYONLY)

CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/datastreams_import_test.py
		${CMAKE_CURRENT_BINARY_DIR}/datastreams_import_test.py COPYONLY)
