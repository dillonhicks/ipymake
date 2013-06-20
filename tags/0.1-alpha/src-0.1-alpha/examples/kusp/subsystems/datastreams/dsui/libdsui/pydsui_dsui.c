
#ifdef CONFIG_DSUI

#include "pydsui_dsui.h"
#include <dsui.h>
#include <stdlib.h>

static void pydsui_dsui_register() __attribute__ ((constructor));

static void pydsui_dsui_register()
{
    dsui_header_check(5, "pydsui");
    struct datastream_ip *ip;
    
    for (ip = __start___pydsui_datastream_ips;
            ip != __stop___pydsui_datastream_ips; ip++) {
        dsui_register_ip(ip);
    }
}
#endif
