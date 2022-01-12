from Nirvana import Nirvana   
from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.secretutil import SecretUtil
from BLS import BLS01
#from charm.toolbox.ABEnc import Input, Output
from secretshare import SecretShare
from charm.core.engine.util import serializeDict,objectToBytes
from openpyxl import load_workbook
from openpyxl import Workbook
import math
from TSPS import TSPS
import random
from datetime import datetime

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
SSS = SecretShare(groupObj)
TSPS = TSPS(groupObj)
BLS01 = BLS01(groupObj)



time=groupObj.hash(objectToBytes(str(datetime.now()), groupObj),ZR)


#Nir.Decryption(mpk, ct1, M1, ct2, M2)

def run_round_trip(n,k,M,C):
    #n=10; k=math.floor(n/2)
    result=[n,k,M,C]
    Mer = []
    for i in range(M):
        Mer.append('Apple'+str(i+1))
    Ledger=dict.fromkeys(list(range(M)), [])
    Cus = []
    for i in range(C):
        Cus.append('Alice'+str(i+1))
    # setup
    setup_time = 0
    for i in range(10):
        start_bench(groupObj)
        (mpk) = Nir.PGen()
        setup_time += end_bench(groupObj)
    setup_time = setup_time * 100
    result.append(setup_time)
    public_parameters_size = sum([len(x) for x in serializeDict(mpk, groupObj).values()]) 
    result.append(public_parameters_size)
    # AuKeyGen
    #Merchants = random.sample(Mer, M)
    AuKeyGentime=0
    for i in range(10):
        start_bench(groupObj)
        (Sgk_a,Vk_a,Pk_a) = Nir.AuKeygen(mpk,k,n)
        AuKeyGentime += end_bench(groupObj)
    AuKeyGentime = AuKeyGentime * 100
    public_key_size = sum([len(x) for x in serializeDict(Vk_a, groupObj).values()]) 
    #secret_key_size = sum([len(x) for x in serializeDict(msk, groupObj).values()]) 
    #secret_key_size = secret_key_size /10
    public_key_size = public_key_size
    result.append(AuKeyGentime)
    result.append(public_key_size)
    #result.append(secret_key_size)

    # MerKeyGen
    Mkeygentime=0
    for i in range(10):
        start_bench(groupObj)
        (Vk_b,Sk_b) = Nir.MKeygen(mpk,len(Mer))
        Mkeygentime += end_bench(groupObj)
    Mkeygentime = Mkeygentime * 100
    result.append(Mkeygentime)

    # MerRegister
    MRegistertime=0
    for i in range(1):
        start_bench(groupObj)
        (Pk_b,cert_b) = Nir.MRegister(mpk,Sgk_a,Vk_b,len(Mer),k)
        MRegistertime += end_bench(groupObj)
    MRegistertime = MRegistertime * 100
    result.append(MRegistertime)

    # CuKeyGen
    CuKeyGentime=0
    for i in range(10):
        start_bench(groupObj)
        (Sk_c,Pk_c) = Nir.CuKeyGen(mpk,len(Cus))
        CuKeyGentime += end_bench(groupObj)
    CuKeyGentime = CuKeyGentime * 100
    result.append(CuKeyGentime)

    # CuRegister
    CuRegistertime=0
    for i in range(10):
        start_bench(groupObj)
        (cert_c) = Nir.CuRegister(mpk,Sgk_a,Pk_c,len(Cus),k)
        CuRegistertime += end_bench(groupObj)
    CuRegistertime = CuRegistertime * 100
    result.append(CuRegistertime)
    
    # CuCreate
    CuCreatetime=0
    for i in range(10):
        start_bench(groupObj)
        (key, N, kprime,certprime,picol) = Nir.CuCreate(mpk,cert_c[10])
        CuCreatetime += end_bench(groupObj)
    CuCreatetime = CuCreatetime * 100
    result.append(CuCreatetime)


    # AuCreate
    AuCreatetime=0
    for i in range(10):
        start_bench(groupObj)
        cert_j,w_j,listIndexes, N_j = Nir.AuCreate(mpk,Sgk_a,kprime,k,Mer,math.floor(math.log2(len(Mer))),certprime,picol)
        AuCreatetime += end_bench(groupObj)
    AuCreatetime = AuCreatetime * 100
    result.append(AuCreatetime)
    
 
    Collateral_size = sum([len(x) for x in serializeDict(cert_j, groupObj).values()]) 
    Collateral_size = Collateral_size
    result.append(Collateral_size)

    # Spending
    ID = mpk['e_gh'] ** Sk_c[10]
  
    #N = pk['Merlist'].index('Apple')
    Spending_time = 0; time=groupObj.hash(objectToBytes(str(datetime.now()), groupObj),ZR)
    for i in range(1):
        start_bench(groupObj)
        (pi,inp,R,wprime_j) = Nir.Spending(mpk, key, Pk_b[8], time,ID, Sk_c[10],cert_j,w_j,listIndexes)
        Spending_time += end_bench(groupObj)
    Spending_time = Spending_time * 10
    result.append(Spending_time)
    Ciphertext_size = sum([len(x) for x in serializeDict(inp, groupObj).values()]) + sum([len(x) for x in serializeDict(pi, groupObj).values()]) 
    result.append(Ciphertext_size)



    # Verification 
    L1=pair(mpk['g'],mpk['pp']) 
    L2=pair(mpk['g'],Pk_b[8])
    Verification_time = 0
    for i in range(1):
        start_bench(groupObj)
        out = Nir.Verification(mpk, Pk_a, N, pi, inp, R, Ledger, time,L1,L2, Pk_b[8], wprime_j, listIndexes,N_j,Sk_b)
        Verification_time += end_bench(groupObj)
    Verification_time = Verification_time * 10
    result.append(Verification_time) 
    #(out2)= Nir.Verification(mpk,ct2,Rand2)

    '''
    # Decryption
    Decryption_time = 0
    for i in range(1):
        start_bench(groupObj)
        (out)= Nir.Decryption(mpk, ct1, 1, ct2, 2)
        Decryption_time += end_bench(groupObj)
    Decryption_time = Decryption_time * 10
    result.append(Decryption_time)
    '''
    return result

book=Workbook()
data=book.active
title=["n","d","M","C","setup_time","public_parameters_size","AuKeyGentime","AU-Verification_size","Mkeygentime","MRegistertime","CuKeyGentime","CuRegistertime","CuCreatetime","AuCreatetime","Collateral_size","Spending_time","Request_size","Verification_time","Decryption_time"]
data.append(title)
for n in range(10,11):
    data.append(run_round_trip(n,math.floor(n/2),5*n,5*n))
    print(n)
book.save("NewResult.xlsx")