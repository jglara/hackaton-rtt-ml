#! /bin/bash -x


cat $1 | ~/git/MPTCP/filter_ss.pl > /tmp/ss.txt

gnuplot -persist <<EOF
 show timestamp
 set title "$1"
 set xlabel "time"
 set ylabel "packets (cwnd, ssthresh,unacked)"
 plot "/tmp/ss.txt" using 1:4 title "cwnd" with lines, "/tmp/ss.txt" using 1:5 title "ssthresh" with lines, "/tmp/ss.txt" using 1:6 title "unacked" with lines, "/tmp/ss.txt" using 1:7 title "retrans" with lines
EOF

gnuplot -persist <<EOF
 show timestamp
 set title "$1"
 set xlabel "time"
 set ylabel "time (ms)"
 plot "/tmp/ss.txt" using 1:2 title "rtt" with lines
EOF
