#ifndef DSKI_NETDATA_H
#define DSKI_NETDATA_H



#include <linux/dski.h>
#include <linux/tcp.h>
#include <linux/ip.h>
#include <net/inet_sock.h>

typedef struct  {
	__u16 sport;
	__u16 dport;
	__u32 sequence;
	__u32 daddr;
	__u32 saddr;
	pid_t pid;
} dski_network_data_t;

typedef struct  {
	__u16 sport;
	__u16 dport;
	__u32 sequence;
	__u32 daddr;
	__u32 saddr;
	__u16 ip_id;
	__u16 frag_off;
	__u16 mf;
	pid_t pid;
	__u32 saddr2;
} dski_ip_network_data_t;


#define DSTRM_NETEVENT(fam, name, netdata) DSTRM_EVENT_DATA(fam, name, 0, sizeof(netdata), &netdata, \
		"get_netdata")

static inline dski_network_data_t get_dski_netdata_from_sock(struct sock *sk) {
	dski_network_data_t netdata;
	struct inet_sock *inet;
	
	memset(&netdata, 0, sizeof(netdata));

	inet = inet_sk(sk);

	netdata.pid = current->pid;

	if (inet) {
		netdata.dport = ntohs(inet->dport);
		netdata.sport = ntohs(inet->sport);
		netdata.saddr = ntohl(inet->saddr);
		netdata.daddr = ntohl(inet->daddr);
	}

	return netdata;
}

static inline dski_network_data_t get_dski_netdata_from_sock2(struct socket *sock)
{
	struct inet_sock *inet;
	dski_network_data_t netdata;
	memset(&netdata, 0, sizeof(netdata));
	netdata.pid = current->pid;

	if (sock)
		inet = (struct inet_sock*)(sock->sk);

	if (inet) {
		netdata.sport = ntohs(inet->sport);
		netdata.dport = ntohs(inet->dport);
		netdata.saddr = ntohl(inet->saddr);
		netdata.daddr = ntohl(inet->daddr);
	}
	return netdata;
}



static inline dski_network_data_t get_dski_outgoing_netdata(struct sk_buff *skb)
{
	dski_network_data_t netdata;
	struct inet_sock *inet;
	struct tcphdr *hdr_tcp;

	memset(&netdata, 0, sizeof(netdata));	

	netdata.pid = current->pid;
	
	if (skb!=NULL && skb->sk != NULL) {
		inet = inet_sk(skb->sk);

		netdata.sport = ntohs(inet->sport);
		netdata.dport = ntohs(inet->dport);
		netdata.saddr = ntohl(inet->saddr);
		netdata.daddr = ntohl(inet->daddr);

		hdr_tcp=tcp_hdr(skb);

		if (hdr_tcp != NULL) {
			netdata.sequence = ntohl(hdr_tcp->seq);
		}
	}

	return netdata;
}

static inline dski_network_data_t dski_incoming_netdata(struct sk_buff *skb) 
{
	dski_network_data_t netdata;
	unsigned char *temp, ipversion, ihl;

	memset(&netdata, 0, sizeof(netdata));	
	netdata.pid = current->pid;

  	if(skb!=NULL && skb->data!=NULL){
		
		// source address is a 32 bit value stored 96 bits (12 bytes)
		// into the IP header
		temp = skb->data + 12;
		netdata.saddr = ntohl(*((__u32*)temp));

		// dest address is a 32 bit value stored 128 bits (16 bytes)
		// into the IP header
		temp = skb->data + 16;
		netdata.daddr = ntohl(*((__u32*)temp));

		// get the first 8 bits of the ip header
      		ipversion = *(skb->data);
      		// the header length is stored in the last 4 bits, so
		// mask out the first 4 (which is the ip version). it
		// specifies the number of 32-bit words in the header,
		// so to get the length in bytes, multiply that by 4.
      		ihl = (ipversion & 0x0F) * 4;

		/* Obtain the source port from TCP Header */
		// this is stored in the first 16 bits of the
		// TCP header.
		temp = skb->data + ihl;
		netdata.sport = ntohs(*((__u16*)temp));
		
		/* Obtain the destination port from TCP Header */
		temp = skb->data + ihl + 2;
		netdata.dport = ntohs(*((__u16*)temp));

		/* Obtain TCP Sequence Number from TCP Header */
		temp = skb->data + ihl + 4;
		netdata.sequence = ntohl(*((__u32*)temp));
	}

	return netdata;
}

static inline dski_network_data_t get_dski_incoming_tcp_netdata(struct sk_buff *skb)
{
	struct tcphdr *tcpheader;
	dski_network_data_t netdata;

	memset(&netdata, 0, sizeof(netdata));	
	
	netdata.pid = current->pid;	
	
	if(skb){
		if(skb->data){
			tcpheader = (struct tcphdr *)skb->data;
			netdata.sport = ntohs(tcpheader->source);
			netdata.dport = ntohs(tcpheader->dest);
			netdata.sequence = ntohl(tcpheader->seq);
		}
	}
	return netdata;
}



#endif

