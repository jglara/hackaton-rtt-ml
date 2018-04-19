#!/usr/bin/perl -w
use Getopt::Long qw(GetOptions);


my $dport=0;

GetOptions('dport=s' => \$dport) or die "Usage: $0 --dport PORT\n";

my $i=0;
my $read_next=0;

while (<>) {
    my ($rtt,$rto,$cwnd,$ssthresh,$unacked, $retrans) = (0,0,0,0,0,0);

    if ($read_next == 1) {
#	print "$_";
	$read_next=0;
	if (/rtt:(.*?)\/(\d*)/) {
	    $rtt=$1;
	}
	
	if (/rto:(\d*)/) {
	    $rto=$1;
	}
	
	if (/cwnd:(\d*)/) {
	    $cwnd=$1;
	}
	
	if (/ssthresh:(\d*)/) {
	    $ssthresh=$1;
	}
	
	if (/unacked:(\d*)/) {
	    $unacked=$1;
	}

	if (/retrans:(\d*)\/(\d*)/) {
	    $retrans=$1;
	}

	
	print "$i $rtt $rto $cwnd $ssthresh $unacked $retrans\n";
	$i=$i+1;
    }

    if (/^ESTAB.*(.*):(\d+) /) {
#	print "$2\n";
	if ($dport != 0) {
	    if ($2 eq $dport) {
		$read_next=1;
	    }
	}

    }
    

}
