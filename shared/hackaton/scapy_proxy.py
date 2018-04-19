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

# All packets that should be filtered :

# If you want to use it as a reverse proxy for your machine
#iptablesr = "iptables -A OUTPUT -j NFQUEUE"

# If you want to use it for MITM :
iptablesr = "iptables -A FORWARD -j NFQUEUE"

print("Adding iptable rules :")
print(iptablesr)
os.system(iptablesr)

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

    def estimate(self, sampleRTT):
        if (self.estimatedRTT == 0):
            self.estimatedRTT = sampleRTT
        else:
            self.estimatedRTT = (1 - self.alfa) * self.estimatedRTT + self.alfa * sampleRTT

        return (self.estimatedRTT)

class TCPHalf:
    def __init__(self,key):
        global Args

        self.key = key
        self.expected_seq = 0
        self.ts = 0
        self.rtt_estimator = RTTEstimator(0.5)
        self.rtt_mean_error = 0
        self.csvfile = open("{0}/{1}.csv".format(Args.dir, self.key), "wb")
        self.csv = csv.writer(self.csvfile, delimiter=',')

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
            self.csvfile.close()

        if (self.expected_seq != 0) and (tcp.ack >= self.expected_seq):
            rtt = time.time() - self.ts
            estimated_rtt = self.rtt_estimator.estimatedRTT
#            rtt_error = abs(estimated_rtt - rtt)
#            self.csv.writerow([rtt, estimated_rtt, rtt_error])
#            print("{0}: RTT = {1}. Estimated RTT = {2}, Error = {3}\n".format(self.key, rtt, estimated_rtt, rtt_error))
#            self.csv.writerow([rtt, estimated_rtt])

            self.expected_seq = 0
            self.ts = 0
            self.rtt_estimator.estimate(rtt)



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

        if not keyLocal in Flows:
            Flows[keyLocal] = TCPHalf(keyLocal)

        if not keyRemote in Flows:
            Flows[keyRemote] = TCPHalf(keyRemote)

        if (len(tcp.payload)):
            Flows[keyLocal].send_seq(ip, tcp)

        Flows[keyRemote].recv_ack(ip, tcp)

    payload.set_verdict(nfqueue.NF_ACCEPT)
    return 1

def main():
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

    Args = parser.parse_args()

    main()
