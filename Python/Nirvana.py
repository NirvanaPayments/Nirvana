from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.secretutil import SecretUtil
#from charm.toolbox.ABEnc import Input, Output
from secretshare import SecretShare
from charm.core.engine.util import serializeDict,objectToBytes
import random
from datetime import datetime
from openpyxl import load_workbook
from openpyxl import Workbook
from PoK import PoK
from TSPS import TSPS
from BLS import BLS01
from secretshare import SecretShare as SSS
from Witness import Witness
import math

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
        (Sgk_a,Vk_a,Pk_a) = TSPS.kgen(self,mpk,k,n)
        return (Sgk_a,Vk_a,Pk_a)

    def MKeygen(self,mpk,M):
        Vk_b={};Sk_b={}
        for i in range(M):
            (vk_b,sk_b)=BLS01.keygen(self.BLS01, mpk['g'])
            Vk_b[i]=vk_b; Sk_b[i]=sk_b    
        return (Vk_b,Sk_b)
    
    def MRegister(self,mpk,sgk,vkm,M,k):
        cert_b={}; Pk_b={}
        s=group.random()
        mpk['pp'] = mpk['h']**s
        shares= SSS.genShares(self.SecretShare, s, 2, M)
        for i in range(1,M):
            sigma1 = TSPS.par_sign1(self.TSPS,mpk,vkm[i],k)
            sigma = TSPS.par_sign2(self.TSPS,sigma1,sgk,k)
            sigmaR = TSPS.reconst(self.TSPS,sigma,k)
            cert_b[i]=sigmaR
            Pk_b[i]=mpk['h']**shares[i]
        return (Pk_b,cert_b)

    def CuKeyGen(self,mpk,C):
        Sk_c={}; Pk_c={}
        for i in range(C):
            sk=group.random(); Sk_c[i]=sk
            pk=mpk['g'] ** sk; Pk_c[i]=pk
        return (Sk_c,Pk_c)

    def CuRegister(self, mpk,Sgk_a,Pk_c,C,k):
        cert_c={}
        for i in range(C):
            sigma1=TSPS.par_sign1(self.TSPS, mpk,Pk_c[i],k)
            sigma=TSPS.par_sign2(self.TSPS, sigma1,Sgk_a,k)
            sigmaR=TSPS.reconst(self.TSPS, sigma,k)
            cert_c[i]=sigmaR
        return cert_c

    def CuCreate(self, mpk,cert_cn):
        K={}; Kprime={}; Col={}
        key = group.random()
        kprime = mpk['g']**key
        N = mpk['h']**key
        pi=PoK.prover1(self.PoK,mpk['g'],kprime,key)
        certprime = TSPS.Randomize(self.TSPS, cert_cn)
        return (key, N, kprime, certprime,pi)
    
    def AuCreate(self,mpk,Sgk_a,kprime,k,wit,w,certprime,picol):
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
        return cert_j,w_j,list_witness_indexes, N_j

    def Spending(self, mpk, key, pk_bm, time,ID,Sk_cn,cert_j,w_j,listWitness):
        r = mpk['g'] ** (1/(key+time))
        R = pair(r,mpk['h'])
        A1 = (pair(r, mpk['pp']))
        C = ID * A1
        C1 = pair(r, pk_bm)
        wprime_j = {}
        for i in listWitness:
            wprime_j[i] = TSPS.Randomize(self.TSPS,w_j[i])
            print(wprime_j[i])
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


    def Verification(self, mpk, Pk_a, N, pi ,inp, R, Ledger, time,L1,L2,pk,wprime_j,witnessindexes,N_j,Sk_b):
        if R not in Ledger and \
            TSPS.verify(self.TSPS, mpk, Pk_a, N, inp['cert'])==1 and \
                mpk['e_gh'] * (R ** (-time))==pi['pi2']['y'] and \
                    L1 * (inp['C']**(-time)) == pi['pi4']['y'] and \
                    L2 * (inp['C1'] ** (-time)) == pi['pi3']['y'] and \
                        PoK.verifier3(self.PoK,mpk['g'],pi['pi1']['y'],pi['pi1']['z'],pi['pi1']['t'],mpk['pp']) == 0 and \
                        PoK.verifier5(self.PoK,pi['pi2']['y'],pi['pi2']['z'],pi['pi2']['t'],R) == 1 and \
                            PoK.verifier4(self.PoK,pi['pi3']['y'],pi['pi3']['z'],pi['pi3']['t'],inp['C1'],pk) == 1 and \
                                PoK.verifier2(self.PoK,inp['C'],mpk['e_gh'],pi['pi4']['y'],pi['pi4']['z1'],pi['pi4']['z2'],pi['pi4']['t'],inp['u'])==1:
                                        sigma = Witness.WitnessApproval(self.witness,mpk, Pk_a, R, wprime_j, witnessindexes,N_j, Sk_b,Ledger)
                                        if len(sigma)>= math.ceil(len(witnessindexes)/2):
                                            print("Verification succeeded")
        else:
            print("Verification failed")

    def Decryption(self, mpk, ct1, M1, ct2, M2): 
        Coeff = SSS.recoverCoefficients([group.init(ZR, M1+1),group.init(ZR, M2+1)])
        return ct2['C'] / ((ct1['C1']**Coeff[M1+1])*(ct2['C1']**Coeff[M2+1]))

