#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#define __USE_GNU
#include <sched.h>
#include <sys/mman.h>
#include <getopt.h>
#include <pthread.h>
#include <signal.h>
#include <errno.h>
#include <sys/types.h>
#include <linux/unistd.h>

//#include <ccsm.h>
#include "sigpipe_dsui.h"

#define gettid() syscall(__NR_gettid)

#define WORK_LOOPS 20000

/* start display test code */
#include <ncurses.h>
#include <stdlib.h>
#include <string.h>




#define STATUS_START	0
#define STATUS_RUN 		1
#define STATUS_WAIT		2
#define STATUS_TERM		3

typedef struct _win_border_struct {
	chtype 	ls, rs, ts, bs,
	 	tl, tr, bl, br;
}WIN_BORDER;

typedef struct _WIN_struct {

	int startx, starty;
	int height, width;
	WIN_BORDER border;
}WIN;

typedef struct _experiment_thread_struct {
	int name;
	int progress;
	int status;
}EXP_THREAD;


EXP_THREAD exp_threads[100];
int disp_threads = 0;

void init_win_params(WIN *p_win, int winy, int winx);
void print_win_params(WIN *p_win);
void create_box(WIN *win, bool flag);
void add_thread(char* t_name);
void refresh_tables();

int init_experiment_display()
{	WIN win_threads;


	initscr();			/* Start curses mode 		*/
	cbreak();			/* Line buffering disabled, Pass on
					 * everty thing to me 		*/
	noecho();
	start_color();			/* Start color 			*/
	init_pair(1, COLOR_GREEN, COLOR_BLACK);
	init_pair(2, COLOR_BLUE, COLOR_BLACK);
	init_pair(3, COLOR_RED, COLOR_BLACK);

	/* Initialize the window parameters */
	init_win_params(&win_threads, 0, 0);
	print_win_params(&win_threads);


	create_box(&win_threads, TRUE);
	mvprintw(1,1, "          THREADS        |        PROGRESS         |         STATUS      ");

	refresh();
	refresh_tables();


	return 0;
}

void init_win_params(WIN *p_win, int winy, int winx)
{
	p_win->height = 2;
	p_win->width = 80;
	p_win->starty = winy;
	p_win->startx = winx;

	p_win->border.ls = ACS_CKBOARD;
	p_win->border.rs = ACS_CKBOARD;
	p_win->border.ts = ACS_CKBOARD;
	p_win->border.bs = ACS_CKBOARD;
	p_win->border.tl = ACS_CKBOARD;
	p_win->border.tr = ACS_CKBOARD;
	p_win->border.bl = ACS_CKBOARD;
	p_win->border.br = ACS_CKBOARD;

}
void print_win_params(WIN *p_win)
{
#ifdef _DEBUG
	mvprintw(25, 0, "%d %d %d %d", p_win->startx, p_win->starty,
				p_win->width, p_win->height);
	refresh();
#endif
}
void create_box(WIN *p_win, bool flag)
{	int i, j;
	int x, y, w, h;

	x = p_win->startx;
	y = p_win->starty;
	w = p_win->width;
	h = p_win->height;

	if(flag == TRUE)
	{	mvaddch(y, x, p_win->border.tl);
		mvaddch(y, x + w, p_win->border.tr);
		mvaddch(y + h, x, p_win->border.bl);
		mvaddch(y + h, x + w, p_win->border.br);
		mvhline(y, x + 1, p_win->border.ts, w - 1);
		mvhline(y + h, x + 1, p_win->border.bs, w - 1);
		mvvline(y + 1, x, p_win->border.ls, h - 1);
		mvvline(y + 1, x + w, p_win->border.rs, h - 1);

	}
	else
		for(j = y; j <= y + h; ++j)
			for(i = x; i <= x + w; ++i)
				mvaddch(j, i, ' ');

	refresh();

}

void add_thread(char* t_name){
	EXP_THREAD* e_thread;
	e_thread = &exp_threads[disp_threads];
	e_thread->name = disp_threads;
	e_thread->progress = 0;
	e_thread->status = STATUS_WAIT;
	disp_threads += 1;
}
void close_display(){
	endwin();
}
void refresh_tables(){
	int tc = 0;
	int lnstart = 3;
	int statusx = 52;
	EXP_THREAD* e_thread;
	for(; tc < disp_threads; ++tc){
		e_thread = &exp_threads[tc];
		mvprintw(tc+lnstart, 0, "%d", e_thread->name);
		mvprintw(tc+lnstart, 26, "|     %d",  e_thread->progress);
		mvprintw(tc+lnstart, statusx ,"|     [");
		switch(e_thread->status){
			case STATUS_START:
				attron(COLOR_PAIR(2));
				printw(" START ");
				attroff(COLOR_PAIR(2));
				break;
			case STATUS_RUN:
				attron(COLOR_PAIR(1));
				printw(" RUN ");
				attroff(COLOR_PAIR(1));
				break;
			case STATUS_WAIT:
				attron(COLOR_PAIR(3));
				printw(" WAIT ");
				attroff(COLOR_PAIR(3));
				break;
			case STATUS_TERM:

				printw(" TERM ");

				break;
		}
		printw("]");
		refresh();
	}
}

void set_active_thread(int id){
	int i=0;
	for(; i<disp_threads; ++i){
		if( exp_threads[i].status == STATUS_RUN){
			exp_threads[i].status = STATUS_WAIT;
		}
	exp_threads[id].status = STATUS_RUN;
	}
}

/* End display test code */
//int ccsm_fd;

pthread_mutex_t thread_count_lock = PTHREAD_MUTEX_INITIALIZER;	/* Mutex protecting our condition variable */
pthread_cond_t thread_count_control;				/* Our condition variable */
static int thread_count = 0;					/* Critical section data */

static pthread_t *threads;	/* Thread references */
static int *tidlist;		/* Thread tids */
static int signals_to_be_sent;	/* Signals to send through pipeline */
static int static_signal_count; /* Signals to send through pipeline (MUST not be modified) */
static int pipeline_len;	/* Number of stages (threads) in pipeline */

static int stop = 0;
static void sigint_handler(int i)
{
	stop = 1;
}

#define help_string "\
\n\nusage %s --threads=<int> --stimuli=<int> [--without-rt] [--help]\n\n\
\t--stimuli=\tnumber of stimuli to send through pipeline\n\
\t--threads=\tnumber of threads in pipeline\n\
\t--help\t\tthis menu\n\n"

void display_help(char **argv)
{
	printf(help_string, argv[0]);
}


/* This subroutine processes the command line options */
void process_options (int argc, char *argv[])
{
	int error = 0;

	for (;;) {
		int option_index = 0;

		static struct option long_options[] = {
			{"threads",          required_argument, NULL, 't'},
			{"stimuli",          required_argument, NULL, 's'},
			{"help",             no_argument,       NULL, 'h'},
			{NULL, 0, NULL, 0}
		};

		/*
		 * c contains the 4th element in the lists above corresponding to
		 * the long argument the user used.
		 */
		int c = getopt_long(argc, argv, "int:c:", long_options, &option_index);

		if (c == -1)
			break;
		switch (c) {
		case 0:
			switch (option_index) {
			case 0:
				display_help(argv);
				exit(0);
				break;
			}
			break;

		case 's':
			signals_to_be_sent = atoi(optarg);
			static_signal_count = signals_to_be_sent;
			break;

		case 't':
			pipeline_len = atoi(optarg);
			break;

		case 'h':
			error = 1;
			break;
		}
	}

	if (signals_to_be_sent <= 0) {
		printf("\nError: signals to be sent must be > 0");
		error = 1;
	}

	if (pipeline_len <= 0) {
		printf("\nError: pipeline length must be > 0");
		error = 1;
	}

	if (error) {
		display_help(argv);
		exit(1);
	}
}

static void *thread_code (void *arg)
{
	int id = (int)arg, numsigs, sigcnt=0, end_sig_count=0;

	/* Record the start of execution of this thread */
	DSTRM_EVENT(THREAD_TEST, THREAD_START, id);

	sigset_t newset;
	pthread_t *next_thread;

	/* Save this threads pid */
	tidlist[id] = gettid();

	/* Set a link to the next thread */
	next_thread = (id == (pipeline_len - 1)) ? NULL : &threads[id+1];

	/*
	 * We grab the condition variable lock, and then
	 * increment the counter. If we are the last thread,
	 * i.e. we increment the counter to match the user input,
	 * we signal the other threads. Otherwise, we block
	 * and wait for the signal.
	 */
	pthread_mutex_lock(&thread_count_lock);
	thread_count++;
	while (thread_count < pipeline_len) {
		pthread_cond_wait(&thread_count_control, &thread_count_lock);
	}
	pthread_cond_signal(&thread_count_control);
	pthread_mutex_unlock(&thread_count_lock);

	/* Until we receive the kill signal... */
	for (;;) {
		sigemptyset(&newset);
		sigaddset(&newset, SIGUSR1);
		sigaddset(&newset, SIGUSR2);
		sigwait (&newset, &numsigs);

		/* If signal SIGUSR1 is recieved, kill the thread */
		if (numsigs == SIGUSR2) break;

		/* If any other signal received, ignore, but notify user */
		if (numsigs != SIGUSR1) printf("Bad Signal: %d\n", numsigs);

		sigcnt++;

		/*
		 * Generate a unique event tag based on thread ID
		 * and signal sequence number. Note that we are using
		 * the (thread ID + 1) as the unique value for this thread
		 * in the tag value. The ID value is used as the index
		 * into the tid[] array which keeps tracks of only the
		 * child thread. However, we also need the parent thread
		 * to have an ID since it generates each signal representing
		 * messages moving through the pipeline. Since we want the
		 * parent thread to have location value 0, we use the index
		 * + 1 for each of the threads.
		 *
		 * In this case, the tag value for each event must encode both
		 * the pipeline stage location value and the signal sequence
		 * number. We chose the convention of using the top five bits
		 * of the tag value for the pipeline stage location and the
		 * bottom 27 bits for the message sequence number.
		 */
		unsigned int unique_id = id+1;
		unique_id <<= 27;
		unique_id |= sigcnt;

		/* Generate a signal recieved event */
		DSTRM_EVENT(GAP_TEST, SIG_RCVD, unique_id);

		/*
		 * Every 1000 signals we print a message to the user,
		 * so that they know progress is being made
		 */
		if (sigcnt % (disp_threads+1) == 0){
			/* printf("T-%d thread [%d] received %d signals\n",
					id, tidlist[id], sigcnt);
			*/
			exp_threads[id].progress = sigcnt;
			set_active_thread(id);
			refresh_tables();

			float dummy = 2.7;
			int i;
			for(i = 0; i < WORK_LOOPS; i++){
			  dummy *= dummy;
			}

		}
		if (!next_thread) {

			/*
			 * Record he exiting of signal from the
			 * pipeline. The signal has not actually
			 * exited to some other thread, but as
			 * this is the end of the pipeline, this
			 * is the last place the signal will be
			 * received.
			 */
			DSTRM_EVENT(PIPE_TEST, PIPE_END, sigcnt);

			end_sig_count++;

			/* Another signal has reached the end */
			signals_to_be_sent--;

			continue;
		}

		/* Generate a signal sent event */
		DSTRM_EVENT(GAP_TEST, SIG_SENT, unique_id);

		pthread_kill(*next_thread, SIGUSR1);
	}

	/* Pass on the kill signal to the next thread in the pipeline */
	if (next_thread) pthread_kill(*next_thread, SIGUSR2);

	/* Record the end of exection of this thread */
	DSTRM_EVENT(THREAD_TEST, THREAD_END, id);

	return NULL;
}

int main(int argc, char **argv)
{
	int i;
	sigset_t newset;

	/* Open DSUI */
	DSUI_BEGIN(&argc, &argv);

	/* Record the start of main() */
	DSTRM_EVENT(FUNC_MAIN, IN_MAIN_FUNC, 0);

	/* Process incoming arguments to setup experiment */
	process_options(argc, argv);
	init_experiment_display();
	/* Open communications with the CCSM device */
	/*ccsm_fd = ccsm_open();
	if (ccsm_fd < 0) {
		perror("ccsm_fd");
		return 1;
	}

//	ccsm_create_set(ccsm_fd, "sigpipe", 0);
	ccsm_create_component_self(ccsm_fd, "sigpipe-main-thread");
	ccsm_add_member(ccsm_fd, "sigpipe", "sigpipe-main-thread");
*/
	/*
	 * Set up signal masking. We do this to prevent
	 * any random system signals from interrupting
	 * our experiment
	 */
	sigemptyset(&newset);
	sigaddset(&newset, SIGUSR1);
	sigaddset(&newset, SIGUSR2);
	sigprocmask (SIG_BLOCK, &newset, NULL);

	signal(SIGINT, sigint_handler);
	signal(SIGTERM, sigint_handler);


	/* Allocate memory to hold references to pthreads */
	threads = malloc(sizeof(pthread_t) * pipeline_len);
	if (!threads) {
		perror("pthread malloc");
		exit(1);
	}

	/* Allocate memory to hold TIDs for pthreads */
	tidlist = malloc(sizeof(int) * pipeline_len);
	if (!tidlist) {
		perror("tidlist malloc");
		exit(1);
	}

	/* Create the threads using the thread code declared above */
	for (i = 0; i < pipeline_len; i++) {
		if (pthread_create (&threads[i], NULL, thread_code, (void *) i)) {
			fprintf(stderr, "Failed on pthread_create. %d\n", errno);
			exit(1);
		}
		add_thread("Testing");
		refresh_tables();
	}

	//printf("Created pipeline of %d threads\n", pipeline_len);

	/*
	 * We use a condition variable to prevent the main thread from
	 * sending signals until the remaining threads are finished
	 * setting up.
	 */
	pthread_mutex_lock(&thread_count_lock);
	while (thread_count < pipeline_len) {
		pthread_cond_wait(&thread_count_control, &thread_count_lock);
	}
	pthread_mutex_unlock(&thread_count_lock);

	//printf("All threads started\n");

	/* While there are still signals to be sent... */
	if (signals_to_be_sent) {
		int sigs = 0, i = 0, start_sig_count = 0, prev = signals_to_be_sent;

		//printf("Sending first signal to thread-%d\n", tidlist[0]);
		do {

			/*
			 * Mark when a signal is first sent. Note that
			 * we mark this point twice, with two different
			 * events. Each event supports a different set
			 * of information we are gathering
			 */
			unsigned int pipeline_stage = 0;
			pipeline_stage <<= 27;
			pipeline_stage |= sigs + 1;
			DSTRM_EVENT(GAP_TEST, SIG_SENT, pipeline_stage);

			DSTRM_EVENT(PIPE_TEST, PIPE_START, sigs + 1);

			/* Send the signal to the first thread in the pipeline */

			pthread_kill(threads[0], SIGUSR1);
			start_sig_count++;
			sigs++;

			/*
			 * Yield the scheduler until the signal reaches the end
			 * of the pipeline
			 */
			while (prev == signals_to_be_sent)
				sched_yield();
			prev = signals_to_be_sent;

		} while (signals_to_be_sent);

		//printf("Received all signals from last thread in pipeline\n");

		/* Record tid of each thread that was used... */
		for (i = 0; i < pipeline_len; i++){
			DSTRM_EVENT(THREAD, THREAD_ID, tidlist[i]);
		}
		/* ...including the main thread! */
		DSTRM_EVENT(THREAD, THREAD_ID, gettid());
	}

	/* Send a kill signal which terminates each pipeline stage */
	pthread_kill(threads[0], SIGUSR2);

	/* Wait for each thread to terminate. */
	for (i = 0; i < pipeline_len; i++)
		pthread_join (threads[i], NULL);

	//ccsm_close(ccsm_fd);
	close_display();
	/* Record the end of main() */
	DSTRM_EVENT(FUNC_MAIN, IN_MAIN_FUNC, 0);

	/* Exit DSUI */
	DSUI_CLEANUP();


	return 0;
}
