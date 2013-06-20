PROJECT( dstream_ki )


# Install the dsui-header python script 
# using the PROGRAM directive to give it executable
# permissions.
#
INSTALL( PROGRAMS ${dstream_ki_SOURCE_DIR}/tools/dski-parse 
		${dstream_ki_SOURCE_DIR}/dskid/dskictrl 
		${dstream_ki_SOURCE_DIR}/dskid/dskid
		${dstream_ki_SOURCE_DIR}/dskid/dskitrace
		${dstream_ki_SOURCE_DIR}/dskid/dskilogd
		DESTINATION bin )
		
INSTALL( FILES ${dstream_ki_SOURCE_DIR}/dskid/dskid.cspec
		${dstream_ki_SOURCE_DIR}/dskid/dskid.gsc
		${dstream_ki_SOURCE_DIR}/dskid/dskid.template
		${dstream_ki_SOURCE_DIR}/dskid/example.dski
		${dstream_ki_SOURCE_DIR}/dskid/pidfilter.dski		
		DESTINATION share )
