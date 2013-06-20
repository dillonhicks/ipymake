
#ifdef CONFIG_DSUI

#include "libdsui_dsui.h"
#include <dsui.h>
#include <stdlib.h>

static void libdsui_dsui_register() __attribute__ ((constructor));

static void libdsui_dsui_register()
{
	dsui_header_check(5, "libdsui");
	struct datastream_ip *ip;

	for (ip = __start___libdsui_datastream_ips;
			ip != __stop___libdsui_datastream_ips; ip++) {
		dsui_register_ip(ip);
	}
}
#endif
