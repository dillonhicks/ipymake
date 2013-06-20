#ifndef _FILTERS_H_
#define _FILTERS_H_

#include <dsentity.h>

#include "datastream.h"

struct dstrm_pipeline;

int apply_filters(struct datastream *d, struct dstrm_pipeline *pipeline,
		struct ds_event_record *event);

#endif
