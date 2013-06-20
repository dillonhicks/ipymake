
#ifndef pydsui_LOCAL_DSUI_H
#define pydsui_LOCAL_DSUI_H


#ifdef __cplusplus
extern "C" {
#endif

#ifdef CONFIG_DSUI
#include <dsui.h>

extern struct datastream_ip __start___pydsui_datastream_ips[];
extern struct datastream_ip __stop___pydsui_datastream_ips[];

#define DSUI_BEGIN(argcp, argvp) \
    dsui_start((argcp), (argvp), "/tmp/pydsui.dsui.bin");
#define DSUI_CLEANUP() dsui_cleanup()
#define DSUI_START() DSUI_BEGIN(NULL, NULL);
#define DSUI_SIGNAL(a, b) dsui_signal((a),(b))
#define DSTRM_PRINTF dsui_printf


#define DSTRM_EVENT_DATA(gname, ename, tag, data_len, data, edfname) do {    \
    static struct datastream_ip_data __datastream_ip_data_##gname##ename =    \
    {                                    \
        #gname,            \
        #ename,                \
        edfname,                        \
        __FILE__,                        \
        __func__,                        \
        __LINE__,                        \
        DS_EVENT_TYPE,                    \
        {NULL, NULL}, \
        0, \
        NULL,                            \
        {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL} \
    };                            \
    static struct datastream_ip __datastream_ip_##gname##ename    \
    __attribute__((section("__pydsui_datastream_ips"), aligned(8))) =            \
    {                                    \
        &__datastream_ip_data_##gname##ename,            \
        &__datastream_ip_data_##gname##ename.next,        \
        &__datastream_ip_data_##gname##ename.id        \
    };                                    \
    if (*__datastream_ip_##gname##ename.next)                \
        dsui_event_log(&__datastream_ip_##gname##ename,        \
                tag, data_len, data);                \
} while (0)

#define DSTRM_EVENT_DATA_ID(id, gname, ename, tag, data_len, data, edfname) do {    \
    static struct datastream_ip_data __datastream_ip_data_##gname##ename =    \
    {                                    \
        #gname,            \
        #ename,                \
        edfname,                        \
        __FILE__,                        \
        __func__,                        \
        __LINE__,                        \
        DS_EVENT_TYPE,                    \
        {NULL, NULL}, \
        0, \
        NULL,                            \
        {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL} \
    };                            \
    static struct datastream_ip __datastream_ip_##gname##ename    \
    __attribute__((section("__pydsui_datastream_ips"), aligned(8))) =            \
    {                                    \
        &__datastream_ip_data_##gname##ename,            \
        &__datastream_ip_data_##gname##ename.next,        \
        &__datastream_ip_data_##gname##ename.id        \
    };                                    \
    if (*__datastream_ip_##gname##ename.next)                \
        dsui_event_log_single(&__datastream_ip_##gname##ename, (id),    \
                tag, data_len, data);                \
} while (0)

#define DSTRM_COUNTER_DECL(gname, ename)                    \
    static struct datastream_ip_data __datastream_ip_data_##gname##ename = \
    {    \
        #gname,            \
        #ename,                \
        "",                        \
        __FILE__,                        \
        "",                        \
        __LINE__,                        \
        DS_COUNTER_TYPE,                    \
        {NULL, NULL}, \
        0, \
        NULL,                            \
        {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL} \
    };                                    \
    struct datastream_ip __datastream_ip_##gname##ename        \
    __attribute__((section("__pydsui_datastream_ips"), aligned(8))) =            \
    {                                    \
        &__datastream_ip_data_##gname##ename,            \
        &__datastream_ip_data_##gname##ename.next,        \
        &__datastream_ip_data_##gname##ename.id        \
    };                                    

#define DSTRM_INTERVAL_DECL(gname, ename)                    \
    static struct datastream_ip_data __datastream_ip_data_##gname##ename = \
    {                                    \
        #gname,            \
        #ename,                \
        "",                        \
        __FILE__,                        \
        "",                        \
        __LINE__,                        \
        DS_INTERVAL_TYPE,                    \
        {NULL, NULL},                     \
        0,                         \
        NULL,                            \
        {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL} \
    };                                    \
    struct datastream_ip __datastream_ip_##gname##ename        \
    __attribute__((section("__pydsui_datastream_ips"), aligned(8))) =            \
    {                                    \
        &__datastream_ip_data_##gname##ename,        \
        &__datastream_ip_data_##gname##ename.next,        \
        &__datastream_ip_data_##gname##ename.id        \
    };                                    \

#define DSTRM_HISTOGRAM_DECL(gname, ename)                    \
    static struct datastream_ip_data __datastream_ip_data_##gname##ename = \
    {                                    \
        #gname,            \
        #ename,                \
        "",                        \
        __FILE__,                        \
        "",                        \
        __LINE__,                        \
        DS_HISTOGRAM_TYPE,                    \
        {NULL, NULL},                     \
        0,                         \
        NULL,                            \
        {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL} \
    };                                \
    struct datastream_ip __datastream_ip_##gname##ename        \
    __attribute__((section("__pydsui_datastream_ips"), aligned(8))) =            \
    {                                    \
        &__datastream_ip_data_##gname##ename,        \
        &__datastream_ip_data_##gname##ename.next,        \
        &__datastream_ip_data_##gname##ename.id        \
    };                                    \

#else

#define DSTRM_EVENT_DATA(gname, ename, tag, data_len, data, edfname)
#define DSTRM_EVENT(gname, ename, tag)
#define DSTRM_COUNTER_DECL(gname, ename)
#define DSTRM_COUNTER_ADD(gname, ename, amount)
#define DSTRM_COUNTER_LOG(gname, ename)
#define DSTRM_COUNTER_RESET(gname, ename)
#define DSTRM_INTERVAL_DECL(gname, ename)
#define DSTRM_INTERVAL_END(gname, ename, tag)
#define DSTRM_INTERVAL_START(gname, ename)
#define DSTRM_HISTOGRAM_DECL(gname, ename)
#define DSTRM_HISTOGRAM_ADD(gname, ename, amount)
#define DSTRM_HISTOGRAM_LOG(gname, ename)
#define DSTRM_HISTOGRAM_RESET(gname, ename)
#define DSTRM_PRINTF
#define DSUI_BEGIN(x,y)        NULL
#define DSUI_START()        NULL
#define DSUI_CLEANUP()
#define DSUI_SIGNAL(a, b)    signal((a),(b))
#endif // CONFIG_DSUI
#ifdef __cplusplus
}
#endif
#endif
