from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.secretutil import SecretUtil
from charm.toolbox.ABEnc import Input, Output
from secretshare import SecretShare
from charm.core.engine.util import serializeDict,objectToBytes
import random
import time
import zmq
import json
from datetime import datetime
from openpyxl import load_workbook
from openpyxl import Workbook
from PoK import PoK


context = zmq.Context()
socket_client = context.socket(zmq.REP)
socket_client.bind("tcp://*:5551") #customer connection

socket_merchant = context.socket(zmq.REP)
socket_merchant.bind("tcp://*:5557") #merchant connection
socket_publish = context.socket(zmq.PUSH)
socket_publish.bind("tcp://*:5556") #publishing mpk

mpk_t = { 'g':G1, 'h':G2, 'pp': G2, 'e_gh':GT, 'e_Xh':GT, 'vk':G2 , 'X': G1 }
msk_t = { 'sec':ZR, 'sgk':ZR }
pk_t = { 'pk':G2, 'Merlist':str }
sk_t = { 'shares': ZR }
Col_t = { 'PRFkey': ZR, 'key':G1, 'R':G2, 'S':G1, 'T':G1, 'W':G1 }
Rand_t = {'Rprime':G2, 'Sprime':G1, 'Tprime':G1, 'Wprime':G1}
ct_t = { 'C':GT, 'C1':GT, 'R':GT}
proof_t = {'z': ZR, 't': GT, 'y': GT}
proof1_t = {'z1': ZR, 'z2': ZR, 't': GT, 'y': GT}
prf_t= {'H':G1, 't':G1, 'c':ZR, 'r':ZR}

class Nirvana():
    def __init__(self, groupObj):
        global util, group
        util = SecretUtil(groupObj)
        group = groupObj
    
    @Output(mpk_t, msk_t)    
    def Setup(self):
        g, h, sec, sgk = group.random(G1), group.random(G2), group.random(ZR), group.random(ZR)
        g.initPP(); h.initPP()
        pp = h ** sec; e_gh = pair(g,h)
        vk = h ** sgk; X = group.random(G1); e_Xh=pair(X,h)
        mpk = {'g':g, 'h':h, 'pp':pp, 'e_gh':e_gh, 'e_Xh':e_Xh, 'vk': vk, 'X': X}
        msk = {'sec':sec, 'sgk':sgk }
        return (mpk, msk)

    @Input(mpk_t, msk_t, [str])
    @Output(pk_t, sk_t)
    def Keygen(self, mpk, msk, Merchants):
        pkey = {}
        shares = SSS.genShares(msk['sec'], 2, len(Merchants))
        for i in range(len(shares)-1):
            pkey[i] = mpk['h'] ** shares[i+1]
        pk = {'pk': pkey, 'Merlist': Merchants}
        sk = {'shares':shares}
        return (pk, sk)

    @Input(mpk_t, msk_t, int)
    @Output(Col_t)
    def Registeration(self, mpk, msk, n):
        PRFkey={}; key={}; S={}; T={}; t=group.random(ZR)
        for i in range(n):
            PRFkey[i] = group.random(ZR)
            key[i]= mpk['g'] ** PRFkey[i]
            S[i] = (key[i] ** (msk['sgk']/t)) * (mpk['X']**(1/t))
            T[i] = (S[i] ** (msk['sgk']/t)) * (mpk['g']**(1/t))
        R = mpk['h']**t
        W = mpk['g']**(1/t)
        return { 'PRFkey': PRFkey, 'key': key, 'R':R, 'S':S, 'T':T, 'W':W }

groupObj = PairingGroup('BN254')
Nir = Nirvana(groupObj)
PoK = PoK(groupObj)
SSS = SecretShare(groupObj)
Mer = ['Apple','Ebay','Tesco','Amazon','Tesla','Colruyt','BMW','hp','Albert','IKEA']

#setup
(mpk, msk) = Nir.Setup()
keep_sending = True
# while keep_sending:
#     message_mpk = objectToBytes(mpk, group)
#     socket_publish.send(message_mpk)
#     time.sleep(10)
#     keep_sending = False
(pk,sk) = Nir.Keygen(mpk, msk, Mer)

#setting up poller
poller = zmq.Poller()
poller.register(socket_client, zmq.REQ)
poller.register(socket_merchant, zmq.REQ)

#receiving requests
keep_receiving = True
while keep_receiving:
    socks = dict(poller.poll())
    if socket_client in socks:
        #Registration
        message_client = socket_client.recv(zmq.DONTWAIT)
        message_client = message_client.decode('utf-8')
        print(f"Received request from customer for {message_client} collaterals ..")
        Col = (mpk, Nir.Registeration(mpk, msk, int(message_client)))
        #print(Col)
        collateral_proofs = objectToBytes(Col, group)
        socket_client.send(collateral_proofs)
        print("Sent collateral proof..")
        socket_client.close()
        
    if socket_merchant in socks:
        #keygen
        message_merchant = socket_merchant.recv(zmq.DONTWAIT)
        print(f"Received request: {message_merchant}")
        message_merchant = message_merchant.decode('utf-8')
        N = pk['Merlist'].index(message_merchant)
        public_key = objectToBytes(pk['pk'][N], group)
        socket_merchant.send(public_key)
        print("Sent public key information to merchant..")
        socket_merchant.close()

        keep_receiving = False        
        
