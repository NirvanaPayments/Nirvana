pragma solidity 0.8.0;
//pragma experimental ABIEncoderV2;

/*
SPDX-License-Identifier: UNLICENSED
*/
/**
* @title NirvanaSecretPaymentChannel
* @dev Accept customer deposits and allow merchant withdrawals. As an example, a customer is allowed to deposit 1 ether per collateral.
*/
contract NirvanaSecretPaymentChannel {

address owner;
address[] merchants_in_network;
uint256 min_deposit_amount = 1 ether;
 
struct Customer{
    bool exists;
    uint256 customer_collateral;
    uint256 total_collaterals_requested;
    mapping(uint256 => bytes32) payments; 
}

struct Merchant{
    bool exists;
    uint256 claim_amount;
}

mapping(address => Customer) public customers;
mapping(address => Merchant) public merchants; 
 
constructor () {
    owner = msg.sender;
 
}
 
modifier onlyOwner { require(msg.sender == owner, 'Only Nirvana authorities can call this function.'); _;}
 
event CustomerRegistered(address _from, uint _collateral);
event CollateralRedeemed(string _redeemed);
event RemuneratedMerchant(address _from, uint balance);
event RevokedCustomer(address _customer, uint balance); 
 
function registerCustomer(bytes32[] memory secret_hashes, uint256 total_requests) public payable{
    require(msg.value/total_requests == min_deposit_amount, 'Please put the correct deposit amount!');
    emit CustomerRegistered(msg.sender, msg.value);
    for(uint i=0; i<total_requests; i++){
        customers[msg.sender].payments[i] = secret_hashes[i]; 
    }
    customers[msg.sender].customer_collateral = msg.value;
    customers[msg.sender].exists = true;
    customers[msg.sender].total_collaterals_requested = total_requests;
}
 
function add_merchants(address[] memory _merchantAddresses) public onlyOwner{
    merchants_in_network = _merchantAddresses;
    for(uint i=0; i<_merchantAddresses.length; i++){
        merchants[merchants_in_network[i]].exists = true;
    }
}
 
function claim_payment(address cheating_customer, string[] memory preimages) public{
    require(merchants[msg.sender].exists== true, 'You are not a merchant in the Nirvana network.');
    require(customers[cheating_customer].customer_collateral > 0, "Customer has no collateral left..!");
    for(uint i=0;i<customers[cheating_customer].total_collaterals_requested;i++){
        for(uint j=0;j<preimages.length;j++){
            bytes32 hash_preimage = keccak256(abi.encodePacked(preimages[j]));
            if(customers[cheating_customer].payments[i] == hash_preimage){
                uint256 amount_per_secret = customers[cheating_customer].customer_collateral / customers[cheating_customer].total_collaterals_requested;
                merchants[msg.sender].claim_amount += amount_per_secret;
                customers[cheating_customer].customer_collateral -= amount_per_secret;
                amount_per_secret = 0;
                customers[cheating_customer].total_collaterals_requested -= 1;
                delete customers[cheating_customer].payments[i];
            }
            else{
                emit CollateralRedeemed('collateral already redeemed');
                break;
            }
        }
    }
}


function remunerate_merchant() public{
    require(merchants[msg.sender].exists == true, 'You are not a merchant in the Nirvana network.');
    address merchant_to_remunerate = msg.sender;
    uint amount_to_transfer = merchants[merchant_to_remunerate].claim_amount;
    merchants[merchant_to_remunerate].claim_amount=0;
    payable(merchant_to_remunerate).transfer(amount_to_transfer); 
    emit RemuneratedMerchant(msg.sender, amount_to_transfer);
}

function revoke_collateral(address payable leaving_customer) public onlyOwner{
    require(customers[leaving_customer].exists == true, 'Customer does not have any deposit in Nirvana network.');
    uint amount_to_transfer = customers[leaving_customer].customer_collateral;
    customers[leaving_customer].customer_collateral = 0;
    customers[leaving_customer].total_collaterals_requested -= 1;
    leaving_customer.transfer(amount_to_transfer);
    emit RevokedCustomer(leaving_customer, amount_to_transfer);
    
}
 
}
