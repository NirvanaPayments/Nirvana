from charm.core.engine.util import objectToBytes
from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair

class PoK():
    def __init__(self, groupObj):
        global util, group
        group = groupObj
    def prover1(self,g,y,x):
        r = group.random(ZR)
        t = g ** r
        c = group.hash(objectToBytes(y, group)+objectToBytes(t, group),ZR)
        z = c * x + r
        return { 'z':z, 't':t, 'y':y }
    def prover2(self, Ct, g, y, x1, x2):
        r1 = group.random(ZR); r2 = group.random(ZR)
        t = (Ct ** r1) * (g ** r2)
        c = group.hash(objectToBytes(y, group)+objectToBytes(t, group),ZR)
        z1 = c * x1 + r1
        z2 = c * x2 + r2
        return { 'z1':z1, 'z2':z2, 't':t, 'y':y }
    def prover3(self,g,y,x,u):
        r = group.random(ZR)
        t = pair(g,u) ** r
        c = group.hash(objectToBytes(y, group)+objectToBytes(t, group)+objectToBytes(u, group),ZR)
        z = c * x + r
        return { 'z':z, 't':t, 'y':y }
    def prover4(self,y,x,R):
        Rbyte=objectToBytes(0, group)
        r= group.random(ZR)
        t = R ** r
        Rbyte += objectToBytes(R, group)
        c = group.hash(objectToBytes(y, group) + objectToBytes(t, group) + Rbyte, ZR)
        z= c * x + r
        return { 'z':z, 't':t, 'y':y } 
    def verifier1(self, g, y, z, t):
        c = group.hash(objectToBytes(y, group)+objectToBytes(t, group),ZR)
        if (y**c) * t == g ** z:
            return 1
        else:
            return 0
    def verifier2(self, Ct, g, y, z1, z2, t, u):
        c = group.hash(objectToBytes(y, group)+objectToBytes(t, group),ZR)
        if (y**c) * (u ** c) * t == (Ct ** z1) * (g ** z2):
            return 1
        else:
            return 0
    def verifier3(self, g, y, z, t, u):
        c = group.hash(objectToBytes(y, group)+objectToBytes(t, group)+objectToBytes(u, group),ZR)
        if (y**c) * t == pair(g,u) ** z:
            return 1
        else:
            return 0
    def verifier4(self, y, z, t, p, u):
        c = group.hash(objectToBytes(y, group)+objectToBytes(t, group)+objectToBytes(u, group),ZR)
        if (y**c) * t == p ** z:
            return 1
        else:
            return 0
    def verifier5(self, y, z, t, R):
        Rbyte=objectToBytes(0,group)
        RHS = R ** z
        Rbyte += objectToBytes(R, group)
        c = group.hash(objectToBytes(y, group) + objectToBytes(t, group) + Rbyte, ZR)
        if (y**c) * t == RHS:
            return 1
        else:
            return 0


'''
groupObj = PairingGroup('BN254')
PoK1 = PoK1(groupObj)
PoK2 = PoK2(groupObj)
PoK3 = PoK3(groupObj)
g, h = groupObj.random(G1), groupObj.random(G2)
x = group.random(ZR)
y = g ** x
(proof1) = PoK1.prover(g,y,x)
(result1) = PoK1.verifier(g,y,proof1['z'],proof1['t'])
v = group.random(ZR)
u = h ** v
y = pair(g,u) ** x
(proof2) = PoK2.prover(g,y,x,u)
(result2) = PoK2.verifier(g,y,proof2['z'],proof2['t'],u)
X=[]; R=[]; y=1
for i in range(10):
    X.append(group.random(ZR))
    R.append(group.random(GT))
    y *= R[i] ** X[i]
(proof3) = PoK3.prover(g,y,X,R)
(result3) = PoK3.verifier(g,y,proof3['z'],proof3['t'],R)
print(result2)
(proof4) = PoK4.prover(g,y,X,R)
(result4) = PoK4.verifier(g,proof4['y'],proof4['z'],proof4['t'],R)
print(result2)
'''