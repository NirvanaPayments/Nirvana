from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.secretutil import SecretUtil
from charm.toolbox.ABEnc import Input, Output
from secretshare import SecretShare
from charm.core.engine.util import serializeDict,objectToBytes, bytesToObject
import random
import time
import zmq
from datetime import datetime
from openpyxl import load_workbook
from openpyxl import Workbook
from PoK import PoK
from TSPS import TSPS
from BLS import BLS01
from secretshare import SecretShare as SSS
from Witness import Witness
import math


class Customer():

    def __init__(self):
        global Mer, groupObj
        groupObj = PairingGroup('BN254')
        self.PoK = PoK(groupObj)
        self.SSS = SecretShare(groupObj)
        self.TSPS = TSPS(groupObj)
        self.BLS01 = BLS01(groupObj)
        self.PoK = PoK(groupObj)
        self.witness = Witness(groupObj)
        

    #Requesting public parameters
    def request_pp(self):
        self.context = zmq.Context()
        print("Connecting to NirvanaTTP, requesting parameters...")
        socket_pull = self.context.socket(zmq.SUB)
        socket_pull.setsockopt(zmq.SUBSCRIBE, b"")
        socket_pull.connect("tcp://localhost:5546")
        msg = socket_pull.recv()
        mpk = bytesToObject(msg, groupObj)
        socket_pull.close()
        return mpk[0],mpk[1],mpk[2]

    def CuKeyGen(self,mpk):
        sk=groupObj.random(); 
        pk=mpk['g'] ** sk; 
        return (sk,pk)

    #requesting registration certificate from Nirvana
    def request_cert(self,pk):
        pk = objectToBytes(pk,groupObj)
        self.context = zmq.Context()
        print("Connecting to Nirvana authorities, requesting registration certificate...")
        socket = self.context.socket(zmq.REQ)
        socket.connect("tcp://localhost:5549")
        socket.send(pk)

        reg_certificate = socket.recv()
        reg_certificate = bytesToObject(reg_certificate, groupObj)
        socket.close()

        return reg_certificate

    #requesting collateral proof from Nirvana    
    def CuCreate(self, mpk,cert_cn):
        K={}; Kprime={}; Col={}
        K = groupObj.random()
        Kprime = mpk['g']**K
        N = mpk['h']**K
        pi=PoK.prover1(self.PoK,mpk['g'],Kprime,K)
        certprime = TSPS.Randomize(self.TSPS, cert_cn)
        #return (K, N, Kprime, certprime,pi)
        customer_Col_proof = (Kprime)
        self.context = zmq.Context()
        print("Connecting to NirvanaTTP, requesting collateral certification...")
        socket = self.context.socket(zmq.REQ)
        socket.connect("tcp://localhost:5545")   
        print(f"Sending certification request...")
        customer_Col_proof = objectToBytes(customer_Col_proof,groupObj)        
        socket.send(customer_Col_proof)
        message_colla = socket.recv()
        message_colla = bytesToObject(message_colla, groupObj)
        print(f"Received certified collateral [ {message_colla} ]")
        socket.close()
        
        return (message_colla,pi,certprime,N,K,Kprime)

    #Generating the payment guarantee for requesting merchant..
    def Spending(self, mpk, key, pk_bm, time,ID,Sk_cn,cert_j,w_j,listWitness):
        r = mpk['g'] ** (1/(key+time))
        R = pair(r,mpk['h'])
        A1 = (pair(r, mpk['pp']))
        C = ID * A1
        C1 = pair(r, pk_bm)
        wprime_j = {}
        for i in listWitness:
            wprime_j[i] = TSPS.Randomize(self.TSPS,w_j[str(i)])
        certprime_j = TSPS.Randomize(self.TSPS,cert_j)
        y2 = R ** key; A= A1 ** key
        u = mpk['e_gh'] ** (key * Sk_cn)
        (proof1) = PoK.prover3(self.PoK,mpk['g'],A,key,mpk['pp']) #Proof of SPS
        (proof2) = PoK.prover4(self.PoK,y2,key,R) # Proof of Aggeragetd collatorals
        (proof3) = PoK.prover3(self.PoK,r,C1**key,key,pk_bm) #Proof of ciphertext C1
        (proof4) = PoK.prover2(self.PoK,C,mpk['e_gh'],((C/ID)**key)*(mpk['e_gh']**(-time*Sk_cn)),key,(-time*Sk_cn)) #Proof of ciphertext C0
        inp = { 'C': C, 'C1': C1 , 'cert': certprime_j, 'u':u}
        pi = {'pi1': proof1,'pi2': proof2,'pi3': proof3,'pi4': proof4}
        return (pi, inp, R, wprime_j)
            
        #socket_receiveProofReq.close()


#main



    def main():
        print("in customer's main")
        def start_bench(group):
            group.InitBenchmark()
            group.StartBenchmark(["RealTime"])

        def end_bench(group):
            group.EndBenchmark()
            benchmarks = group.GetGeneralBenchmarks()
            real_time = benchmarks['RealTime']
            return real_time
        c = Customer()
        mpk,pk_a,num_mer = c.request_pp()
        (sk_c,pk_c) = c.CuKeyGen(mpk)
        (reg_certificate) = c.request_cert(pk_c)
        (certified_col,pi,certprime,N,key,kprime) = c.CuCreate(mpk,reg_certificate)
        context = zmq.Context()
        socket_receiveProofReq = context.socket(zmq.REP)
        socket_receiveProofReq.bind("tcp://*:5540")
        #def run_round_trip(j):
        result = [num_mer]
        Mer = []
        for i in range(int(num_mer)):
            Mer.append('Apple'+str(i+1))

        merchant_col_req = socket_receiveProofReq.recv()
        merchant_col_req = bytesToObject(merchant_col_req, groupObj)
        pk_merchant = merchant_col_req[0]
        new_mpk = merchant_col_req[1]
        print(f"Received proof request from merchant: {pk_merchant}")
        time=groupObj.hash(objectToBytes(str(datetime.now()), groupObj),ZR)
        ID = new_mpk['e_gh'] ** sk_c
        start_bench(groupObj)
        Spend_time=0
        spend_proof = c.Spending(new_mpk,key,pk_merchant,time,ID,sk_c,certified_col[0],certified_col[1],certified_col[2])
        Spend_time = end_bench(groupObj)
        message_to_mer = (spend_proof,N, certified_col[2], certified_col[3],time)
        spend_proof = objectToBytes(message_to_mer, groupObj)
        socket_receiveProofReq.send(spend_proof)
        print("Sent payment guarantee to merchant....")
        #PPSpending_time = (PPSpending_time*100)
        result.append(Spend_time)      
        #return result
        book=Workbook()
        data=book.active    
        title = ['total_merchants','Spending Time']
        data.append(title) 
        data.append(result)
        book.save('Spend_comm'+str(num_mer)+'.xlsx')

if __name__ == "__main__":
    Customer.main()


