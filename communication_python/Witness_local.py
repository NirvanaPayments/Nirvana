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


class Witness():
    def __init__(self, groupObj):
        global util, group
        util = SecretUtil(groupObj)
        group = groupObj
        self.TSPS = TSPS(groupObj)
        self.BLS01 = BLS01(groupObj)
        

    def WitnessApproval(self,mpk, pk, R, wprime_j, witnessindexes,N_j, Sk_b,Ledger):
        sigma = {}
        for i in witnessindexes:
            if R not in Ledger[i] and \
                TSPS.verify(self.TSPS,mpk,pk,N_j[str(i)],wprime_j[str(i)])==1:
                Ledger[i] = R
                sigma[i] = BLS01.sign(self.BLS01,Sk_b[i], R)
        return sigma


