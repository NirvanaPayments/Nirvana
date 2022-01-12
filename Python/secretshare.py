# Implementing the proof of concept secret sharing 
from charm.toolbox.pairinggroup import PairingGroup,ZR,order

class SecretShare:
    def __init__(self, element, verbose_status=True):
        self.elem = element
        self.verbose = verbose_status
        
    def P(self, coeff, x):
        share = 0
        # evaluate polynomial
        for i in range(0, len(coeff)):
            share += (coeff[i] * (x ** i))
        return share

    def genShares(self, secret, k=0, n=0, q=None, x_points=None):
        if(k <= n):
            if q == None: 
                q = [self.elem.random(ZR) for i in range(0, k)]
                q[0] = secret

            if x_points == None: # just go from 0 to n
                shares = [self.P(q, i) for i in range(0, n+1)] # evaluating poly. q at i for all i
            else:
                shares = {}
                for i in range(len(x_points)):
                    shares[i] = (x_points[i], self.P(q, x_points[i]))
#                     = [self.P(q, i) for i in x_points] # x_points should be a list

        # debug
        if self.verbose:
            for i in range(0, 1):
                print("")
            print('')
            if x_points == None:
                for i in range(1,1):
                    print('Share %s: %s' % (i, shares[i]))
            else:
                for i in range(1):
                    print('Share %s: %s' % (i, shares[i]))
            
        return shares
    
    # shares is a dictionary
    def recoverCoefficients(self, list):
        coeff = {}
        for i in list:
            result = 1
            for j in list:
                if not (i == j):
                    # lagrange basis poly
                    result *= (0 - j) / (i - j)
            if self.verbose: print("")
            coeff[i] = result
        return coeff

    # shares is a dictionary
    def recoverCoefficientsDict(self, dict):
        coeff = {}
        for i in dict.values():
            result = 1
            for j in dict.values():
                if not (i == j):
                    # lagrange basis poly
                    result *= (0 - j) / (i - j)
            coeff[i] = result
        return coeff
        
    def recoverSecret(self, shares):
        list = shares.keys()
        if self.verbose: print(list)
        coeff = self.recoverCoefficients(list)
        if self.verbose: print("coefficients: ", coeff)
        secret = 0
        for i in list:
            secret += (coeff[i] * shares[i])

        return secret
