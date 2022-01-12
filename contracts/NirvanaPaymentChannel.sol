pragma solidity >=0.4.22 <0.9.0;

/*
SPDX-License-Identifier: UNLICENSED
*/
/**
* @title Nirvana
* @dev Accept customer deposits and allow merchant withdrawals. A customer is allowed to deposit 100 milliether per collateral.
*/
contract NirvanaPaymentChannel{

uint256 p_nonce; //indicates payment nonce. Used by Customers to make multiple payments to merchants. 
 //uint256 secrets_required;
address owner;
address payable[] merchants_in_network;
 
struct Customer{
    bool exists;
    uint256 customer_collateral;
    uint256 duration;
    //bytes32[] secret_hashes;
}

struct Merchant{
    bool exists;
    uint256 earnings;
}
mapping(address => Customer) public customers;
mapping(address => Merchant) public merchants; 
 
constructor () public {
    owner = msg.sender;
 
}
 
modifier onlyOwner { require(msg.sender == owner, 'Only Nirvana can call this function.'); _;}
 

 
 
function registerCustomer() public payable{
    //secrets_required = (msg.value/1000000000000000000);
    //require(secrets.length == secrets_required, 'Not enough secrets for deposited collateral!');
    customers[msg.sender].customer_collateral = msg.value;
    customers[msg.sender].exists = true;
    customers[msg.sender].duration = block.timestamp; 
    //customers[msg.sender].secret_hashes = secrets;
    //secrets_required = 0;
}
 
function add_merchants(address payable[] memory _merchantAddresses) public onlyOwner{
    merchants_in_network = _merchantAddresses;
    for(uint i=0; i<merchants_in_network.length; i++){
        merchants[merchants_in_network[i]].exists = true;
        merchants[merchants_in_network[i]].earnings = 0;
    }
}
 
function claim_payment(uint256 amount, uint8 v, bytes32 r, bytes32 s, address cheating_customer) public{
    require(merchants[msg.sender].exists == true, 'You are not a merchant in the Nirvana network.');
    require(isSignatureValid(amount, v, r, s, cheating_customer), "Wrong customer signature.");
    customers[cheating_customer].customer_collateral -= amount;
    merchants[msg.sender].earnings += amount;
    payable(msg.sender).transfer(amount);
}


/*
function isValidSignature(uint256 amount, bytes memory signature, address cheater)
internal
view
returns (bool)
{
    bytes32 message = prefixed(keccak256(abi.encodePacked(this, amount)));
    // check that the signature is from the payment sender
    return recoverSigner(message, signature) == cheater;
}
 
 
function splitSignature(bytes memory sig)
internal
pure
returns (uint8 v, bytes32 r, bytes32 s)
{
    require(sig.length == 65);

    assembly {
        // first 32 bytes, after the length prefix
        r := mload(add(sig, 32))
        // second 32 bytes
        s := mload(add(sig, 64))
       // final byte (first byte of the next 32 bytes)
        v := byte(0, mload(add(sig, 96)))
    }

return (v, r, s);
}

function recoverSigner(bytes32 message, bytes memory sig)
internal
pure
returns (address)
{
    (uint8 v, bytes32 r, bytes32 s) = splitSignature(sig);

    return ecrecover(message, v, r, s);
}

function prefixed(bytes32 hash) internal pure returns (bytes32) {
    return keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", hash));
}
*/

function isSignatureValid(uint256 amount, uint8 v, bytes32 r, bytes32 s, address _customer) view public returns(bool correct) {
        bytes32 mustBeSigned = prefixHash(amount);
        address signer = ecrecover(mustBeSigned, v, r, s);
        
        return(signer == _customer);
    }
 /// builds a prefixed hash to mimic the behavior of eth_sign.

function prefixHash(uint256 _amount) internal view returns(bytes32) {
        bytes32 hash = keccak256(abi.encodePacked(address(this), _amount));
        return hash;
    }
 
}