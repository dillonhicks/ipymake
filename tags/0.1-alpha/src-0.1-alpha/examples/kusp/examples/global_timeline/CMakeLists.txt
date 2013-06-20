CMAKE_MINIMUM_REQUIRED(VERSION 2.6)

PROJECT( GLOBAL_TIMELINE )

# Install all python scripts using the PROGRAM directive to give
# them executable permissions.
INSTALL( PROGRAMS ${GLOBAL_TIMELINE_SOURCE_DIR}/mpi_netspec
	 DESTINATION bin )
