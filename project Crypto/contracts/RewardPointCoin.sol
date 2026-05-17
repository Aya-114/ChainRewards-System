// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface StoreRewardsAdmin {
    function getAdmin() external view returns (address);
}

contract RewardPointCoin {

    // ===== COIN INFO =====
    string public name     = "RewardPointCoin";
    string public symbol   = "RPC";
    uint8  public decimals = 0;
    uint   public totalSupply;

    // ===== ADMIN =====
    address public admin;
    address public storeRewardsContract;

    constructor() {
        admin = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == getAdmin(), "Not admin!");
        _;
    }

    function getAdmin() public view returns (address) {
        if (storeRewardsContract != address(0)) {
            return StoreRewardsAdmin(storeRewardsContract).getAdmin();
        }
        return admin;
    }

    function setStoreRewardsContract(address _storeRewardsContract) public {
        require(msg.sender == admin, "Only deployer admin can link core!");
        require(storeRewardsContract == address(0), "Core already linked!");
        require(_storeRewardsContract != address(0), "Invalid address!");
        storeRewardsContract = _storeRewardsContract;
    }

    function transferOwnership(address newAdmin) public onlyOwner {
        require(newAdmin != address(0), "Invalid address!");
        require(storeRewardsContract == address(0), "Use core transferOwnership!");
        admin = newAdmin;
    }

    // ===== BALANCES =====
    mapping(address => uint) public balanceOf;

    // ===== ALLOWANCES =====
    // owner => spender => amount
    mapping(address => mapping(address => uint)) public allowance;

    // ===== EVENTS =====
    event Transfer(address indexed from, address indexed to, uint amount);
    event Approval(address indexed owner, address indexed spender, uint amount);
    event Mint(address indexed to, uint amount);

    // ===== MINT =====
    function mint(address _to, uint _amount) public onlyOwner {
        require(_to != address(0), "Invalid address!");
        require(_amount > 0, "Amount must be > 0!");

        totalSupply        += _amount;
        balanceOf[_to]     += _amount;

        emit Mint(_to, _amount);
        emit Transfer(address(0), _to, _amount);
    }

    // ===== TRANSFER =====
    function transfer(address _to, uint _amount) public returns (bool) {
        require(_to != address(0), "Invalid address!");
        require(balanceOf[msg.sender] >= _amount, "Not enough coins!");
        require(_amount > 0, "Amount must be > 0!");

        balanceOf[msg.sender] -= _amount;
        balanceOf[_to]        += _amount;

        emit Transfer(msg.sender, _to, _amount);
        return true;
    }

    // ===== APPROVE =====
    // الـ user بيقول للـ contract: "مسموحلك تسحب X كوين مني"
    function approve(address _spender, uint _amount) public returns (bool) {
        require(_spender != address(0), "Invalid spender!");

        allowance[msg.sender][_spender] = _amount;

        emit Approval(msg.sender, _spender, _amount);
        return true;
    }

    // ===== TRANSFER FROM =====
    // الـ contract بتسحب من الـ user بعد ما عمل approve
    function transferFrom(address _from, address _to, uint _amount) public returns (bool) {
        require(_from != address(0), "Invalid from!");
        require(_to   != address(0), "Invalid to!");
        require(_amount > 0, "Amount must be > 0!");
        require(balanceOf[_from]               >= _amount, "Not enough coins!");
        require(allowance[_from][msg.sender]   >= _amount, "Allowance exceeded!");

        balanceOf[_from]             -= _amount;
        balanceOf[_to]               += _amount;
        allowance[_from][msg.sender] -= _amount;

        emit Transfer(_from, _to, _amount);
        return true;
    }
}
