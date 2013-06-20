#include <unistd.h>
#include <stdio.h>
#include <comedilib.h>

#define BLINK_PERIOD_MSECS 2000
#define DEVFILE "/dev/comedi0"
#define IN_SUBDEV   0
#define IN_CHANNEL  0
#define OUT_SUBDEV  5
#define OUT_CHANNEL 0
#define LED_ON  1
#define LED_OFF 2

static comedi_t *dev;
static lsampl_t maxdata;
static int led_state;
static lsampl_t max_input;
static lsampl_t min_input;

extern int kurt_suspend(void);

void led_off(void)
{
  //	comedi_data_write(dev, OUT_SUBDEV, OUT_CHANNEL, 0, AREF_DIFF, 0);
	comedi_dio_write(dev, OUT_SUBDEV, 0, 0);
	led_state = LED_OFF;
	return;
}

void led_on(void)
{
  //	comedi_data_write(dev, OUT_SUBDEV, OUT_CHANNEL, 0, AREF_DIFF, maxdata);
	comedi_dio_write(dev, OUT_SUBDEV, 0, 1);
	led_state = LED_ON;
	return;
}

lsampl_t get_sample(void)
{
	lsampl_t data;
	comedi_data_read(dev, IN_SUBDEV, IN_CHANNEL, 0, AREF_DIFF, &data);
	return data;
}

float get_period_coeff(void)
{
	char ch;
	lsampl_t temp;

	/*
	 * This is some barebones c code sufficient to grab a little
	 * data from the user, but it rather ugly.
	 */
	printf("get first extreme. 'y' to accept, 'n' for next value.\n");
	do {
		max_input = get_sample();
		printf("%u :", max_input);
		ch = getchar();
		if (ch != '\n')
			while (getchar() != '\n') { getchar(); }
	} while (ch != 'y');

	printf("get second extreme. 'y' to accept, 'n' for next value.\n");
	do {
		min_input = get_sample();
		printf("%u :", min_input);
		ch = getchar();
		if (ch != '\n')
			while (getchar() != '\n') { getchar(); }
	} while (ch != 'y');

	/*
	 * sort out the bounds selected by the user.
	 */
	if (min_input > max_input) {
		temp = max_input;
		max_input = min_input;
		min_input = temp;
	}

	/* return the period coefficient */

	return (float)BLINK_PERIOD_MSECS / (float)(max_input-min_input);
}

int main(int argc, char *argv[])
{
	lsampl_t data;
	int countdown;
	float period_coeff;

	/*
	 * Open the comedi device
	 */
	dev = comedi_open(DEVFILE);
	if (!dev) {
	  perror("comedi_open");
	  printf("cannot open %s.\n", DEVFILE);
	  exit(1);
	}
	
	/*
	 * Aquire a maximum value for the output channel. This will be
	 * written to the output channel when we wish the LED to
	 * activate.
	 */
	maxdata = comedi_get_maxdata(dev, OUT_SUBDEV, OUT_CHANNEL);
	
	/* start w/ the led off */
	led_off();


	printf("off ");
	/*
	 * This is the main work loop. The loop represents a period of
	 * work, in our case the period of work is 1 millisecond.
	 */
	while(1)
	{
		

		led_on();
		printf("on ");
		fflush(stdout);
		sleep(1);
		led_off();
		printf("off ");
		fflush(stdout);
		sleep(1);
	}
	
	/* close the comedi device. */
	comedi_close(dev);
}
