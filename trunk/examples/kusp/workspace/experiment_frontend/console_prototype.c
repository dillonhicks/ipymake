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
int thread_count = 0;

void init_win_params(WIN *p_win, int winy, int winx);
void print_win_params(WIN *p_win);
void create_box(WIN *win, bool flag);
void add_thread(char* t_name);
void refresh_tables();

int main(int argc, char **argv)
{	WIN win_threads;



	initscr();			/* Start curses mode 		*/
	cbreak();			/* Line buffering disabled, Pass on
					 * everty thing to me 		*/
	noecho();
	start_color();			/* Start color 			*/
	init_pair(1, COLOR_GREEN, COLOR_BLACK);
	init_pair(2, COLOR_BLUE, COLOR_BLACK);
	init_pair(3, COLOR_RED, COLOR_BLACK);
	int num_threads = 20;
	int thr = 0;
	for(; thr < num_threads; ++thr){
		add_thread("HELLOKITTY");
	}

	/* Initialize the window parameters */
	init_win_params(&win_threads, 0, 0);
	print_win_params(&win_threads);


	create_box(&win_threads, TRUE);
	mvprintw(1,1, "          THREADS        |        PROGRESS         |         STATUS      ");

	refresh();
	refresh_tables();
	endwin();

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
	e_thread = &exp_threads[thread_count];
	e_thread->name = thread_count;
	e_thread->progress = 0;
	e_thread->status = thread_count%4;
	thread_count += 1;
}

void refresh_tables(){
	int tc = 0;
	int lnstart = 3;
	int statusx = 52;
	EXP_THREAD* e_thread;
	for(; tc < thread_count; ++tc){
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
