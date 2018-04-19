#!/bin/bash -x


./filter_bw.pl --flow=1 sasn/dpi.logfile.log > /tmp/rtt.txt
./filter_bw.pl --flow=2 sasn/dpi.logfile.log > /tmp/rtt2.txt


# set data style linespoints                                                                                              
gnuplot -persist <<EOF

 show timestamp                                                                                                          
 set title "RTT"                                                                                                          
 set ylabel "pkts"                                                                                                      
 plot "/tmp/rtt.txt" using 1:4 title 'RTT #1' with lines, "/tmp/rtt2.txt" using 1:4 title 'RTT #2' with lines
EOF

