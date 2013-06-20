#ifndef MESSAGE_HPP
#define MESSAGE_HPP

/* Maximum size of the data in a message. */
/* Should be a multiple of 3, ie: rgb triplets. */
#define MAX_PAYLOAD 4002

struct Message
{

	int size() const { return sizeof(int) + payload_len; }
	int read(int fd)
	{
		int length;

		length = recv(fd, &payload_len, sizeof(payload_len), 0);

		if (length > 0) {
			recv(fd, &payload, payload_len, 0);
		}

		return length;
	}

        int payload_len;
	unsigned char payload[MAX_PAYLOAD];
};


#endif
