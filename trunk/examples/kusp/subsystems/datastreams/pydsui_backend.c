#include <dsui.h>
#include <string.h>

#define DSTREAM_BUFFER_COUNT 16

static int active_dstream = -1;
static char *dstream_log = NULL;

void dstream_close(void){
  dsui_cleanup();
}

void dstream_open(const char *filename){

  dstream_log = dsui_open_output_file(strdup(filename));
  active_dstream = dsui_open_datastream(dstream_log, DSTREAM_BUFFER_COUNT,
					  STREAM_NORMAL_MODE);
  dsui_enable_all_ips(active_dstream);
}


static struct datastream_ip *dstream_get_ip(char *group, char *name, int type, char *info)
{
	struct datastream_ip *ip;

	ip = dsui_get_ip_byname(group, name);

	if (ip) {
		return ip;
	}

	ip = dsui_create_ip(group, name, type, info);

	if (active_dstream != -1) {
		dsui_enable_ip(active_dstream, ip, NULL);
	}

	return ip;
}


void dstream_print(char *msg){
  dsui_printf(msg);
}

void dstream_event(char *group, char *name, int tag, char* data){
  
  struct datastream_ip *ip;

  ip = dstream_get_ip(group, name, DS_EVENT_TYPE, strdup("print_pickle"));
  
  if(*ip->next){
    
    dsui_event_log(ip, tag, strlen(data), data);

  }


}



void dstream_histogram_add(char *group, char *name, int increment){
  
  struct datastream_ip *ip;

  ip = dstream_get_ip(group, name, DS_HISTOGRAM_TYPE, NULL);
  
  if(*ip->next){
    
    dsui_histogram_add(ip, increment);

  }


}





void dstream_counter_add(char *group, char *name, int increment){
  
  struct datastream_ip *ip;

  ip = dstream_get_ip(group, name, DS_COUNTER_TYPE, NULL);
  
  if(*ip->next){
    
    dsui_counter_add(ip, increment);

  }


}


void dstream_interval_start(char *group, char *name){
  
  struct datastream_ip *ip;

  ip = dstream_get_ip(group, name, DS_INTERVAL_TYPE, NULL);
  
  if(*ip->next){
    
    dsui_interval_start(ip);
    
  }


}

void dstream_interval_end(char *group, char *name, int tag){

  struct datastream_ip *ip;

  ip = dstream_get_ip(group, name, DS_INTERVAL_TYPE, NULL);
  
  if(*ip->next){
    
    dsui_interval_end(ip, tag);
    
  }


}
