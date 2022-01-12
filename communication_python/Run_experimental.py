from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.secretutil import SecretUtil
from charm.toolbox.ABEnc import Input, Output
from secretshare import SecretShare
from charm.core.engine.util import serializeDict,objectToBytes, bytesToObject
import random
from datetime import datetime
from openpyxl import load_workbook
from openpyxl import Workbook
from PoK import PoK

mpk_t = { 'g':G1, 'h':G2, 'pp': G2, 'e_gh':GT, 'e_Xh':GT, 'vk':G2 , 'X': G1 }
msk_t = { 'sec':ZR, 'sgk':ZR }
pk_t = { 'pk':G2, 'Merlist':str }
sk_t = { 'shares': ZR }
Col_t = { 'PRFkey': ZR, 'key':G1, 'R':G2, 'S':G1, 'T':G1, 'W':G1 }
Rand_t = {'Rprime':G2, 'Sprime':G1, 'Tprime':G1, 'Wprime':G1}
ct_t = { 'C':GT, 'C1':GT, 'R':GT}
proof1_t = {'p1z': ZR, 'p1t': GT, 'p1y': GT}
proof4_t = {'p4z': ZR, 'p4t': GT, 'p4y': GT}
proof3_t = {'p3z': ZR, 'p3t': GT, 'p3y': GT}
proof2_t = {'p2z1': ZR, 'p2z2': ZR, 'p2t': GT, 'p2y': GT}
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

    @Input(mpk_t, Col_t, pk_t, ZR, int, int, ZR, GT)
    @Output(ct_t,Rand_t,proof1_t,proof4_t,proof3_t,proof2_t)
    def Spending(self, mpk, Col, pk, time, d ,N, IDsk,ID):
        SAgg=1; TAgg=1; PRFkey=0; R=[]; X=[]; y2=1
        if len(Col['PRFkey']) >= d:
            for i in range(d):
                SAgg *= Col['S'][i]
                TAgg *= Col['T'][i]
                PRFkey += Col['PRFkey'][i]
                R.append(mpk['e_gh'] ** (1/(Col['PRFkey'][i]+time)))
                X.append(Col['PRFkey'][i])
                y2 *= R[i] ** X[i]
                A = pair(mpk['g'],mpk['vk']) ** PRFkey
            tprime = group.random(ZR)
            Rprime = Col['R'] ** (1/tprime)
            Sprime = SAgg ** tprime
            Tprime = (TAgg ** (tprime**2))* (Col['W']**(d*tprime*(1-tprime)))
            Wprime = Col['W'] ** (1/tprime)
            r = mpk['g'] ** (1/(PRFkey+time))
            C = ID * (pair(r, mpk['pp']))
            C1 = pair(r, pk['pk'][N])
            (proof1) = PoK.prover1(mpk['g'],A,PRFkey,mpk['vk']) #Proof of SPS
            (proof2) = PoK.prover4(y2,X,R) # Proof of Aggeragetd collatorals
            (proof3) = PoK.prover3(r,C1**PRFkey,PRFkey,pk['pk'][N]) #Proof of ciphertext C1
            (proof4) = PoK.prover2(C,mpk['e_gh'],((C/ID)**PRFkey)*(mpk['e_gh']**(-time*IDsk)),PRFkey,(-time*IDsk)) #Proof of ciphertext C0
            Rand = { 'Rprime':Rprime, 'Sprime':Sprime, 'Tprime':Tprime, 'Wprime':Wprime }
            ct = { 'C': C, 'C1': C1, 'R':R }
            return (ct, Rand, proof1, proof2, proof3, proof4)
        else:
            return (print("You don't have enough money in your account"), None)


    # @Input(mpk_t, Col_t, pk_t, ZR, int, int, ZR, GT, ZR, list, GT)
    # @Output(ct_t,proof1_t,proof4_t,proof3_t,proof2_t)
    # def PPSpending(self, mpk, Col, pk, time, d ,N, IDsk, ID, PRFkey, X, A):
    #     R=[]; y2=1
    #     if len(Col['PRFkey']) >= d:
    #         for i in range(d):
    #             R.append(mpk['e_gh'] ** (1/(X[i]+time)))
    #             y2 *= R[i] ** X[i]
    #         r = mpk['g'] ** (1/(PRFkey+time))
    #         C = ID * (pair(r, mpk['pp']))
    #         C1 = pair(r, pk['pk'][N])
    #         (proof1) = PoK.prover1(mpk['g'],A,PRFkey,mpk['vk']) #Proof of SPS
    #         (proof2) = PoK.prover4(y2,X,R) # Proof of Aggeragetd collatorals
    #         (proof3) = PoK.prover3(r,C1**PRFkey,PRFkey,pk['pk'][N]) #Proof of ciphertext C1
    #         (proof4) = PoK.prover2(C,mpk['e_gh'],((C/ID)**PRFkey)*(mpk['e_gh']**(-time*IDsk)),PRFkey,(-time*IDsk)) #Proof of ciphertext C0
    #         ct = { 'C': C, 'C1': C1, 'R':R }
    #         return (ct, proof1, proof2, proof3, proof4)
    #     else:
    #         return (print("You don't have enough money in your account"), None)
    @Input(mpk_t, Rand_t, ct_t, proof1_t, proof4_t, proof3_t, proof2_t, G2, int, list, ZR)
    @Output(list)
    def Verification(self, mpk, Rand, ct, proof1, proof2, proof3, proof4, mer_pk, d, Ledger, time):
        LHS=1
        for i in range(len(ct['R'])):
            LHS *= (mpk['e_gh'] * ct['R'][i] ** (-time)) 
        if pair(Rand['Sprime'], Rand['Rprime']) == proof1['p1y'] * mpk['e_Xh'] ** d and \
            pair(Rand['Tprime'],Rand['Rprime']) == pair(Rand['Sprime'],mpk['vk']) * mpk['e_gh']**d and \
                LHS==proof2['p4y'] and \
                    pair(mpk['g'],mpk['pp']) * (ct['C']**(-time)) == proof4['p2y'] and \
                    pair(mpk['g'],mer_pk) * (ct['C1'] ** (-time)) == proof3['p3y'] and \
                    PoK.verifier3(mpk['g'],proof1['p1y'],proof1['p1z'],proof1['p1t'],mpk['vk']) == 1 and \
                        PoK.verifier5(proof2['p4y'],proof2['p4z'],proof2['p4t'],ct['R']) == 1 and \
                            PoK.verifier4(proof3['p3y'],proof3['p3z'],proof3['p3t'],ct['C1'],mer_pk) == 1 and \
                                PoK.verifier2(ct['C'],mpk['e_gh'],proof4['p2y'],proof4['p2z1'],proof4['p2z2'],proof4['p2t'])==0 and \
                                ct['R'] not in Ledger:
                Ledger.append(ct['R'])
                print("passed")
                return Ledger
        else:
            print("not passed")
            return Ledger

    @Input(mpk_t, ct_t, int, ct_t, int)
    @Output(GT)
    def Decryption(self, mpk, ct1, M1, ct2, M2): 
        Coeff = SSS.recoverCoefficients([group.init(ZR, M1+1),group.init(ZR, M2+1)])
        return ct2['C'] / ((ct1['C1']**Coeff[M1+1])*(ct2['C1']**Coeff[M2+1]))


def start_bench(group):
    group.InitBenchmark()
    group.StartBenchmark(["RealTime"])

def end_bench(group):
    group.EndBenchmark()
    benchmarks = group.GetGeneralBenchmarks()
    real_time = benchmarks['RealTime']
    return real_time

groupObj = PairingGroup('BN254')
Nir = Nirvana(groupObj)
PoK = PoK(groupObj)
SSS = SecretShare(groupObj)
Mer = ['Apple','Ebay','Tesco','Amazon','Tesla','Colruyt','BMW','hp','Albert','IKEA'] * 201

def run_round_trip(n,d,M):
    result=[n,d,M]
    # setup
    
    setup_time = 0
    for i in range(1):
        start_bench(groupObj)
        (mpk, msk) = Nir.Setup()
        setup_time += end_bench(groupObj)
    setup_time = setup_time  
    result.append(setup_time)
    public_parameters_size = sum([len(x) for x in serializeDict(mpk, groupObj).values()]) 
    result.append(public_parameters_size)
    # Key Gen
    Merchants = random.sample(Mer, M)
    Key_Gen_time=0
    for i in range(10):
        start_bench(groupObj)
        (pk,sk) = Nir.Keygen(mpk, msk, Merchants)
        Key_Gen_time += end_bench(groupObj)
    Key_Gen_time = Key_Gen_time * 100
    public_key_size = sum([len(x) for x in serializeDict(pk, groupObj).values()]) 
    secret_key_size = sum([len(x) for x in serializeDict(sk, groupObj).values()]) 
    secret_key_size = secret_key_size /10
    public_key_size = public_key_size /10
    result.append(Key_Gen_time)
    result.append(public_key_size)
    result.append(secret_key_size)

    # Registeration
    
    Registeration_time=0
    for i in range(10):
        start_bench(groupObj)
        (Col) = Nir.Registeration(mpk, msk, n)
        Registeration_time += end_bench(groupObj)
    Registeration_time = Registeration_time * 100
    Collateral_size = sum([len(x) for x in serializeDict(Col, groupObj).values()]) 
    Collateral_size = Collateral_size
    result.append(Registeration_time)
    result.append(Collateral_size)

    # Spending
    IDsk = group.random(ZR); ID= mpk['e_gh']**IDsk 
    N = pk['Merlist'].index('Amazon')
    Spending_time = 0; time=groupObj.hash(objectToBytes(str(datetime.now()), group),ZR)
    for i in range(10):
        start_bench(groupObj)
        (ct1, Rand1,proof1,proof2,proof3,proof4) = Nir.Spending(mpk, Col, pk, time, d, N, IDsk, ID)
        Spending_time += end_bench(groupObj)
    Spending_time = Spending_time /10
    result.append(Spending_time)
    Ciphertext_size = sum([len(x) for x in serializeDict(ct1, groupObj).values()]) + sum([len(x) for x in serializeDict(Rand1, groupObj).values()]) + sum([len(x) for x in serializeDict(proof1, groupObj).values()]) + sum([len(x) for x in serializeDict(proof2, groupObj).values()]) + sum([len(x) for x in serializeDict(proof3, groupObj).values()]) + sum([len(x) for x in serializeDict(proof4, groupObj).values()]) 
    result.append(Ciphertext_size/1000)
    (ct2, Rand2,p1,p2,p3,p4) = Nir.Spending(mpk, Col, pk, time, d, N+1,IDsk,ID)
    spend_proof = (mpk, ct1, Rand1, proof1, proof2, proof3, proof4, time)
    spend_proof = objectToBytes(spend_proof, group)
    # PP Spending
    # SAgg=1; TAgg=1; PRFkey=0; X=[]; y2=1
    # for i in range(d):
    #     SAgg *= Col['S'][i]
    #     TAgg *= Col['T'][i]
    #     PRFkey += Col['PRFkey'][i]
    #     X.append(Col['PRFkey'][i])
    #     A = pair(mpk['g'],mpk['vk']) ** PRFkey
    # tprime = group.random(ZR)
    # Rprime = Col['R'] ** (1/tprime)
    # Sprime = SAgg ** tprime
    # Tprime = (TAgg ** (tprime**2))* (Col['W']**(d*tprime*(1-tprime)))
    # Wprime = Col['W'] ** (1/tprime)
    # Rand = { 'Rprime':Rprime, 'Sprime':Sprime, 'Tprime':Tprime, 'Wprime':Wprime }
    # PPSpending_time = 0; time=groupObj.hash(objectToBytes(str(datetime.now()), group),ZR)
    # for i in range(10):
    #     start_bench(groupObj)
    #     (ct1, proof1, proof2, proof3, proof4) = Nir.PPSpending(mpk, Col, pk, time, d, N, IDsk, ID,PRFkey,X,A)
    #     PPSpending_time += end_bench(groupObj)
    # PPSpending_time = PPSpending_time /10
    # result.append(PPSpending_time)
    # Verification 
    Verification_time = 0
    spend_proof = bytesToObject(spend_proof, groupObj)
    N = pk['Merlist'].index('Amazon')
    mer_pk = pk['pk'][N]
    for i in range(10):
        start_bench(groupObj)
        Ledger=[]
        #out = Nir.Verification(mpk, pk, Rand1, ct1, proof1, proof2, proof3, proof4 , d, Ledger, time, N)
        
        mpkst = spend_proof[0]
        randomstr = spend_proof[2]
        ct1st = spend_proof[1]
        proof1st = spend_proof[3]
        proof2st = spend_proof[4]
        proof3st = spend_proof[5]
        proof4st = spend_proof[6]
        timest = spend_proof[7]
        out = Nir.Verification(mpkst, randomstr, ct1st, proof1st, proof2st, proof3st, proof4st, mer_pk, d, Ledger, timest)
        Verification_time += end_bench(groupObj)
    Verification_time = Verification_time /10
    #print(out)
    result.append(Verification_time) 
    #(out2)= Nir.Verification(mpk,ct2,Rand2)


    # Decryption
    Decryption_time = 0
    for i in range(1):
        start_bench(groupObj)
        (out)= Nir.Decryption(mpk, ct1, 1, ct2, 2)
        Decryption_time += end_bench(groupObj)
    Decryption_time = Decryption_time  
    result.append(Decryption_time)

    return result

# book=Workbook()
# data=book.active
# title=["n","d","M","setup_time","public_parameters_size", "Key_Gen_time","public_key_size","secret_key_size","Registeration_time","Collateral_size","Spending_time","Ciphertext_size","PPSpending_time","Verification_time","Decryption_time"]
# data.append(title)
# for n in range(1,3):
#     data.append(run_round_trip(n,n,50*n))
#     print(n)
# book.save("Result1.xlsx")

run_round_trip(3, 1, 50)