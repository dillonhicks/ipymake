
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <pthread.h>

#include "simple_dsui.h"

DSTRM_HISTOGRAM_DECL(FUNC_LOOP, SUM);
DSTRM_INTERVAL_DECL(FUNC_LOOP, DSUI_OVERHEAD);
DSTRM_COUNTER_DECL(FUNC_LOOP, ITER_COUNT);

void display_onto_stdout(const char *str)
{
	/* Entered the display function. Note that we are logging the function
	 * parameter as extra data
	 */
	DSTRM_EVENT_DATA(FUNC_DISPLAY, ENTER, 0, strlen(str),
		    str, "print_string");
	printf("%s\n", str);

	/* Exiting the display function */
	DSTRM_EVENT(FUNC_DISPLAY, EXIT, 0);

	return;
}

double find_cosine(double value)
{
	double retval;
	/* Entered the cosine function. Note that we are logging the function
	 * parameter as extra data
	 */
	DSTRM_EVENT_DATA(FUNC_COSINE, ENTER, 0, sizeof(double),
		&value, "print_double");
	retval = cos(value);
	/* Returning from the cosine function */
	DSTRM_EVENT_DATA(FUNC_COSINE, EXIT, 0, sizeof(double), 
		&retval, "print_double");
	return retval;

}

void useless_loop(int iterations)
{
	DSTRM_EVENT_DATA(FUNC_LOOP, ENTER, 0, sizeof(int),
		&iterations, "print_int");
	int i;
	for (i = 0; i < iterations; i++) {
		DSTRM_INTERVAL_START(FUNC_LOOP, DSUI_OVERHEAD);
		DSTRM_EVENT(FUNC_LOOP, ITER_ONE, i);
		DSTRM_COUNTER_ADD(FUNC_LOOP, ITER_COUNT, 1);
		long long t1, t2;
		t1 = random();
		t2 = random();
		DSTRM_HISTOGRAM_ADD(FUNC_LOOP, SUM, t1+t2);
		DSTRM_EVENT(FUNC_LOOP, ITER_TWO, i);
		DSTRM_INTERVAL_END(FUNC_LOOP, DSUI_OVERHEAD, 0);
	}
	DSTRM_EVENT(FUNC_LOOP, EXIT, 0);
}

void bigbuf_test(int size)
{
	char *bigbuf = malloc(size * sizeof(char));
	int i;

	for (i=0; i<size; i++) {
		bigbuf[i] = 'a' + (i % 26);
	}

	DSTRM_EVENT_DATA(FUNC_BIGBUF, LARGE_DATA, size, size, bigbuf, "print_string");
}

int main(int argc, char **argv)
{
	char choice;
	double x;
	int i;

	DSUI_BEGIN(&argc, &argv);

	/* We have entered main -tag 0 */
	DSTRM_EVENT(FUNC_MAIN, IN_MAIN_FUNC, 0);

	/* We are calling the display function here */
	DSTRM_EVENT(FUNC_MAIN, CALLING_FUNC_DISPLAY, 1);
	display_onto_stdout("Simple Program");

	/* We are calling the cosine function here */
	DSTRM_EVENT(FUNC_MAIN, CALLING_FUNC_COSINE, 1);
	x = find_cosine(45.0);
	DSTRM_PRINTF("cosine of 45 is %f\n", x);

	x = find_cosine(0);
	DSTRM_PRINTF("cosine of 0 is %f\n", x);

	DSTRM_EVENT(FUNC_MAIN, CALLING_FUNC_LOOP, 1);
	useless_loop(10000);

	bigbuf_test(150000);
	
	DSTRM_EVENT(FUNC_MAIN, CALLING_FUNC_DISPLAY, 2);
	display_onto_stdout("Done Executing this Simple Program");

	/* We are exiting main -tag 999 */
	DSTRM_EVENT(FUNC_MAIN, IN_MAIN_FUNC, 999);

	DSUI_CLEANUP();
	return 0;
}

