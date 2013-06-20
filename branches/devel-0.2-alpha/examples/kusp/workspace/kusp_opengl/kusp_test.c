/*
 *
 */

#include <stdlib.h>
#include <stdio.h>
#include "kuspgl.h"
#include "GLCube.h"

GLCube *my_cube;

void my_draw(void){
    glBegin(GL_TRIANGLES);
        glVertex3f(0.0f, 1.0f, 0.0f);
        glVertex3f(-1.0f, -1.0f, 0.0f);
        glVertex3f(1.0f, -1.0f, 0.0f);
    glEnd();
    glTranslatef(3.0f, 0.0f, 0.0f);
    glBegin(GL_QUADS);
        glVertex3f(-1.0f, 1.0f, 0.0f);
        glVertex3f(1.0f, 1.0f, 0.0f);
        glVertex3f(1.0f, -1.0f, 0.0f);
        glVertex3f(-1.0f, -1.0f, 0.0f);
    glEnd();
    draw_cube(my_cube);
}

int main(int argc, char **argv)
{
    XEvent event;
    Bool done;
    Bool full_screen;
    GLWindow *GLWin;
    GLWin = (GLWindow*) malloc( sizeof(GLWindow) );
    my_cube = (GLCube*) malloc( sizeof(GLCube) );

    done = False;
    full_screen = False;

    createGLWindow(GLWin, "KUSP -- Experiment Visualization", 800, 600, 24, full_screen);
    init_cube(my_cube, 1.0f, 1.0f, 1.0f, 1.0f);
    GLWin->drawing_callback = &my_draw;

    /* wait for events*/
    while (!done)
    {
        /* handle the events in the queue */
        while (XPending(GLWin->dpy) > 0)
        {
            XNextEvent(GLWin->dpy, &event);
            switch (event.type)
            {
                case Expose:
	                if (event.xexpose.count != 0)
	                    break;
                    drawGLScene(GLWin);
         	        break;
	            case ConfigureNotify:
	            /* call resizeGLScene only if our window-size changed */
	                if ((event.xconfigure.width != GLWin->width) ||
	                    (event.xconfigure.height != GLWin->height))
	                {
	                    GLWin->width = event.xconfigure.width;
	                    GLWin->height = event.xconfigure.height;
                        printf("Resize event\n");
	                    resizeGLScene(event.xconfigure.width,
	                        event.xconfigure.height);
	                }
	                break;
                /* exit in case of a mouse button press */
                case ButtonPress:
                    done = True;
                    break;
                case KeyPress:
                    if (XLookupKeysym(&event.xkey, 0) == XK_Escape)
                    {
                        done = True;
                    }
                    if (XLookupKeysym(&event.xkey,0) == XK_F1)
                    {
                        killGLWindow(GLWin);
                        GLWin->fs = !GLWin->fs;
                        createGLWindow(GLWin, "NeHe's First Polygon Tutorial",
                            640, 480, 24, GLWin->fs);
                    }
                    break;
                case ClientMessage:
                    if (*XGetAtomName(GLWin->dpy, event.xclient.message_type) ==
                        *"WM_PROTOCOLS")
                    {
                        printf("Exiting sanely...\n");
                        done = True;
                    }
                    break;
                default:
                    break;
            }
        }
        drawGLScene(GLWin);
    }
    /* Kill Window does not free the
     * GLWin memory.
     */
    killGLWindow(GLWin);
    free(GLWin);
    free(my_cube);
    exit (0);
}
