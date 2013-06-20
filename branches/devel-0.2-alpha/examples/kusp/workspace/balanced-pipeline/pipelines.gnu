set terminal png transparent nocrop enhanced font arial 8 size	420,320
set output "pipelines.png"
set xlabel "Time"
set ylabel "Frames Processed"
plot [0:553588][0:2500] \
"pipeline-1.gnuplot.dat" title "pipe-1" with steps,\
"pipeline-2.gnuplot.dat" title "pipe-2" with steps
