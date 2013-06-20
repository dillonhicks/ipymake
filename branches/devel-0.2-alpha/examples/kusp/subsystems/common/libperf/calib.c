#include <stdio.h>
#include <sys/time.h>
#include <time.h>

static float dummy;
static unsigned int loop_curr;

static unsigned int loop_avg;
static unsigned int loop_sum;
static unsigned int loop_cnt;

#define NSEC_PER_SEC	1000000000
#define NSEC_PER_MSEC	1000000
#define NSEC_PER_USEC	1000

static inline long long timeval_to_ns(const struct timeval *tv)
{
	return ((long long)tv->tv_sec * NSEC_PER_SEC) +
		tv->tv_usec * NSEC_PER_USEC;
}

static inline long long timeval_subtract(struct timeval *a, struct timeval *b)
{
	return timeval_to_ns(a) - timeval_to_ns(b);
}

int main(int argc, char **argv)
{
	struct timeval start, stop;
	long long duration, target, diff, range;
	int i, counter, in_range;

	loop_sum = 0;
	loop_cnt = 0;
	loop_curr = 10;
	dummy = 2.7;
	in_range = 0;

	/* 10 milliseconds */
	target = 10*NSEC_PER_MSEC;
	/* +/- 0.5 millisecond */
	range = 500*NSEC_PER_USEC;

	while (1) {
	
		/* run work loop */
		gettimeofday(&start, NULL);
		for (i = 0; i < loop_curr; i++) {
			dummy *= 2.7;
		}
		gettimeofday(&stop, NULL);

		/* how long it took */
		duration = timeval_subtract(&stop, &start);

		/* how far from target */
		diff = duration - target;

		/* With range of our target */
		if (((-range < diff) && (diff <= 0)) ||
						((0 <= diff) && (diff < range))) {
			loop_sum += loop_curr;
			loop_cnt += 1;
			loop_avg = loop_sum/loop_cnt;

			in_range = 1;
		} else
			in_range = 0;

		/* linear adjustment when in range */
		if (in_range) {
			if (diff < 0) {
				loop_curr += 100;
			} else if (diff > 0) {
				loop_curr -= 100;
			}
		/* larger adjustments */
		} else {
			if (diff < 0) {
				loop_curr *= 3;
			} else if (diff > 0) {
				loop_curr /= 2;
			}
		}

		counter++;
		if (counter % 100 == 0)
			printf("loop_sum: %u, loop_cnt: %u, loop_avg: %u, loop_curr: %u, "\
							"diff: %lld, duration: %lld\n",
							loop_sum, loop_cnt, loop_avg, loop_curr, diff, duration);
	}
}
