CONTRACT = """
pragma solidity ^0.4.0;
    
contract issuer_contract {

    // Structs
    struct DateReq {
        uint start_date;
        uint end_date;
    }
    
    struct LocationReq {
        int256 latitude;
        int256 longitude;
        int256 radius;
    }
    
    // Address of the contract owner
    address owner;
    address root_acct;  // Account that funds transactions
    
    // Contract members
    string issuer_name;
    string contract_name;
    string contract_symbol;
    string contract_description;
    string img_url;
    uint num_tokes;
    uint remaining_tokes;  // Holds the remaining # of tokens
    
    // Constraints
    bytes6[] code_reqs;
    DateReq[] date_reqs;
    LocationReq[] loc_reqs;
    
    
    // Mappings
    mapping(uint256 => address) private token_owners;  // Holds owners of tokens
    mapping(address => bool) private owns_token;       // Holds whether a user owns a token
    mapping(address => uint256) private owners_token;  // Holds the token owned by a user

    // Constructor
    function issuer_contract(address _owner, string _in, string _cn, string _ts, string _cd, 
            string _iu, uint256 _it, bytes6[] _codes, uint[] _dates, int256[] _locs) public {
        // Set attributes
        issuer_name = _in;
        contract_name = _cn;
        contract_symbol = _ts;
        contract_description = _cd;
        img_url = _iu;
        remaining_tokes = _it;
        num_tokes = _it;
        
        // Set the requirements
        code_reqs = _codes;
        
        // Populate the date and location requirements
        uint num_dates = _dates.length;
        for(uint i = 0; i < num_dates; i += 2){
            date_reqs.push(DateReq(_dates[i], _dates[i + 1]));
        }
        uint num_locs = _locs.length;
        for(i = 0; i < num_locs; i += 3) {
            loc_reqs.push(LocationReq(_locs[i], _locs[i + 1], _locs[i + 2]));
        }
    
        // Set the owner and root account of the contract 
        owner = _owner; 
        root_acct = msg.sender;
    }
    
    /* GETTERS AND SETTERS */
    
    // Function to get issuer_name
    function issuerName() public view returns (string) {
        return issuer_name;
    }
    
    // Function to get contract name
    function name() public view returns (string) {
        return contract_name;
    }
    
    // Function to return the token's symbol
    function symbol() public view returns (string) {
        return contract_symbol;
    }
    
    // Function to get description
    function description() public view returns (string) {
        return contract_description;
    }
    
    // Function to get image URL
    function imageURL() public view returns (string) {
        return img_url;
    }
    
    // Function to get the number of tokens
    function totalSupply() public view returns (uint) {
        return num_tokes;
    }
    
    // Function to get the remaining # of tokens
    function remainingTokens() public view returns (uint) {
        return remaining_tokes;
    }
    
    // Function to determine if a user owns a token 
    function ownsToken(address _user) public view returns (bool) {
        return owns_token[_user];
    }
    
    // Function to get a user's token_id
    function getUsersToken(address _user) public view returns (uint256) {
        return owners_token[_user];
    }
    
    // Function to get a user from a token_id
    function getUserFromTokenID(uint _token_id) public view returns (address) {
        return token_owners[_token_id];
    }
    
    // Gets the number of date ranges set
    function num_dates() public view returns (uint) {
        return date_reqs.length;
    }
    
    // Gets the date range at the given date index
    function get_date_range(uint index) public view returns (uint, uint) {
        DateReq storage date = date_reqs[index];
        return (date.start_date, date.end_date);
    }
    
    // Gets the number of code requirements
    function num_codes() public view returns (uint) {
        return code_reqs.length;
    }
    
    // Gets the code at the given index
    function get_code(uint index) public view returns (bytes6) {
        return code_reqs[index];
    }
    
    // Gets the number of location requirements
    function num_locations() public view returns (uint) {
        return loc_reqs.length;
    }
    
    // Gets the location at the given index as (lat, long, radius)
    function get_location(uint index) public view returns (int256, int256, int256) {
        LocationReq storage loc = loc_reqs[index];
        return (loc.latitude, loc.longitude, loc.radius);
    }
    
    // Function to transfer from creator to another user
    function sendToken(address _to, uint256 _tokenId, bytes6 code, uint date) public {
        address newOwner = _to;
        require((msg.sender == owner) || (msg.sender == root_acct));  // Make sure sender is the creator
        require(owner != newOwner);                                  // Make sure the creator isn't sending to self
        require(newOwner != address(0));                             // Make sure new owner isn't address 0
        require(token_owners[_tokenId] == address(0));               // Make sure token isn't already owned
        require(owns_token[newOwner] == false);                      // Make sure new owner doesn't own a token
        require(remaining_tokes > 0);                                // Make sure there are tokens left
        require(code_permitted(code));                               // Make sure the code is permitted
        require(date_permitted(date));                               // Make sure the date is permitted
        remaining_tokes -= 1;                                        // Decrement the remaining tokens
        token_owners[_tokenId] = newOwner;                           // Set the tokens owner
        owners_token[newOwner] = _tokenId;                           // Set the owners token
        owns_token[newOwner] = true;                                 // Set that the user owns a token
    }
    
    // Function to ensure that the date is within the permitted dates
    function date_permitted(uint date) private view returns(bool) {
        if (date_reqs.length == 0)
            return true;
        
        uint date_length = date_reqs.length;
        for (uint i = 0; i < date_length; i++) {
            DateReq storage check_date = date_reqs[i];
            if (check_date.start_date < date && date < check_date.end_date)
                return true;
        }
        return false;
    }
    
    // Function to ensure that the code is one of the permitted codes
    function code_permitted(bytes6 code) private view returns (bool) {
        if (code_reqs.length == 0)
            return true;
            
        uint code_len = code_reqs.length;
        for (uint i = 0; i < code_len; i++) {
            if (code_reqs[i] == code)
                return true;
        }
        return false;
    }

    // Function to recover the funds on the contract
    function kill() public {
        if ((msg.sender == owner) || (msg.sender == root_acct)) {
            selfdestruct(root_acct);
            selfdestruct(owner);
        }
    }
}
"""