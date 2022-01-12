pragma solidity >=0.4.22 <0.7.0;

/*
SPDX-License-Identifier: UNLICENSED
*/
/**
 * @title Nirvana
 * @dev Accept customer deposits and allow merchant withdrawals
 */
contract Nirvana {

    uint256 p_nonce;    //indicates payment nonce. Used by Customers to make multiple payments to merchants. 
    
    struct Customer{
        bool exists;
        uint256 customer_collateral;
    }
    
    mapping(address => Customer) public customers;
    
    function registerCustomer() public payable{
        //require(customers(msg.sender).exists == false);
        customers[msg.sender].customer_collateral = msg.value;
        customers[msg.sender].exists = true;
    }
    
    
    struct Merchant{
        //address merchant_address;
        bool  exists;
        uint256 payment_nonce;                      //identifier for each individual payment
        uint256[] merchant_payment;                 //Array of payments to a merchant. Each individual payment can be accessed using payment_nonce 
        bytes32[] secrets_for_payment;              //Array of secrets to obtain each individual payment. Each unique nonce links 1 payment to 1 secret
        uint256 merchant_balance;                   //Total balance of merchant
        uint256[] payment_time;                     //Recieving time of each unique payment. This is used by customer to reclaim their undisputed payments to merchant.
    }
    
    mapping(address => Merchant) public merchants;
    
    constructor() public{
        p_nonce = 0;                                //Instantiating value of payment nonce to 0 for each new merchant
    }
    
    function deposit_collateral() public payable{
        require(customers[msg.sender].exists == true, 'Register yourself first');
        customers[msg.sender].customer_collateral += msg.value;
    }
    
    
    /*
    This function is called by the customer to make a payment, or many payments to a merchant. We first check if the merchant already exists (If condition) or not (Else). If they do, 
    we push the new secret and accompanied payments in their respective arrays. If they don't, we use p_nonce (always 0), to make the first entry in the secret and payment arrays. 
    We always increment this payment nonce whenever a payment is made to an existing merchant. 
    */
    function pay_merchant(bytes32 secret_hash, uint amount, address merchant_to_pay) public{
        require(customers[msg.sender].customer_collateral >= amount, 'not enough collateral to pay merchant');
        if(merchants[merchant_to_pay].exists == true){
            merchants[merchant_to_pay].secrets_for_payment.push(secret_hash);
            merchants[merchant_to_pay].merchant_payment.push(amount);
            merchants[merchant_to_pay].payment_time.push(block.timestamp);
            merchants[merchant_to_pay].payment_nonce++;
            customers[msg.sender].customer_collateral -= amount;
        }
        else{
        merchants[merchant_to_pay].exists = true;
        merchants[merchant_to_pay].secrets_for_payment.push(secret_hash);
        merchants[merchant_to_pay].merchant_payment.push(amount); 
        merchants[merchant_to_pay].payment_time.push(block.timestamp);
        merchants[merchant_to_pay].payment_nonce = p_nonce; 
        //merchants[merchant_to_pay].merchant_balance += amount; 
        customers[msg.sender].customer_collateral -= amount;
        }
    }
    
    /*
    Using this function, a victim merchant can claim his lost money. Once the customer cheats, the victim merchant gains access to the preimage of the secret hash, which can be provided
    as a parameter to this function, namely, secret_link_payment. The victim merchant also needs to provide the payment_nonce of the disputed payment. 
    Once the merchant claims his money, his balance is incremented to reflect the amount in dispute.
    */
    
    function merchant_claim_payment(string memory secret_link_payment, uint256 nonce) public{
        //bytes32 hashed_secret = keccak256(abi.encodePacked(secret_link_payment));
        require(merchants[msg.sender].secrets_for_payment[nonce] == keccak256(abi.encodePacked(secret_link_payment)), 'Invalid Secret');
        merchants[msg.sender].merchant_balance += merchants[msg.sender].merchant_payment[nonce]; 
        merchants[msg.sender].merchant_payment[nonce] = 0; 
    }
    
    
    /*
    Using this function, the merchant can withdraw their final balance AFTER claiming all disputed payments. 
    Once withdrawal is successful, that merchant is deleted from this contract.   
    */
    
    
    function merchant_withdraw_funds() public{
        require(merchants[msg.sender].exists == true, 'You do not have any balance to claim');
        uint amount_to_transfer = merchants[msg.sender].merchant_balance;
        merchants[msg.sender].merchant_balance=0;
        //merchants[msg.sender].exists = false; 
        //delete(merchants[msg.sender]);
        msg.sender.transfer(amount_to_transfer);
    }
    
    /*
    This function removes the merchant entry from the merchants mapping. This is done in order to start new payments for the merchant 
    with payment nonce 0.
    */

    function remove_merchant() public{
        assert(merchants[msg.sender].exists == true);
        uint totalRemainingBalance;
        for(uint i=0; i<merchants[msg.sender].merchant_payment.length; i++){
            totalRemainingBalance += merchants[msg.sender].merchant_payment[i];
        }
        require(totalRemainingBalance == 0, 'You still have pending payments, revoking yourself will lead to losing access to those payments.');
        require(merchants[msg.sender].merchant_balance == 0, 'You still have to claim your balance. Revoking yourself will remove that balance.');
        merchants[msg.sender].exists = false; 
        delete(merchants[msg.sender]);
    }
    
    /*
    This function allows a customer to claim their payment back after 1 day. Since Nirvana guarantees payments after 1 latency period of the underlying
    blockchain, 1 day is enough time for a victim merchant to reclaim their disputed payment. 
    If 1 day passes and the customer reclaims their payment, the merchant's payment at that specific nonce becomes 0. However, other disputed payments
    are still reclaimable.
     */

    function claim_payment_customer(address merchant_paid, uint256 nonce_to_claim) public{
        require(merchants[merchant_paid].exists == true, 'Merchant does not exist.');
        require(block.timestamp >= merchants[merchant_paid].payment_time[nonce_to_claim] + 1 days, 'Not so fast, give merchant enough time to receive money.');
        uint256 amount = merchants[merchant_paid].merchant_payment[nonce_to_claim];
        merchants[merchant_paid].merchant_payment[nonce_to_claim] = 0;
        customers[msg.sender].customer_collateral += amount;
    }
    
    /**
    This function enables a customer to withdraw their collateral in Nirvana back to their Ethereum account, since Nirvana holds no custody.
     */

    function customer_withdraw_funds() public{
        require(customers[msg.sender].exists == true, 'You do not have any balance to claim');
        require(customers[msg.sender].customer_collateral > 0, 'You do not have any balance to claim');
        uint amount_to_transfer = customers[msg.sender].customer_collateral;
        customers[msg.sender].customer_collateral=0;
        //merchants[msg.sender].exists = false; 
        //delete(merchants[msg.sender]);
        msg.sender.transfer(amount_to_transfer);
    }
    

    /**
    This function removes a customer from Nirvana environment. This is only done after the collateral is successfully withdrawn by the customer.
     */

    function remove_customer() public{
        assert(customers[msg.sender].exists == true);
        require(customers[msg.sender].customer_collateral == 0, 'You still have to claim your balance. Revoking yourself will remove that balance.');
        customers[msg.sender].exists = false; 
        delete(customers[msg.sender]);
    }
    
}