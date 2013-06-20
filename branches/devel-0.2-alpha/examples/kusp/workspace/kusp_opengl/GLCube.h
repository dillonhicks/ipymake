#include <stdio.h>
#include <GL/glx.h>
#include <GL/gl.h>
#include <GL/glu.h>
#include <X11/extensions/xf86vmode.h>
#include <X11/keysym.h>

typedef struct {

  float x;
  float y;
  float z;
  float side_length;
  

} GLCube;


int init_cube(GLCube *cube, float x, float y, 
	      float z, float side_length);

void draw_cube(GLCube *cube);
