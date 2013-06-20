#include <stdio.h>
#include <GL/glx.h>
#include <GL/gl.h>
#include <GL/glu.h>
#include <X11/extensions/xf86vmode.h>
#include <X11/keysym.h>
#include "kuspgl.h"



/* function called when our window is resized (should only happen in window mode) */
extern void resizeGLScene(unsigned int width, unsigned int height)
{
    if (height == 0)    /* Prevent A Divide By Zero If The Window Is Too Small */
        height = 1;
    glViewport(0, 0, width, height);    /* Reset The Current Viewport And Perspective Transformation */
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluPerspective(45.0f, (GLfloat)width / (GLfloat)height, 0.1f, 100.0f);
    glMatrixMode(GL_MODELVIEW);
}

/* general OpenGL initialization function */
extern int initGL(GLWindow *Win)
{
    glShadeModel(GL_SMOOTH);
    glClearColor(0.0f, 0.0f, 0.0f, 0.0f);
    glClearDepth(1.0f);
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LEQUAL);
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST);
    /* we use resizeGLScene once to set up our initial perspective */
    resizeGLScene(Win->width, Win->height);
    glFlush();
    return True;
}

/* Here goes our drawing code */
extern int drawGLScene(GLWindow *GLWin)
{
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glLoadIdentity();
    glTranslatef(-1.5f, 0.0f, -6.0f);
    GLWin->drawing_callback();
    glEnd();
    if (GLWin->doubleBuffered)
    {
        glXSwapBuffers(GLWin->dpy, GLWin->win);
    }
    return True;
}



/* function to release/destroy our resources and restoring the old desktop */
extern GLvoid killGLWindow(GLWindow *GLWin)
{
    if (GLWin->ctx)
    {
        if (!glXMakeCurrent(GLWin->dpy, None, NULL))
        {
            printf("Could not release drawing context.\n");
        }
        glXDestroyContext(GLWin->dpy, GLWin->ctx);
        GLWin->ctx = NULL;
    }
    /* switch back to original desktop resolution if we were in
     * full screen mode.
     */
    if (GLWin->fs)
    {
        XF86VidModeSwitchToMode(GLWin->dpy, GLWin->screen, &GLWin->deskMode);
        XF86VidModeSetViewPort(GLWin->dpy, GLWin->screen, 0, 0);
    }
    XCloseDisplay(GLWin->dpy);
}

/* this function creates our window and sets it up properly */
/* FIXME: bits is currently unused */
extern Bool createGLWindow(GLWindow *GLWin, char* title, int width, int height, int bits,
                    Bool fullscreenflag)
{
    XVisualInfo *vi;
    Colormap cmap;
    int dpyWidth, dpyHeight;
    int i;
    int glxMajorVersion, glxMinorVersion;
    int vidModeMajorVersion, vidModeMinorVersion;
    XF86VidModeModeInfo **modes;
    int modeNum;
    int bestMode;
    Atom wmDelete;
    Window winDummy;
    unsigned int borderDummy;

    GLWin->fs = fullscreenflag;
    /* set best mode to current */
    bestMode = 0;
    /* get a connection to the X server */
    GLWin->dpy = XOpenDisplay(0);
    GLWin->screen = DefaultScreen(GLWin->dpy);
    XF86VidModeQueryVersion(GLWin->dpy, &vidModeMajorVersion,
        &vidModeMinorVersion);
    printf("XF86VidModeExtension-Version %d.%d\n", vidModeMajorVersion,
        vidModeMinorVersion);
    XF86VidModeGetAllModeLines(GLWin->dpy, GLWin->screen, &modeNum, &modes);
    /* save desktop-resolution before switching modes */
    GLWin->deskMode = *modes[0];

    /* look for mode with requested resolution */
    for (i = 0; i < modeNum; i++)
    {
        if ((modes[i]->hdisplay == width) && (modes[i]->vdisplay == height))
        {
            bestMode = i;
        }
    }
    /* get an appropriate visual */
    vi = glXChooseVisual(GLWin->dpy, GLWin->screen, attrListDbl);
    if (vi == NULL)
    {
        vi = glXChooseVisual(GLWin->dpy, GLWin->screen, attrListSgl);
        GLWin->doubleBuffered = False;
        printf("Only Singlebuffered Visual!\n");
    }
    else
    {
        GLWin->doubleBuffered = True;
        printf("Got Doublebuffered Visual!\n");
    }
    glXQueryVersion(GLWin->dpy, &glxMajorVersion, &glxMinorVersion);
    printf("glX-Version %d.%d\n", glxMajorVersion, glxMinorVersion);
    /* create a GLX context */
    GLWin->ctx = glXCreateContext(GLWin->dpy, vi, 0, GL_TRUE);
    /* create a color map */
    cmap = XCreateColormap(GLWin->dpy, RootWindow(GLWin->dpy, vi->screen),
        vi->visual, AllocNone);
    GLWin->attr.colormap = cmap;
    GLWin->attr.border_pixel = 0;

	/* Set up for the full screen is drastically different from a normal window
	 * since it overtakes the whole desktop display.
	 */
    if (GLWin->fs)
    {
        XF86VidModeSwitchToMode(GLWin->dpy, GLWin->screen, modes[bestMode]);
        XF86VidModeSetViewPort(GLWin->dpy, GLWin->screen, 0, 0);
        dpyWidth = modes[bestMode]->hdisplay;
        dpyHeight = modes[bestMode]->vdisplay;
        printf("Resolution %dx%d\n", dpyWidth, dpyHeight);
        XFree(modes);

        /* create a fullscreen window */
        GLWin->attr.override_redirect = True;
        GLWin->attr.event_mask = ExposureMask | KeyPressMask | ButtonPressMask |
            StructureNotifyMask;
        GLWin->win = XCreateWindow(GLWin->dpy, RootWindow(GLWin->dpy, vi->screen),
            0, 0, dpyWidth, dpyHeight, 0, vi->depth, InputOutput, vi->visual,
            CWBorderPixel | CWColormap | CWEventMask | CWOverrideRedirect,
            &GLWin->attr);
        XWarpPointer(GLWin->dpy, None, GLWin->win, 0, 0, 0, 0, 0, 0);
		XMapRaised(GLWin->dpy, GLWin->win);
        XGrabKeyboard(GLWin->dpy, GLWin->win, True, GrabModeAsync,
            GrabModeAsync, CurrentTime);
        XGrabPointer(GLWin->dpy, GLWin->win, True, ButtonPressMask,
            GrabModeAsync, GrabModeAsync, GLWin->win, None, CurrentTime);
    }
    else
    {
        /* create a window in window mode*/
        GLWin->attr.event_mask = ExposureMask | KeyPressMask | ButtonPressMask |
            StructureNotifyMask;
        GLWin->win = XCreateWindow(GLWin->dpy, RootWindow(GLWin->dpy, vi->screen),
            0, 0, width, height, 0, vi->depth, InputOutput, vi->visual,
            CWBorderPixel | CWColormap | CWEventMask, &GLWin->attr);
        /* only set window title and handle wm_delete_events if in windowed mode */
        wmDelete = XInternAtom(GLWin->dpy, "WM_DELETE_WINDOW", True);
        XSetWMProtocols(GLWin->dpy, GLWin->win, &wmDelete, 1);
        XSetStandardProperties(GLWin->dpy, GLWin->win, title,
            title, None, NULL, 0, NULL);
        XMapRaised(GLWin->dpy, GLWin->win);
    }
    /* connect the glx-context to the window */
    glXMakeCurrent(GLWin->dpy, GLWin->win, GLWin->ctx);
    XGetGeometry(GLWin->dpy, GLWin->win, &winDummy, &GLWin->x, &GLWin->y,
        &GLWin->width, &GLWin->height, &borderDummy, &GLWin->depth);
    printf("Depth %d\n", GLWin->depth);

    if (glXIsDirect(GLWin->dpy, GLWin->ctx))
        printf("Congrats, you have Direct Rendering!\n");
    else
        printf("Sorry, no Direct Rendering possible!\n");
    initGL(GLWin);
    return True;
}
