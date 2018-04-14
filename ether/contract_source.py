CONTRACT = """
pragma solidity ^0.4.0;
    
contract issuer_contract {
    // Address of the contract owner
    address owner;
    
    // Contract members
    string issuer_name;
    string contract_name;
    string contract_symbol;
    string contract_description;
    string img_url;
    uint num_tokes;
    uint remaining_tokes;  // Holds the remaining # of tokens
    
    // Mappings
    mapping(uint256 => address) private token_owners;  // Holds owners of tokens
    mapping(address => bool) private owns_token;       // Holds whether a user owns a token
    mapping(address => uint256) private owners_token;  // Holds the token owned by a user

    // Constructor
    function issuer_contract(string _in, string _cn, string _ts, string _cd, 
            string _iu, uint256 _it) {
        // Set attributes
        issuer_name = _in;
        contract_name = _cn;
        contract_symbol = _ts;
        contract_description = _cd;
        img_url = _iu;
        remaining_tokes = _it;
        num_tokes = _it;
    
        // Set the owner of the contract 
        owner = msg.sender; 
    }
    
    /* GETTERS AND SETTERS */
    
    // Function to get issuer_name
    function issuerName() constant returns (string) {
        return issuer_name;
    }
    
    // Function to get contract name
    function name() constant returns (string) {
        return contract_name;
    }
    
    // Function to return the token's symbol
    function symbol() constant returns (string) {
        return contract_symbol;
    }
    
    // Function to get description
    function description() constant returns (string) {
        return contract_description;
    }
    
    // Function to get image URL
    function imageURL() constant returns (string) {
        return img_url;
    }
    
    // Function to get the number of tokens
    function totalSupply() constant returns (uint) {
        return num_tokes;
    }
    
    // Function to get the remaining # of tokens
    function remainingTokens() constant returns (uint) {
        return remaining_tokes;
    }
    
    // Function to determine if a user owns a token 
    function ownsToken(address _user) constant returns (bool) {
        return owns_token[_user];
    }
    
    // Function to get a user's token_id
    function getUsersToken(address _user) constant returns (uint256) {
        return owners_token[_user];
    }
    
    // Function to transfer from creator to another user
    function sendToken(address _to, uint256 _tokenId) public {
        address newOwner = _to;
        require(msg.sender == owner);                   // Make sure sender is the creator
        require(owner != newOwner);                     // Make sure the creator isn't sending to self
        require(newOwner != address(0));                // Make sure new owner isn't address 0
        require(token_owners[_tokenId] == address(0));  // Make sure token isn't already owned
        require(owns_token[newOwner] == false);         // Make sure new owner doesn't own a token
        require(remaining_tokes > 0);                   // Make sure there are tokens left
        remaining_tokes -= 1;                           // Decrement the remaining tokens
        token_owners[_tokenId] = newOwner;              // Set the tokens owner
        owners_token[newOwner] = _tokenId;              // Set the owners token
        owns_token[newOwner] = true;                    // Set that the user owns a token
    }

    // Function to recover the funds on the contract
    function kill() {
        if (msg.sender == owner) 
            suicide(owner); 
    }
}
"""