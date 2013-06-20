PROJECT(ntp)

SET( ntp_version 4.2.4p7 )
SET( ntp_link http://www.eecis.udel.edu/~ntp/ntp_spool/ntp4/ntp-${ntp_version}.tar.gz )

# Download and patch the specified NTP source.
ADD_CUSTOM_TARGET( ntp_prep ALL DEPENDS ntp-${ntp_version} )
ADD_CUSTOM_COMMAND( OUTPUT ntp-${ntp_version}
		   COMMAND wget ${ntp_link}
		   COMMAND rm -rf ntp-${ntp_version}
		   COMMAND tar -xzf ntp-${ntp_version}.tar.gz
		   COMMAND patch -p1 -d ntp-${ntp_version} < ${ntp_SOURCE_DIR}/ntp-${ntp_version}.patch
		   COMMAND rm -f ntp-${ntp_version}.tar.gz
		   WORKING_DIRECTORY ${ntp_BINARY_DIR}
		   COMMENT "Downloading and patching NTP." 
		   VERBATIM )

# Configure and build the modified NTP source.
ADD_CUSTOM_TARGET( ntp_build ALL DEPENDS ku_ntpdate ntpd )
ADD_CUSTOM_COMMAND( OUTPUT ku_ntpdate ntpd
		   COMMAND autoreconf -i -v
		   COMMAND ./configure --with-kusproot=${CMAKE_INSTALL_PREFIX} --prefix=${CMAKE_INSTALL_PREFIX}		
		   COMMAND LD_RUN_PATH=${CMAKE_INSTALL_PREFIX}/lib make
		   COMMAND cp ntpdate/ku_ntpdate ${ntp_BINARY_DIR}
		   COMMAND cp ntpd/ntpd ${ntp_BINARY_DIR}
		   DEPENDS ntp-${ntp_version}
		   WORKING_DIRECTORY ${ntp_BINARY_DIR}/ntp-${ntp_version}
		   COMMENT "Building NTP."
		   VERBATIM )

# Ensure that building takes place after prep.
ADD_DEPENDENCIES( ntp_build ntp_prep )

# Install our ntp.conf example into the share directory.
INSTALL( FILES ${ntp_SOURCE_DIR}/ku-ntp.conf
	 DESTINATION share)
# Install our modified NTP executables into the bin directory.
INSTALL( PROGRAMS ${ntp_BINARY_DIR}/ku_ntpdate 
		  ${ntp_BINARY_DIR}/ntpd 
	 DESTINATION bin)
