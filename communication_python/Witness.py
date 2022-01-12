from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.secretutil import SecretUtil
#from charm.toolbox.ABEnc import Input, Output
from secretshare import SecretShare
from charm.core.engine.util import bytesToObject, serializeDict,objectToBytes
import random
from datetime import datetime
from openpyxl import load_workbook
from openpyxl import Workbook
from PoK import PoK
from TSPS import TSPS
from BLS import BLS01
from secretshare import SecretShare as SSS
import zmq


class Witness():
    def __init__(self, groupObj):
        global util, group
        util = SecretUtil(groupObj)
        group = groupObj
        self.TSPS = TSPS(groupObj)
        self.BLS01 = BLS01(groupObj)
        
        

    def WitnessApproval(self):
        sigma={}
        context = zmq.Context()
        socket_verify = context.socket(zmq.REP)
        socket_verify.bind("tcp://*:5535") 
        
        received_guarantee = socket_verify.recv()
        received_guarantee = bytesToObject(received_guarantee,group)
        mpk = received_guarantee[0]
        pk = received_guarantee[1]
        R = received_guarantee[2]
        wprime_j = received_guarantee[3]
        witnessindexes = received_guarantee[4]
        N_j = received_guarantee[5]
        Sk_b = received_guarantee[6]
        Ledger = received_guarantee[7]
        for i in witnessindexes:
            if R not in Ledger[str(i)] and \
                TSPS.verify(self.TSPS,mpk,pk,N_j[str(i)],wprime_j[str(i)])==1:
                sigma[i] = BLS01.sign(self.BLS01,Sk_b[str(i)], R)
                Ledger[str(i)].append(R)
        sigma = objectToBytes(sigma,group)
        socket_verify.send(sigma)
        socket_verify.close()

    def main():
        groupObj = PairingGroup('BN254')
        w = Witness(groupObj)
        w.WitnessApproval()

if __name__ == "__main__":
    Witness.main()
