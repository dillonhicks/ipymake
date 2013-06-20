#include <GL/glx.h>
#include <GL/gl.h>
#include <GL/glu.h>
#include <X11/extensions/xf86vmode.h>
#include <X11/keysym.h>

/* stuff about our window grouped together */
typedef struct {
	/* handle to the display */
    Display *dpy;
    /* Screen number, ie for multiple monitors */
    int screen;

	/* The GLX window we are encapsulating
	 * into a more accessable GLWindow struct.
	 */
    Window win;
    GLXContext ctx;
    XSetWindowAttributes attr;

    /* Full Screen flag */
    Bool fs;
    /* Double buffered graphics are slower,
     * but cut down on tearing.
     */
    Bool doubleBuffered;

    XF86VidModeModeInfo deskMode;

    /* x and y coords of the window */
    int x, y;
    /* The width and hieght  of the window. */
    unsigned int width, height;
    /* The color depth. */
    unsigned int depth;

    void (*drawing_callback)(void);
} GLWindow;


/* attributes for a single buffered visual in RGBA format with at least
 * 4 bits per color and a 16 bit depth buffer */
static int attrListSgl[] = {GLX_RGBA, GLX_RED_SIZE, 4,
    GLX_GREEN_SIZE, 4,
    GLX_BLUE_SIZE, 4,
    GLX_DEPTH_SIZE, 16,
    None};

/* attributes for a double buffered visual in RGBA format with at least
 * 4 bits per color and a 16 bit depth buffer */
static int attrListDbl[] = { GLX_RGBA, GLX_DOUBLEBUFFER,
    GLX_RED_SIZE, 4,
    GLX_GREEN_SIZE, 4,
    GLX_BLUE_SIZE, 4,
    GLX_DEPTH_SIZE, 16,
    None };




/* function called when our window is resized (should only happen in window mode) */
extern void resizeGLScene(unsigned int width, unsigned int height);

/* general OpenGL initialization function */
extern int initGL(GLWindow *Win);

/* Here goes our drawing code */
extern int drawGLScene(GLWindow *GLWin);


/* function to release/destroy our resources and restoring the old desktop */
extern GLvoid killGLWindow(GLWindow *GLWin);

/* this function creates our window and sets it up properly */
/* FIXME: bits is currently unused */
extern Bool createGLWindow(GLWindow *GLWin, char* title, int width, int height, int bits,
                    Bool fullscreenflag);
