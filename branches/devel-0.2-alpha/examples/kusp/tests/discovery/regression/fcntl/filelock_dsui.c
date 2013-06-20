
#ifdef CONFIG_DSUI

#include "filelock_dsui.h"
#include <dsui.h>
#include <stdlib.h>

static void filelock_dsui_register() __attribute__ ((constructor));

static void filelock_dsui_register()
{
	dsui_header_check(5, "filelock");
	struct datastream_ip *ip;
	
	for (ip = __start___filelock_datastream_ips;
			ip != __stop___filelock_datastream_ips; ip++) {
		dsui_register_ip(ip);
	}
}
#endif
