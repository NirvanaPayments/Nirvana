import sys
from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.secretutil import SecretUtil
#from charm.toolbox.ABEnc import Input, Output
from secretshare import SecretShare
from charm.core.engine.util import bytesToObject, serializeDict,objectToBytes
import random
import time
import zmq
import json
from datetime import datetime
from openpyxl import load_workbook
from openpyxl import Workbook
from PoK import PoK
from TSPS import TSPS
from secretshare import SecretShare as SSS
from BLS import BLS01
from Witness import Witness
from Merchant import Merchant
from Customer_preprocessed import Customer
import math

context = zmq.Context()
socket_clientSig = context.socket(zmq.REP)
socket_clientSig.bind("tcp://*:5545") #customer connection
socket_merchant = context.socket(zmq.REP)
socket_merchant.bind("tcp://*:5547") #merchant connection
socket_clientReg = context.socket(zmq.REP)
socket_clientReg.bind("tcp://*:5549") #customer connection
socket_publish = context.socket(zmq.PUB)
socket_publish.bind("tcp://*:5546") #publishing mpk



class Nirvana():
    def __init__(self, groupObj):
        global util, group
        util = SecretUtil(groupObj)
        group = groupObj
        self.SecretShare = SecretShare(groupObj)
        self.TSPS = TSPS(groupObj)
        self.BLS01 = BLS01(groupObj)
        self.PoK = PoK(groupObj)
        self.witness = Witness(groupObj)
        
    
      
    def PGen(self):
        mpk = TSPS.PGen(self)
        return (mpk)

    
    def AuKeygen(self, mpk,k,n):
        (Sgk_a,Vk_a,Pk_a) = TSPS.kgen(self.TSPS,mpk,k,n)
        return (Sgk_a,Vk_a,Pk_a)

    
    def MRegister(self,mpk,sgk,vkm,M,k,merchant_index):
        s=group.random()
        mpk['pp'] = mpk['h']**s
        shares= SSS.genShares(self.SecretShare, s, 2, M)
        sigma1 = TSPS.par_sign1(self.TSPS, mpk,vkm,k)
        sigma = TSPS.par_sign2(self.TSPS, sigma1,sgk,k)
        sigmaR = TSPS.reconst(self.TSPS, sigma,k)
        cert_b=sigmaR
        Pk_b=mpk['h']**shares[merchant_index]
        reg_message = (Pk_b,cert_b,mpk)
        return reg_message


    def CuRegister(self, mpk,Sgk_a,Pk_c,C,k):
        sigma1=TSPS.par_sign1(self.TSPS, mpk,Pk_c,k)
        sigma=TSPS.par_sign2(self.TSPS, sigma1,Sgk_a,k)
        sigmaR=TSPS.reconst(self.TSPS, sigma,k)
        cert_c = sigmaR
        return cert_c

    def AuCreate(self,mpk,Sgk_a,kprime,k,wit,w):
        sigma1 = TSPS.par_sign1(self.TSPS,mpk,kprime,k)
        sigma = TSPS.par_sign2(self.TSPS,sigma1,Sgk_a,k)
        sigmaR = TSPS.reconst(self.TSPS,sigma,k)
        cert_j=sigmaR
        selectedWitnesses = random.sample(wit,w)
        w_j = {}; N_j={}
        list_witness_indexes = []
        for i in range(len(selectedWitnesses)):
            Witness_int=group.hash(objectToBytes(selectedWitnesses[i], group),ZR)
            sigma1 = TSPS.par_sign1(self.TSPS, mpk, mpk['g']**Witness_int,k)
            sigma = TSPS.par_sign2(self.TSPS,sigma1,Sgk_a,k)
            sigmaR = TSPS.reconst(self.TSPS,sigma,k)
            list_witness_indexes.append(wit.index(selectedWitnesses[i]))
            w_j[list_witness_indexes[i]] = sigmaR
            N_j[list_witness_indexes[i]] = mpk['h'] ** Witness_int
        cust_certified_col = (cert_j,w_j,list_witness_indexes, N_j)
        return cust_certified_col

    
    
    
    
    def main(num_mer):
        groupObj = PairingGroup('BN254')
        Nir = Nirvana(groupObj)
        Mer = []
        for i in range(int(num_mer)):
            Mer.append('Apple'+str(i+1))
        #setup
        mpk = Nir.PGen()
        mers = int(num_mer)
        print(type(mers))
        # while keep_sending:
        #     message_mpk = objectToBytes(mpk, group)
        #     socket_publish.send(message_mpk)
        #     time.sleep(10)
        #     keep_sending = False

        (sgk_a,vk_a,pk_a) = Nir.AuKeygen(mpk, 5,10)

        publish_msg = (mpk,pk_a,num_mer)

        publish_msg = objectToBytes(publish_msg,groupObj)
        time.sleep(10)
        socket_publish.send(publish_msg)
        #time.sleep(10)
        #socket_publish.close()


        #setting up poller
        poller = zmq.Poller()
        #poller.register(socket_clientCol,zmq.REQ)
        poller.register(socket_clientReg, zmq.REQ)
        poller.register(socket_clientSig, zmq.REQ)
        poller.register(socket_merchant, zmq.REQ)

        #receiving requests
        keep_receiving = True
        while keep_receiving:
            socks = dict(poller.poll())
            if(socket_clientReg) in socks:
                message_clientReg = socket_clientReg.recv(zmq.DONTWAIT)
                message_clientReg = bytesToObject(message_clientReg,groupObj)
                print(f"Received registration request from customer with publick key: {message_clientReg}")
                cert = Nir.CuRegister(mpk,sgk_a, message_clientReg,1,5)
                print(f"Sent certificate to customer: {cert}..")
                approved_registration = objectToBytes(cert,groupObj)
                socket_clientReg.send(approved_registration)
                #time.sleep(10)
                socket_clientReg.close()

            if socket_clientSig in socks:
                #Registration
                message_client = socket_clientSig.recv(zmq.DONTWAIT)
                message_client = bytesToObject(message_client,groupObj)
                k_prime = message_client
                print(f"Received request from customer for collateral signature..")
                data_to_send = (Nir.AuCreate(mpk,sgk_a,k_prime, 5, Mer,math.floor(math.log10(len(Mer)))))
                #print(Col)
                print(f"Sent collateral proof.. : {data_to_send}")
                collateral_proofs = objectToBytes(data_to_send, groupObj)
                socket_clientSig.send(collateral_proofs)
                #time.sleep(10)
                socket_clientSig.close()
                
                
            if socket_merchant in socks:
                #keygen
                message_merchant = socket_merchant.recv(zmq.DONTWAIT)
                message_merchant = bytesToObject(message_merchant,groupObj)
                print(f"Received request for public key from merchant..")
                merchant_registration_data = (Nir.MRegister(mpk,sgk_a,message_merchant,mers,5,5))
                merchant_registration_data = objectToBytes(merchant_registration_data,groupObj)
                socket_merchant.send(merchant_registration_data)
                print("Sent public key information to merchant..")
                socket_merchant.close()
                time.sleep(10)
                keep_receiving = False      

if __name__ =="__main__":
    Nirvana.main(sys.argv[1])
    #Nirvana.main('30000')
        
