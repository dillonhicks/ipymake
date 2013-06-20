set terminal png transparent nocrop enhanced font arial 8 size 420,320 
set output 'steps.1.png'
set title "Compare steps, fsteps and histeps" 
plot [0:16][0:13] "steps.dat" notitle with points, "steps.dat" title 'steps' with steps
