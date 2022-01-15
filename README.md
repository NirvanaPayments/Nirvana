# Nirvana

Nirvana enables a customer to instantly transact with a merchant using a cryptocurrency of their choice.

Prerequisites: Please follow all steps in http://pages.cs.wisc.edu/~ace/install-charm.html, add install zmq. 

The structure of this repository is as follows:

    Python: Python code for Nirvana to emulate it locally. Please execute Test.py for testing Nirvana. 
    
        BLS.py: Python code to emulate BLS signatures in Nirvana
        Nirvana.py: Python code to emulate Nirvana payments in a local environment
        PoK.py: Python code for NIZKs used in Nirvana
        TSPS.py: Python code to emulate our proposed TSPS scheme for Nirvana
        Test.py: Python code to test Nirvana.py locally
        secretshare.py: Python code for Shamir secret sharing
 
    communication_python: Python code to emulate Nirvana in a distributed environment. Please execute script.bash for testing Nirvana.
    
        BLS.py: Python code to emulate BLS signatures in Nirvana
        Customer_preprocessed.py: Python code to emulate a customer in Nirvana. Socket IP can be configured to connect this customer to Nirvana and merchants. Customer's socket is binded to port 5540.
        Merchant.py: Python code to emulate a merchant in Nirvana. Socket IP can be configured to connect this merchant to Nirvana and customers.
        Merchant_witness_distributed.py: Similar code to merchant.py with distributed witnesses. 
        NirvanaAuthorities.py: Python code to emulate Nirvana. Sockets are binded to ports 545, 5547, 5549 and 5546
        TSPS.py: Python code to emulate our proposed TSPS scheme for Nirvana
        Witness.py: Python code to emulate a witness located at a separate location in Nirvana. Its socket is binded to port 5585
        Witness_local.py: Python code to emulate a local witness in Nirvana
        script.bash: Bash script that can be used to run our distributed code locally for varying size of the merchant consortium
        secretshare.py: Python code for Shamir secret sharing
        
    contracts: Nirvana's smart contract
    
        NirvanaSecretPaymentChannel: Nirvana's smart contract for accepting customer deposits and remunerating victim merchants

