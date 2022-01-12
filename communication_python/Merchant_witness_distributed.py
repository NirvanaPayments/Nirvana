from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.secretutil import SecretUtil
from charm.toolbox.ABEnc import Input, Output
from secretshare import SecretShare
from charm.core.engine.util import serializeDict,objectToBytes, bytesToObject, deserializeDict
import random
import time
import zmq
from secretshare import SecretShare as SSS
from datetime import datetime
from BLS import BLS01
from openpyxl import load_workbook
from openpyxl import Workbook
from PoK import PoK
from TSPS import TSPS
from Witness import Witness
import math


class Merchant():
    def __init__(self):
        global groupObj
        groupObj = PairingGroup('BN254')
        self.PoK = PoK(groupObj)
        self.SSS = SecretShare(groupObj)
        self.context = zmq.Context()
        self.socket_receiveProof = self.context.socket(zmq.REQ)
        self.TSPS = TSPS(groupObj)
        self.BLS01 = BLS01(groupObj)
        self.witness = Witness(groupObj)

    #requesting public parameters from Nirvana
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

    #Requesting public key from Nirvana
    
    def MKeygen(self,mpk,M):
        Vk_b={};Sk_b={}
        for i in range(M):
            (vk_b,sk_b)=BLS01.keygen(self.BLS01, mpk['g'])
            Vk_b[i]=vk_b; Sk_b[i]=sk_b    
        return (Vk_b,Sk_b)

    def request_pk(self,merchant_index,vk_b):
        vk_merchant = vk_b[merchant_index]
        vk_merchant = objectToBytes(vk_merchant,groupObj)
        self.context = zmq.Context()
        print("Connecting to NirvanaTTP, requesting public key...")
        socket = self.context.socket(zmq.REQ)
        socket.connect("tcp://localhost:5547")
        print(f"Sending request for public key ...")
        socket.send(vk_merchant)

        message_pk = socket.recv()
        merchant_public_key = bytesToObject(message_pk, groupObj)
        pk_merchant = merchant_public_key[0]
        cert_merchant = merchant_public_key[1]
        new_mpk = merchant_public_key[2]
        print(f"Received public key [ {pk_merchant} ]")
        socket.close()
        return pk_merchant, cert_merchant, new_mpk
    
    
    

    #Requesting payment guarantee from Customer
    def request_proof(self, merchant_public_key,new_mpk):
        print("Connecting to customer, requesting proofs and ciphertext...")
        # socket_receiveProof = self.context.socket(zmq.REQ)
        # #socket_receiveProof.connect("tcp://81.164.204.249:5550")
        self.socket_receiveProof.connect("tcp://localhost:5540")
        proof_request_cust = (merchant_public_key,new_mpk)
        merchant_public_key = objectToBytes(proof_request_cust, groupObj)
        self.socket_receiveProof.send(merchant_public_key)
        #time.sleep(0.2)
        received_proof =  self.socket_receiveProof.recv()
        print("Received payment guarantee from customer..")
        received_proof = bytesToObject(received_proof, groupObj)
        return received_proof
        
    #Verifying payment guarantee from customer and appending payment ciphertext to the ledger
    def Verification(self, mpk, Pk_a, N, pi ,inp, R, time,L1,L2,pk,wprime_j,witnessindexes,N_j,Sk_w,socket_witness,Ledger):
        if TSPS.verify(self.TSPS, mpk, Pk_a, N, inp['cert'])==1 and \
                mpk['e_gh'] * (R ** (-time))==pi['pi2']['y'] and \
                    L1 * (inp['C']**(-time)) == pi['pi4']['y'] and \
                    L2 * (inp['C1'] ** (-time)) == pi['pi3']['y'] and \
                        PoK.verifier3(self.PoK,mpk['g'],pi['pi1']['y'],pi['pi1']['z'],pi['pi1']['t'],mpk['pp']) == 0 and \
                        PoK.verifier5(self.PoK,pi['pi2']['y'],pi['pi2']['z'],pi['pi2']['t'],R) == 1 and \
                            PoK.verifier4(self.PoK,pi['pi3']['y'],pi['pi3']['z'],pi['pi3']['t'],inp['C1'],pk) == 1 and \
                                PoK.verifier2(self.PoK,inp['C'],mpk['e_gh'],pi['pi4']['y'],pi['pi4']['z1'],pi['pi4']['z2'],pi['pi4']['t'],inp['u'])==1:
                                        for_witness = (mpk,Pk_a,R,wprime_j,witnessindexes,N_j,Sk_w,Ledger)
                                        for_witness = objectToBytes(for_witness,groupObj)
                                        socket_witness.send(for_witness)
                                        from_witness = socket_witness.recv()
                                        from_witness = bytesToObject(from_witness,groupObj)
                                        #sigma = Witness.WitnessApproval(self.witness,mpk, Pk_a, R, wprime_j, witnessindexes,N_j, Sk_b,Ledger)
                                        if len(from_witness)>= math.ceil(len(witnessindexes)/2):
                                            print("Verification succeeded")
                                            socket_witness.close()
        else:
            print("Verification failed")

    #revealing identity of customer in case of double-spending
    def Decryption(self, mpk, ct1, M1, ct2, M2): 
        Coeff = SSS.recoverCoefficients([groupObj.init(ZR, M1+1),groupObj.init(ZR, M2+1)])
        return ct2['C'] / ((ct1['C1']**Coeff[M1+1])*(ct2['C1']**Coeff[M2+1]))  




    def main():
        print("in Merchant's main")
        def start_bench(group):
            group.InitBenchmark()
            group.StartBenchmark(["RealTime"])

        def end_bench(group):
            group.EndBenchmark()
            benchmarks = group.GetGeneralBenchmarks()
            real_time = benchmarks['RealTime']
            return real_time
        m = Merchant()
        mpk,pk_a,num_mer = m.request_pp()

        #def run_round_trip(j):
        #main run'Spending Time','
        result=[num_mer]
            
        Mer = []
        for i in range(int(num_mer)):
            Mer.append('Apple'+str(i+1))
        (vk_b,sk_b) = m.MKeygen(mpk,int(num_mer))
        mer_pk, mer_cert, new_mpk = m.request_pk(5,vk_b)



        

        #start_bench(groupObj)
        spend_time = 0
        Verification_time = 0
        start_bench(groupObj)
        spend_proof,N, list_witness_index, N_j,time = m.request_proof(mer_pk,new_mpk)
        spend_time = end_bench(groupObj)
        sk_w = {}
        Ledger=dict.fromkeys(list_witness_index, [])
        print(Ledger)
        #counter = 0
        for j in list_witness_index:
            sk_w[j] = sk_b[j]
            #counter += 1
        pi = spend_proof[0]
        inp = spend_proof[1]
        R = spend_proof[2]
        wprime_j = spend_proof[3]
        L1=pair(new_mpk['g'],new_mpk['pp']) 
        L2=pair(new_mpk['g'],mer_pk)
        Verification_time=0
        
        context = zmq.Context()
        socket_witness = context.socket(zmq.REQ)
        socket_witness.connect("tcp://localhost:5535")
        start_bench(groupObj)
        out = m.Verification(new_mpk, pk_a,N, pi, inp, R, time, L1, L2, mer_pk,wprime_j, list_witness_index, N_j, sk_w,socket_witness,Ledger)
        Verification_time = end_bench(groupObj)
        result.append(spend_time)
        result.append(Verification_time)
        result.append(len(wprime_j))
        #verify_time += end_bench(groupObj)
        #spend_time = (spend_time*100)
        #result.append(spend_time)
        #verify_time = (verify_time*100)
        #result.append(verify_time) 
        book=Workbook()
        data=book.active    
        title = ['total_merchants','Spending time','Verification time', 'total_witnesses']
        data.append(title)   
        data.append(result)
        book.save('Verify_comm'+str(num_mer)+'.xlsx')

if __name__ == "__main__":
    Merchant.main()
   

