from pygsched import gschedapi
import sys

fd = gschedapi.grp_open()
ret = gschedapi.gsched_uninstall_group(fd, "socket_pipeline")
ret = gschedapi.grp_destroy_group(fd, "socket_pipeline")
