#ifndef CLKSYNC_H
#define CLKSYNC_H

#ifdef __KERNEL__
#include <linux/ioctl.h>
#include <linux/ip.h>
#endif

/* ioctl commands */
#define CLKSYNC_ADJ_TIME 1
#define CLKSYNC_ADJ_FREQ 2
#define CLKSYNC_GET_INFO 4
#define CLKSYNC_SET_DEV  8
#define CLKSYNC_SET_IRQ  16
#define CLKSYNC_FLAGS_OK ((int)(1|2|4|8|16))

/* ioctl structure for communicating with clksync device */
typedef struct clksync_info_s {
		int flags;
		struct timespec time;

		// CPU timestamp of when this data was filled in
		unsigned long long ts;

		// number of CPU cycles in a millisecond
		unsigned long long tsckhz;

		/// size of device_name, including the \0
		int size;
		char *device_name;

		/// clocksource variables
		unsigned int shift;
		unsigned int mult;

		int irq;
} clksync_info_t;

#define CLKSYNC_CHAR_MAJOR 241
#define CLKSYNC_DEVICE_NAME "clksync"
#define CLKSYNC_IOCTL		_IOWR(CLKSYNC_CHAR_MAJOR, 1, clksync_info_t)
#ifdef __KERNEL__
#include <linux/skbuff.h>
/* information about a eth device */
typedef struct clksync_eth_s {
	char *name;
	unsigned int irq;
	struct list_head link;
} clksync_eth_t;

/* for other kernel locations that use our data such as do_IRQ and eth device
 * drivers
 */
extern unsigned int clksync_irq;
extern unsigned long long clksync_rx_cycles;
extern unsigned long long clksync_tx_cycles;
extern unsigned long long clksync_update_cycles;

unsigned long transmit_time_sync_capture(struct sk_buff *skb);
unsigned long receive_time_sync_capture(struct sk_buff *skb);
int clksync_register_eth(char *name, unsigned int irq);
char *clksync_get_device(void);

extern void clksync_get_info(clksync_info_t *nfo);
extern void clksync_adj_time(struct timespec *);
#endif

#ifdef __KERNEL__
/*
 * KU NTP packet struct definition. everytime the packet changes in
 * userland, this must be updated to reflect the change.
 *
 * in kusp/src/utime/clock_sync/ntp/ntp-<ver>/include/ntp.h is the ntp
 * definition that should be consulted.
 */

typedef signed char  s_char;
typedef unsigned int u_fp;

typedef struct {
	union {
		unsigned int Xl_ui;
		int Xl_i;
	} Ul_i;
	union {
		unsigned int Xl_uf;
		int Xl_f;
	} Ul_f;
} l_fp;

#define l_ui	Ul_i.Xl_ui		/* unsigned integral part */
#define	l_i	Ul_i.Xl_i		/* signed integral part */
#define	l_uf	Ul_f.Xl_uf		/* unsigned fractional part */
#define	l_f	Ul_f.Xl_f		/* signed fractional part */

struct ntp_pkt {
	u_char	li_vn_mode;	/* leap indicator, version and mode */
	u_char	stratum;	/* peer stratum */
	u_char	ppoll;		/* peer poll interval */
	s_char	precision;	/* peer clock precision */
	u_fp	rootdelay;	/* distance to primary clock */
	u_fp	rootdispersion;	/* clock dispersion */
	unsigned int	refid;		/* reference clock ID */
	l_fp	reftime;	/* time peer clock was last updated */
	l_fp	org;		/* originate time stamp */
	l_fp	rec;		/* receive time stamp */
	l_fp	xmt;		/* transmit time stamp */

	unsigned int       magic_num;
        unsigned long long start_ts;       /* start field added at KU */
        unsigned long long rx_ts;          /* rx field added at KU */
        unsigned long long tx_ts;          /* tx field added at KU */
        unsigned long long end_ts;         /* end field added at KU */

	long               xtime_tv_sec;
	long               xtime_tv_nsec;
	unsigned long long xtime_tsc;
	unsigned long      tsc_khz;

	unsigned int	saddr;		/* source address added at KU */
	unsigned int	daddr;		/* destination address added at KU */	
	unsigned int	pkt_id;		/* unique identifier for packet added at KU */

#define	LEN_PKT_NOMAC	(12+17) * sizeof(unsigned int) /* min header length */
#define	LEN_PKT_MAC	LEN_PKT_NOMAC +  sizeof(unsigned int)
#define MIN_MAC_LEN	3 * sizeof(unsigned int)	/* DES */
#define MAX_MAC_LEN	5 * sizeof(unsigned int)	/* MD5 */
#define KU_MAGIC_NUM 2345

	/*
	 * The length of the packet less MAC must be a multiple of 64
	 * with an RSA modulus and Diffie-Hellman prime of 64 octets
	 * and maximum host name of 128 octets, the maximum autokey
	 * command is 152 octets and maximum autokey response is 460
	 * octets. A packet can contain no more than one command and one
	 * response, so the maximum total extension field length is 672
	 * octets. But, to handle humungus certificates, the bank must
	 * be broke.
	 */
	unsigned int	exten[1]; /* misued */
	u_char	mac[MAX_MAC_LEN]; /* mac */
};
#endif
#endif
