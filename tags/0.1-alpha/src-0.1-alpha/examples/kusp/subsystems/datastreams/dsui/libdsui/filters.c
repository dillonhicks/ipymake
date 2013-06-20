#include "filters.h"

/**
 * Apply a stream's filter chain to a particular event.
 * Note that calling this function may generate more events
 *
 * @param stream stream that event was generated for
 * @param event event to place in filter pipeline
 * @retval 0 The event should not be logged
 * @retval nonzero Go ahead and log the event
 */
int apply_filters(struct datastream *d, struct dstrm_pipeline *pipeline, 
		struct ds_event_record *event)
{
	/* if no pipeline is set, then accept all events */
	if (pipeline == NULL)
		return 1;

	
	/* stub */
	return 1;
}

