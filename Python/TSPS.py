from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.secretutil import SecretUtil
from PoK import PoK
from openpyxl import Workbook
from secretshare import SecretShare
from charm.core.engine.util import serializeDict

class TSPS():
    def __init__(self, groupObj):
        global util, group
        util = SecretUtil(groupObj)        
        group = groupObj
                        
    def PGen(self):
        g, h = group.random(G1), group.random(G2)   
        e_gh = pair(g,h)
        mpk = {'g':g, 'h':h, 'e_gh':e_gh}
        return (mpk)


    def kgen(self, mpk, k,n):
        sgk={}; vk={}; X={}; Y={}; alphaShare={}; betaShare={}
        SSS = SecretShare(group, True)
        alpha, beta = group.random(), group.random()
        alphashares = SSS.genShares(alpha, k, n)
        betashares = SSS.genShares(beta, k, n)
        for i in range(1,n+1):
            alphaShare[i] = alphashares[i]
            betaShare[i] = betashares[i]
            X[i] = mpk['h'] ** alphaShare[i]
            Y[i] = mpk['h'] ** betaShare[i]
        sgk = {'alpha': alphashares, 'beta': betashares}
        vk = {'X': X, 'Y':Y}
        pk = {'X': mpk['h']**alpha, 'Y': mpk['h']**beta}
        return (sgk, vk, pk)
   

    def par_sign1(self,pk,M,k):
        R1={}; S1={}
        for i in range(1,k+1):
            r = group.random(ZR) 
            R1[i] = pk['g'] ** r
            S1[i] = M ** r
        sigma1={'R1':R1, 'S1': S1}
        return (sigma1)


    def par_sign2(self,sigma1,sk,k):
        T={}; R=1; S=1
        for i in range(1,k+1):
            R*=sigma1['R1'][i]
            S*=sigma1['S1'][i]
        for i in range(1,k+1):
            T[i] = (R ** (sk['alpha'][i])) * (S ** sk['beta'][i])
        sigma={'R':R, 'S': S, 'T':T}
        return (sigma)

    def Par_verify(self,vk,pk,sigma,N,k):
        for i in range(1,k+1):
            if pair(sigma['R'],N) == pair(sigma['S'],pk['h']) and \
            pair(sigma['T'][i],pk['h']) == pair(sigma['R'],vk['X'][i])*pair(sigma['S'],vk['Y'][i]):
                return print("True")
        else:
            return print("Wrong")


    def reconst(self, sigma, k):
        SSS = SecretShare(group, True)
        R,S,T=group.init(G2, 1),group.init(G1, 1),group.init(G1, 1); list={}
        for i in range(1,k+1):
            list[group.init(ZR, i)]=group.init(ZR, i)
        keys= list.keys()
        coeff = SSS.recoverCoefficients(keys)
        for i in range(1,k+1):
            T *= sigma['T'][i] ** coeff[group.init(ZR, i)]
        return {'R':sigma['R'], 'S':sigma['S'], 'T':T}

    def verify(self,mpk,pk,N,sigma):
        if pair(sigma['R'],N) == pair(sigma['S'],mpk['h']) and \
            pair(sigma['T'],mpk['h']) == pair(sigma['R'],pk['X'])*pair(sigma['S'],pk['Y']):
                return 1
        else:
            return 0
    
    def Randomize(self, cert_cn):
        r = group.random()
        (randomized_cert) = {'R':cert_cn['R']**r,'S':cert_cn['S']**r,'T':cert_cn['T']**r}
        return randomized_cert

'''
SPS = SPS(groupObj)
def start_bench(group):
    group.InitBenchmark()
    group.StartBenchmark(["RealTime"])

def end_bench(group):
    group.EndBenchmark()
    benchmarks = group.GetGeneralBenchmarks()
    real_time = benchmarks['RealTime']
    return real_time

def main(k,n):
    result=[n,k]   
    #setup
    setup_time=0
    for i in range(10):
        start_bench(groupObj)
        (mpk) = SPS.PGen()
        setup_time += end_bench(groupObj)
    result.append(setup_time*100)

    # key gen
    keygen_time=0
    for i in range(10):
        start_bench(groupObj)
        (sk,vk,pk) = SPS.kgen(mpk,k,n)
        keygen_time += end_bench(groupObj)
    result.append(keygen_time*100)
    key_size = sum([len(x) for x in serializeDict(sk, groupObj).values()])
    result.append(key_size)
 
 
    # Signing
    m = groupObj.random(ZR); M = mpk['g'] ** m; N = mpk['h'] ** m
    signing_time1=0
    for i in range(10):
        start_bench(groupObj)
        (sigma1) = SPS.par_sign1(mpk,M,k)
        signing_time1 += end_bench(groupObj)
    result.append(signing_time1*100)
    sig_size1 = sum([len(x) for x in serializeDict(sigma1, groupObj).values()])
    result.append(sig_size1)

    signing_time2=0
    for i in range(10):
        start_bench(groupObj)
        (sigma) = SPS.par_sign2(sigma1,sk,k)
        signing_time2 += end_bench(groupObj)
    result.append(signing_time2*100)
    sig_size = sum([len(x) for x in serializeDict(sigma, groupObj).values()])
    result.append(sig_size)

    #Par_Verify
    par_verify=0
    for i in range(10):
        start_bench(groupObj)
        (out) = SPS.Par_verify(vk,mpk,sigma,N,k)
        par_verify += end_bench(groupObj)
    result.append(par_verify*100)


    # Reconstruction
    recon_time=0
    for i in range(10):
        start_bench(groupObj)
        sigmaR = SPS.reconst(sigma, k)
        recon_time += end_bench(groupObj)
    result.append(recon_time*100)

    # Verification
    verification_time=0
    for i in range(10):
        start_bench(groupObj)
        (out) = SPS.verify(mpk, pk, N, sigmaR)
        verification_time += end_bench(groupObj)
    result.append(verification_time*100)
    return result

book = Workbook()
data = book.active
title = ["n","k","setup_time", "keygen_time", "key_size" , "Signing_time1", "Signing_time2","Par_verify" ,"signature_size", "recons_time", "verification_time"]
data.append(title)

for n in range(3,19):
    data.append(main(n-2,n))
book.save("Result.xlsx")
'''