#ifndef _DSUI3_ENTITY_PRIVATE_H_
#define _DSUI3_ENTITY_PRIVATE_H_

#include "dsui_private.h"

int histogram_init(const struct datastream_ip_data *ip,
		struct active_entity *entity, union ds_entity_info *einfo);
int histogram_configure(const struct datastream_ip_data *ip,
		struct active_entity *entity, union ds_entity_info *einfo);
void histogram_log(struct datastream_list *next);
void histogram_add(struct datastream_list *next,
		long long amount);
void histogram_reset(struct datastream_list *next);
void histogram_free(struct ds_active_histogram *hist);


int interval_init(const struct datastream_ip_data *ip,
		struct active_entity *entity, union ds_entity_info *einfo);
void interval_start(struct datastream_list *next);
void interval_end(struct datastream_list *next, int tag);


void __event_log(struct datastream *d,
		struct ds_event_record *evt, int data_len, const void *data);


int counter_init(const struct datastream_ip_data *ip,
		struct active_entity *entity, union ds_entity_info *einfo);
void counter_add(struct datastream_list *next, int amount);
void counter_log(struct datastream_list *next);
void counter_reset(struct datastream_list *next);


#endif

