#!/usr/bin/python

"""

"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI

from mininet.link import TCLink
from mininet.link import Link
from mininet.link import TCIntf
from mininet.node import CPULimitedHost
from mininet.nodelib import NAT

from subprocess import Popen, PIPE
import argparse
import os
from os.path import isfile, join
from time import sleep, time

class MyTCLink( Link ):
    "Link with symmetric TC interfaces configured via opts"
    def __init__( self, node1, node2, port1=None, port2=None,
                  intfName1=None, intfName2=None,
                  addr1=None, addr2=None, ip1=None, ip2=None, **params ):
        Link.__init__( self, node1, node2, port1=port1, port2=port2,
                       intfName1=intfName1, intfName2=intfName2,
                       cls1=TCIntf,
                       cls2=TCIntf,
                       addr1=addr1, addr2=addr2,
                       params1=params,
                       params2=params )
        if ip1 is not None:
            self.intf1.setIP(ip1)

        if ip2 is not None:
            self.intf2.setIP(ip2)



class MyForwardingRouter( Node ):
    "A Node with routing."

    def config( self, **params ):
        super( MyForwardingRouter, self).config( **params )
        self.cmd( 'echo $SHELL ; for d in $(ip li | awk \'BEGIN {FS=":"} /^[0-9]+:(.*):/ {print $2}\'  | grep -v lo | cut -d\'@\' -f 1);do ethtool -K $d tso off gso off tx off rx off; done')

        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1' )
        self.cmd('python /home/vagrant/shared/hackaton/scapy_proxy.py&')

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( MyForwardingRouter, self ).terminate()


class MyHost( Node ):
    "A Node simple"

    def config( self, **params ):
        super( MyHost, self).config( **params )
        self.cmd( 'echo $SHELL ; for d in $(ip li | awk \'BEGIN {FS=":"} /^[0-9]+:(.*):/ {print $2}\'  | grep -v lo | cut -d\'@\' -f 1);do ethtool -K $d tso off gso off tx off rx off; done')

#        self.cmd( 'echo $SHELL ; for d in $(ip li | awk \'BEGIN {{FS=":"}} /^[0-9]+:(.*):/ {{print $2}}\'  | grep -v lo | cut -d\'@\' -f 1);do tshark -i $d -w /tmp/{0}/$d.cap -F pcap & echo "tshark $d" ; done'.format(args.dir))


    def terminate( self ):
        super( MyHost, self ).terminate()
#        self.popen("pgrep -f tshark | xargs kill -9", shell=True).wait()


class MyNAT( NAT ):
    "A NAT node"

    def config( self, **params ):
        super( MyNAT, self).config( **params )
        self.cmd( 'echo $SHELL ; for d in $(ip li | awk \'BEGIN {FS=":"} /^[0-9]+:(.*):/ {print $2}\'  | grep -v lo | cut -d\'@\' -f 1);do ethtool -K $d tso off gso off tx off rx off; done')


    def terminate( self ):
        super( MyNAT, self ).terminate()
#        self.popen("pgrep -f tshark | xargs kill -9", shell=True).wait()


class MyServer( Node ):
    "A Server with Web Server & iperf server"

    def config( self, **params ):
        super( MyServer, self).config( **params )
        info("Starting server")
        self.cmd( 'echo $SHELL ; for d in $(ip li | awk \'BEGIN {FS=":"} /^[0-9]+:(.*):/ {print $2}\'  | grep -v lo | cut -d\'@\' -f 1);do ethtool -K $d tso off gso off tx off rx off; done' )
#        self.cmd( 'echo $SHELL ; for d in $(ip li | awk \'BEGIN {{FS=":"}} /^[0-9]+:(.*):/ {{print $2}}\'  | grep -v lo | cut -d\'@\' -f 1);do tshark -i $d -w /tmp/{0}/$d.cap -F pcap & echo "tshark $d" ; done'.format(args.dir))


#self.cmd('iperf3 -s -p 5001 &')
        self.cmd('nginx -c /home/vagrant/shared/hackaton/nginx_config/nginx.conf')
#        self.cmd('python http/webserver.py&')

####


#        self.cmd('watch -n0.1 "ss -itn >> {0}/ss-{1}.txt" &'.format(args.dir, self.IP()))
#        self.cmd('/home/mininet/git/tcpretrans/tcpretrans -s >> {0}/tcpretrans-{1}.txt &'.format(args.dir, self.IP()))
#        self.cmd('/home/mininet/git/tcpretrans/tcpretrans -s >> {0}/tcpretrans-{1}.txt &'.format(args.dir, self.IP()))

    def terminate( self ):
        self.cmd('nginx -s stop')
#        self.popen("pgrep -f tshark | xargs kill -9", shell=True).wait()
        super( MyServer, self ).terminate()



class NetworkTopo( Topo ):
    "A simple topology of a router with three subnets (one host in each)."

    def sysctl_set(self,key, value):
	"""Issue systcl for given param to given value and check for error."""

	p = Popen("sysctl -w %s=%s" % (key, value), shell=True, stdout=PIPE, stderr=PIPE)
	# Output should be empty; otherwise, we have an issue.	
	stdout, stderr = p.communicate()
	stdout_expected = "%s = %s\n" % (key, value)
	if stdout != stdout_expected:
		raise Exception("Popen returned unexpected stdout: %s != %s" % (stdout, stdout_expected))
	if stderr:
		raise Exception("Popen returned unexpected stderr: %s" % stderr)

    def setup_kernel_settings(self):
        self.sysctl_set('net.ipv4.tcp_no_metrics_save', 0) # Disable slow start threshold caching
        self.sysctl_set('net.ipv4.tcp_congestion_control', 'cubic') # Disable slow start threshold caching


    def build( self, **_opts ):

        s1 = self.addSwitch('sw1')
        s2 = self.addSwitch('sw2')
        s3 = self.addSwitch('sw3')
#        s4 = self.addSwitch('sw4')
        s5 = self.addSwitch('sw5')

        router1 = self.addNode( 'r1', cls=MyForwardingRouter, ip='192.168.1.20/24',
                               defaultRoute='via 192.168.5.51')

        router2 = self.addNode( 'r2', cls=MyForwardingRouter, ip='192.168.2.30/24',
                               defaultRoute='via 192.168.5.50')


        nat = self.addNode( 'nat0', cls=MyNAT, ip='192.168.5.50/24', subnet='192.168.0.0/16', inetIntf='eth1', localIntf='nat0-eth1', inNamespace=False)
        server1 = self.addNode( 's1', cls=MyServer, ip='192.168.5.51/24', subnet='192.168.0.0/16')

        # cpu=0.5,
        host = self.addHost( 'h1', ip='192.168.1.10/24', cls=MyHost, 
                           defaultRoute='via 192.168.1.20' )


        host2 = self.addHost( 'h2', ip='192.168.2.10/24', cls=MyHost, 
                           defaultRoute='via 192.168.2.30' )



        linkConfig = {'bw': 50, 'delay': '1ms', 'loss': 0, 'jitter': 0, 'max_queue_size': 1000 }
        linkConfig1 = {'bw': float(args.dsl_bw), 'delay': args.dsl_delay, 'loss': float(args.dsl_loss), 'jitter': args.dsl_jitter, 'max_queue_size': 1000 }
        linkConfig2 = {'bw': float(args.dsl_bw), 'delay': args.dsl_delay, 'loss': float(args.dsl_loss), 'jitter': args.dsl_jitter, 'max_queue_size': 1000 }
        linkConfig_server = {'bw': float(args.server_bw), 'delay': args.server_delay, 'loss': float(args.server_loss), 'jitter': args.server_jitter, 'max_queue_size': 1000 }

        # client connections
        self.addLink( s1, host, cls=MyTCLink, intfName2='h1-eth1', ip2='192.168.1.10/24', **linkConfig)
        self.addLink( s2, host2, cls=MyTCLink, intfName2='h2-eth1', ip2='192.168.2.10/24', **linkConfig)

        # router1 connections
        self.addLink( s1, router1, cls=MyTCLink, intfName2='r1-eth1', ip2='192.168.1.20/24', **linkConfig1)
        self.addLink( s3, router1, cls=MyTCLink, intfName2='r1-eth2', ip2='192.168.5.20/24', **linkConfig)

        # router2 connections
        self.addLink( s2, router2, cls=MyTCLink, intfName2='r2-eth1', ip2='192.168.2.30/24', **linkConfig2)
        self.addLink( s5, router2, cls=MyTCLink, intfName2='r2-eth2', ip2='192.168.5.30/24', **linkConfig)

        # NAT
        self.addLink( s5, nat, cls=MyTCLink, intfName2='nat0-eth1', ip2='192.168.5.50/24', **linkConfig_server)

        # S1
        self.addLink( s3, server1, cls=MyTCLink, intfName2='s1-eth1', ip2='192.168.5.51/24', **linkConfig_server)
    

def run():
    topo = NetworkTopo()
    net = Mininet( topo=topo )  

    topo.setup_kernel_settings()

    net.start()

    nat = net.getNodeByName('nat0')
    nat.cmdPrint('ip route add 192.168.2.0/24 via 192.168.5.30 dev nat0-eth1')

    s1 = net.getNodeByName('s1')
    s1.cmdPrint('ip route add 192.168.1.0/24 via 192.168.5.20 dev s1-eth1')

#    os.system('ovs-vsctl add-port sw6 eth1')
#    nat.cmdPrint('ifconfig nat0-eth0 0')
#    nat.cmdPrint('dhclient nat0-eth0')

    h1 = net.getNodeByName('h1')


    info( '*** Routing Table on Router\n' )
    #print net[ 'r1' ].cmd( 'route' )
    if args.cli:
        CLI( net )
    else:
        h1.cmd('sleep 1')


        if args.get:
            h1.cmd('sleep 1')
            for file in args.get:
                #h1.sendCmd('wget --delete-after {0}'.format(file))
                h1.sendCmd('aria2c -d output -x5  -k1M  http://{0}/http/{1}'.format(net.getNodeByName('s1').IP(), file, args.dir))
                #h1.sendCmd('mget --delete-after {0}'.format(file))
                print "waiting for the sender to finish"
                h1.waitOutput()
        sleep(1)

    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    parser = argparse.ArgumentParser(description="Hackaton RTT-ML")


    parser.add_argument('--server_loss',
                        help="packet loss percentage in the server side",
                        default=0)

    parser.add_argument('--server_jitter',
                        help="packet jitter in ms in the server side",
                        default=0)

    parser.add_argument('--server_bw',
                        help="bandwidth in mbps in the server side",
                        default=50)

    parser.add_argument('--server_delay',
                        help="delay in ms in the server side",
                        default='1ms')



    parser.add_argument('--dsl_bw',
                        help="bandwidth in mbps in the dsl side",
                        default=50)

    parser.add_argument('--dsl_delay',
                        help="delay in ms in the dsl side",
                        default='1ms')

    parser.add_argument('--dsl_loss', 
                        help="packet loss percentage in the dsl side",
                        default=0)

    parser.add_argument('--dsl_jitter', 
                        help="packet jitter in ms in the dsl side",
                        default=0)
     
    parser.add_argument('--dir', '-d',
                        help="Directory to store outputs",
                        default="results")
    
    parser.add_argument('--cli', '-c',
                        action='store_true',
                        help='Run CLI for topology debugging purposes')

    parser.add_argument('--get', nargs='*', help="HTTP get file")
    
    # Expt parameters
    args = parser.parse_args()


    #os.system("mkdir /tmp/{0} ; mkdir ./{0} ; rm /tmp/{0}/* ; rm ./{0}/*".format(args.dir))
    run()
    #os.system("mv /tmp/{0}/* ./{0} ; chmod o=rw ./{0}/*".format(args.dir))


        
