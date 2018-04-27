#!/usr/bin/python2

"""
    Use scapy to modify packets going through your machine.
    Based on nfqueue to block packets in the kernel and pass them to scapy for validation
"""

import nfqueue
from scapy.all import *
import os
import argparse
import time
import csv
from RTTMLEstimator import *

# All packets that should be filtered :

# If you want to use it as a reverse proxy for your machine
#iptablesr = "iptables -A OUTPUT -j NFQUEUE"



# If you want to use it for MITM attacks, set ip_forward=1 :
#print("Set ipv4 forward settings : ")
#os.system("sysctl net.ipv4.ip_forward=1")





class RTTEstimator:
    def __init__(self, alfa):
        self.alfa = alfa
        self.__estimatedRTT = 0

    @property
    def estimatedRTT(self):
        return self.__estimatedRTT

    def update(self, sampleRTT):
        if (self.estimatedRTT == 0):
            self.estimatedRTT = sampleRTT
        else:
            self.estimatedRTT = (1 - self.alfa) * self.estimatedRTT + self.alfa * sampleRTT

        return (self.estimatedRTT)

class TCPHalf:
    def __init__(self,key, estimator):
        global Args

        self.key = key
        self.expected_seq = 0
        self.ts = 0
        self.rtt_estimator = estimator
        self.rtts = []

    @staticmethod
    def createKeyLocal(ip,tcp):
        return ":".join([ip.src, str(tcp.sport), ip.dst, str(tcp.dport)])

    @staticmethod
    def createKeyRemote(ip, tcp):
        return ":".join([ip.dst, str(tcp.dport), ip.src, str(tcp.sport)])

    ## Local send payload, accept ack
    def send_seq(self, ip, tcp):
#        print("seq={0} ip.len={1} tcp.ofs={2} tcp.len={3} payload.len={4}\n".format(tcp.seq, ip.len, tcp.dataofs, tcp.dataofs << 2, len(tcp.payload)))
        if self.expected_seq == 0:
            self.expected_seq = tcp.seq + len(tcp.payload)
            self.ts = time.time()

    def recv_ack(self, ip, tcp):
#        print("ack={0} \n".format(tcp.ack))

        if tcp.flags & 0x01: # FIN
            if len(self.rtts) > 3:
                csvfile = open("{0}/{1}.csv".format(Args.dir, self.key), "wb")
                csv_writer = csv.writer(csvfile, delimiter=',')
                for l in self.rtts:
                    csv_writer.writerow(l)
                csvfile.close()

        if (self.expected_seq != 0) and (tcp.ack >= self.expected_seq):
            rtt = time.time() - self.ts
            estimated_rtt = self.rtt_estimator.estimatedRTT
            self.rtts.append([rtt, estimated_rtt])

            self.expected_seq = 0
            self.ts = 0
            self.rtt_estimator.update(rtt)



Flows={}


def callback(i,payload):
    global Flows
    # Here is where the magic happens.
    data = payload.get_data()
    ip = IP(data)

    if TCP in ip:
        tcp = ip[TCP]
        keyLocal = TCPHalf.createKeyLocal(ip,tcp)
        keyRemote = TCPHalf.createKeyRemote(ip,tcp)

        estimator = RTTEstimator(Args.alpha) if Args.estimator == "AVG" else RTTMLEstimator(rttmin=float(Args.rtt_min)/1000,
                                                                                            rttmax=float(Args.rtt_max)/1000,
                                                                                            numExperts=Args.experts,
                                                                                            learningRate=Args.learning_rate,
                                                                                            shareRate=Args.share_rate)

        if not keyLocal in Flows:
            Flows[keyLocal] = TCPHalf(keyLocal, estimator)

        if not keyRemote in Flows:
            Flows[keyRemote] = TCPHalf(keyRemote, estimator)

        if (len(tcp.payload)):
            Flows[keyLocal].send_seq(ip, tcp)

        Flows[keyRemote].recv_ack(ip, tcp)

    payload.set_verdict(nfqueue.NF_ACCEPT)
    return 1

def main():
    # If you want to use it for MITM :
    iptablesr = "iptables -A FORWARD -j NFQUEUE"

    print("Adding iptable rules :")
    print(iptablesr)
    os.system(iptablesr)


    # This is the intercept
    q = nfqueue.queue()
    q.open()
    q.bind(socket.AF_INET)
    q.set_callback(callback)
    q.create_queue(0)
    try:
        while 1:
            q.try_run() # Main loop
    except KeyboardInterrupt:
        q.unbind(socket.AF_INET)
        q.close()
        print("Flushing iptables.")
        # This flushes everything, you might wanna be careful
        os.system('iptables -F')
        os.system('iptables -X')
    except Exception as e:
        print("An error ocurred"+e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hackaton RTT-ML")

    parser.add_argument('--dir', '-d',
                        help="Directory to store outputs",
                        default="results")

    parser.add_argument('--estimator', '-e',
                        help="Estimator",
                        default="ML")

    parser.add_argument('--alpha', '-a',
                        help="Alpha parameter for RTT estimator",
                        type=float,
                        default=0.2)

    parser.add_argument('--rtt_min', '-m',
                        help="Alpha rtt min for RTT estimator",
                        type=int,
                        default=2)

    parser.add_argument('--rtt_max', '-x',
                        help="Alpha rtt max for RTT estimator",
                        type=int,
                        default=500)

    parser.add_argument('--experts', '-p',
                        help="num experts for RTT estimator",
                        type=int,
                        default=100)

    parser.add_argument('--learning_rate', '-r',
                        help="Learning rate",
                        type=float,
                        default=2)

    parser.add_argument('--share_rate', '-s',
                        help="Share rate",
                        type=float,
                        default=0.08)

    Args = parser.parse_args()

    main()
