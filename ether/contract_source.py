CONTRACT = """
pragma solidity ^0.4.20;

interface ERC165 {

    // Ensures a smart contract supports an interface
    function supportsInterface(bytes4 _interface) external view returns (bool);
    
}

interface ERC721TokenReceiver {
    // Handles the receipt of a Non-Fungible token
    function onERC721Received(address _operator, address _From, uint256 _token_id, bytes _data) 
            external returns(bytes4);
}

contract SupportsInterface is ERC165 {

    mapping(bytes4 => bool) internal supportedInterfaces;

    function SupportsInterface() public {
        supportedInterfaces[0x01ffc9a7] = true; // ERC165
    }

    function supportsInterface(bytes4 _interface) external view returns (bool) {
        return supportedInterfaces[_interface];
    }
}

interface ERC721 {
    // This event is emitted when a token is transferred to another address
    event Transfer(address indexed _from, address indexed _to, uint256 indexed _token_id);
    
    // This event is emitted when a the address is approved for trading
    event Approval(address indexed _owner, address indexed _approved, uint256 indexed _token_id);
    
    // Emitted when the owner approves or denies the operator to manage all tokens
    event ApprovalForAll(address indexed _owner, address indexed _operator, bool _approved);
    
    // Returns the number of tokens owned by the owner
    function balanceOf(address _owner) external view returns (uint256);
    
    // Returns the address of the owner of the given token
    function ownerOf(uint256 _token_id) external view returns (address);
    
    // Transfers the token from one address to another
    function safeTransferFrom(address _from, address _to, uint256 _token_id, bytes _data) external;
    
    // Same as function above, but does not contain optional bytes
    function safeTransferFrom(address _from, address _to, uint256 _token_id) external;
    
    // Unsafe transfer functionality - must ensure trade receipient is capable of receiving tokens
    function transferFrom(address _from, address _to, uint256 _token_id) external;
    
    // Sets the approved address for a token
    function approve(address _approved, uint256 _token_id) external;
    
    // Allows an operator to manage all of the senders assets
    function setApprovalForAll(address _operator, bool _approved) external;
    
    // Gets the approved user address for a token
    function getApproved(uint256 _token_id) external view returns (address);
    
    // Indicates whether the operator is permitted for operating the owner
    function isApprovedForAll(address _owner, address _operator) external view returns (bool);
}
    
contract issuer_contract is ERC721, SupportsInterface {

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
    string contract_uri;
    uint num_tokes;
    uint remaining_tokes;  // Holds the remaining # of tokens
    bool is_transferrable;
    
    // Constraints
    bytes6[] code_reqs;
    DateReq[] date_reqs;
    LocationReq[] loc_reqs;
    
    // Mappings
    mapping(uint256 => address) private token_owners;       // Holds owners of tokens
    mapping(uint256 => address) private approvals;          // Holds all approvals
    mapping(address => uint256) private owner_token_count;  // Holds the number of tokens owned
    mapping (address => mapping (address => bool)) private operators;  // Maps owners to operators
    mapping (uint256 => string) internal token_uri;         // Maps token_id to a token_uri
    
    // This event is emitted when a token is transferred to another address
    event Transfer(address indexed _from, address indexed _to, uint256 indexed _token_id);
    
    // This event is emitted when a the address is approved for trading
    event Approval(address indexed _owner, address indexed _approved, uint256 indexed _token_id);
    
    // Emitted when the owner approves or denies the operator to manage all tokens
    event ApprovalForAll(address indexed _owner, address indexed _operator, bool _approved);
    
    // Modifier requiring that the sender has rights to make actions on this token
    modifier can_operate(uint256 _token_id) {
        address token_owner = token_owners[_token_id];
        require(token_owner == msg.sender || operators[token_owner][msg.sender] || owner == msg.sender
            || root_acct == msg.sender);
        _;
    }
    
    // Modifier requiring the sender has rights to transfer the token
    modifier can_transfer(uint256 _token_id) {
        address token_owner = token_owners[_token_id];
        require((token_owner == msg.sender || approvals[_token_id] == msg.sender || operators[token_owner][msg.sender]
            || owner == msg.sender || root_acct == msg.sender) && is_transferrable);
        _;
    }

    // Requires that the given token is valid
    modifier valid_token(uint256 _token_id) {
        require(token_owners[_token_id] != address(0));
        _;
    }

    // Constructor
    function issuer_contract(address _owner, string _in, string _cn, string _ts, string _cd, 
            string _iu, uint256 _it, bytes6[] _codes, uint[] _dates, int256[] _locs, bool _can_transfer, 
            string _contract_uri) public {
                
        supportedInterfaces[0x80ac58cd] = true; // ERC721
        supportedInterfaces[0x5b5e139f] = true; // ERC721Metadata
        
        // Set attributes
        issuer_name = _in;
        contract_name = _cn;
        contract_symbol = _ts;
        contract_description = _cd;
        img_url = _iu;
        remaining_tokes = _it;
        num_tokes = _it;
        is_transferrable = _can_transfer;
        contract_uri = _contract_uri;
        
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
    
    /* ERC721 Required Functions */
    
    // Returns the number of tokens owned by this user
    function balanceOf(address _owner) external view returns (uint256) {
        require(_owner != address(0));
        return owner_token_count[_owner];
    }
    
    // Returns the owner of the given token
    function ownerOf(uint256 _token_id) external view returns (address _owner) {
        _owner = token_owners[_token_id];
        require(_owner != address(0));
    }
    
    // Transfers ownership of tokens to and from the given addresses
    function safeTransferFrom(address _from, address _to, uint256 _token_id, bytes _data) external {
        _safe_transfer_from(_from, _to, _token_id, _data);
    }
    
    // Transfers ownership of tokens to and from the given addresses without _data
    function safeTransferFrom(address _from, address _to, uint256 _token_id) external {
        _safe_transfer_from(_from, _to, _token_id, "");
    }
    
    // Does an unsafe transfer 
    function transferFrom(address _from, address _to, uint256 _token_id) external can_transfer(_token_id) 
            valid_token(_token_id) {
        address token_owner = token_owners[_token_id];
        require(token_owner == _from);
        require(_to != address(0));
        _transfer(_to, _token_id);
    }
    
    // Approves the given address to manage the given token
    function approve(address _approved, uint256 _token_id) external can_operate(_token_id) valid_token(_token_id) {
        address token_owner = token_owners[_token_id];
        require(_approved != token_owner);
        approvals[_token_id] = _approved;
        emit Approval(token_owner, _approved, _token_id);
    }
    
    // Approves operator to manage all of the senders assets
    function setApprovalForAll(address _operator, bool _approved) external {
        require(_operator != address(0));
        operators[msg.sender][_operator] = _approved;
        emit ApprovalForAll(msg.sender, _operator, _approved);
    }
    
    // Gets a token's approved address
    function getApproved(uint256 _token_id) external view returns (address) {
        return approvals[_token_id];
    }

    // Returns true if the operator is a valid operator for the owner
    function isApprovedForAll(address _owner, address _operator) external view returns (bool) {
        require(_owner != address(0));
        require(_operator != address(0));
        return operators[_owner][_operator];
    }
    
    // Performs the safe transfer from function
    function _safe_transfer_from(address _from, address _to, uint256 _token_id, bytes _data) 
            internal can_transfer(_token_id) valid_token(_token_id) {
        address token_owner = token_owners[_token_id];
        require(token_owner == _from);
        require(_to != address(0));

        _transfer(_to, _token_id);
        
        uint256 size;
        assembly { size := extcodesize(_to) }

        if (size > 0) {
            bytes4 val = ERC721TokenReceiver(_to).onERC721Received(msg.sender, _from, _token_id, _data);
            require(val == 0x150b7a02);  // Indicates the contract can receive tokens
        }
    }
    
    // Performs the transfer
    function _transfer(address _to, uint256 _token_id) private {
        address from = token_owners[_token_id];
        clear_approval(_token_id);

        remove_token_from_owner(from, _token_id);
        add_token_to_owner(_to, _token_id);

        emit Transfer(from, _to, _token_id);
    }
    
    // Mints a new token and sends it to an account
    function mint_and_send(address _to, uint256 _token_id, string _token_uri) public {
        require(_to != address(0));
        require(_token_id != 0);
        require(token_owners[_token_id] == address(0));
        
        num_tokes += 1;
        add_token_to_owner(_to, _token_id);
        if (bytes(_token_uri).length != 0) {
            token_uri[_token_id] = _token_uri;
        }

        emit Transfer(address(0), _to, _token_id);
    }
    
    // Mints a new token
    function mint(uint256 _token_id, string _token_uri) public {
        require(_token_id != 0);
        require(token_owners[_token_id] == address(0));
        
        num_tokes += 1;
        remaining_tokes += 1;
        if (bytes(_token_uri).length != 0) {
            token_uri[_token_id] = _token_uri;
        }
    }
    
    // Removes the approval for a token
    function clear_approval(uint256 _token_id) private {
        if(approvals[_token_id] != 0) {
            delete approvals[_token_id];
        }
    }
    
    // Removes token from owner
    function remove_token_from_owner(address _from, uint256 _token_id) internal {
        require(token_owners[_token_id] == _from);
        assert(owner_token_count[_from] > 0);
        owner_token_count[_from] = owner_token_count[_from] - 1;
        delete token_owners[_token_id];
    }
    
    // Add token to owner
    function add_token_to_owner(address _to, uint256 _token_id) internal {
        require(token_owners[_token_id] == address(0));

        token_owners[_token_id] = _to;
        owner_token_count[_to] = owner_token_count[_to] + 1;
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
    
    // Returns the tokenURI for the token metadata
    function tokenURI(uint256 _token_id) valid_token(_token_id) external view returns (string) {
        if (bytes(token_uri[_token_id]).length != 0) {
            return token_uri[_token_id];
        }
        return contract_uri;
    }
    
    // Function to transfer from creator to another user
    function sendToken(address _to, uint256 _token_id, bytes6 code, uint date) public {
        address newOwner = _to;
        require((msg.sender == owner) || (msg.sender == root_acct));  // Make sure sender is the creator
        require(owner != newOwner);                                   // Make sure the creator isn't sending to self
        require(newOwner != address(0));                              // Make sure new owner isn't address 0
        require(token_owners[_token_id] == address(0));               // Make sure token isn't already owned
        require(remaining_tokes > 0);                                 // Make sure there are tokens left
        require(code_permitted(code));                                // Make sure the code is permitted
        require(date_permitted(date));                                // Make sure the date is permitted
        remaining_tokes -= 1;                                         // Decrement the remaining tokens
        add_token_to_owner(_to, _token_id);                           // Set the tokens owner
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

DEFAULT_JSON_METADATA = """
{{
   “name”: {name},
   “description”: {description},
   “image”: {img_loc} 
}}
"""