
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// ربط الكوين — أضفنا transferFrom عشان نحول من wallet الـ user مباشرة
interface IRewardPointCoin {
    function balanceOf(address user) external view returns (uint);
    function transfer(address to, uint amount) external returns (bool);
    function transferFrom(address from, address to, uint amount) external returns (bool);
}

contract StoreRewards {

    // ===== ADMIN =====
    address public admin;

    constructor(address _coinAddress) {
        admin = msg.sender;
        coin = IRewardPointCoin(_coinAddress);
    }

    modifier onlyOwner() {
        require(msg.sender == admin, "Not admin!");
        _;
    }

    function getAdmin() public view returns (address) {
        return admin;
    }

    function transferOwnership(address newAdmin) public onlyOwner {
        require(newAdmin != address(0), "Invalid address!");
        admin = newAdmin;
    }

    // ===== PAUSE =====
    bool public paused = false;

    modifier whenNotPaused() {
        require(!paused, "Paused!");
        _;
    }

    function pause() public onlyOwner {
        paused = true;
    }

    function resume() public onlyOwner {
        paused = false;
    }

    // ===== LINK TO COIN =====
    IRewardPointCoin public coin;

    // ===== USER REGISTRATION =====
    mapping(address => string) public userNames;
    mapping(address => bool)   public isRegistered;

    event UserRegistered(address indexed user, string name);

    function registerUser(string memory _name) public whenNotPaused {
        require(!isRegistered[msg.sender], "Already registered!");
        require(bytes(_name).length > 0, "Name cannot be empty!");

        userNames[msg.sender]   = _name;
        isRegistered[msg.sender] = true;

        emit UserRegistered(msg.sender, _name);
    }

    function getUserName(address _user) public view returns (string memory) {
        return userNames[_user];
    }

    // ===== REWARDS =====
    struct Reward {
        uint id;
        string name;
        uint cost;
        bool exists;
    }

    uint public rewardCount;
    mapping(uint => Reward) public rewards;

    // ===== EVENTS =====
    event RewardAdded(uint id, string name, uint cost);
    event RewardUpdated(uint id, string name, uint cost);
    event RewardPurchased(address indexed user, uint id, uint cost);

    // ===== ADD =====
    function addReward(string memory _name, uint _cost)
        public onlyOwner whenNotPaused
    {
        require(bytes(_name).length > 0, "Empty name!");
        require(_cost > 0, "Invalid cost!");

        rewardCount++;
        rewards[rewardCount] = Reward(rewardCount, _name, _cost, true);

        emit RewardAdded(rewardCount, _name, _cost);
    }

    // ===== UPDATE =====
    function updateReward(uint _id, string memory _name, uint _cost)
        public onlyOwner whenNotPaused
    {
        require(rewards[_id].exists, "Not found!");
        require(_cost > 0, "Invalid cost!");

        rewards[_id].name = _name;
        rewards[_id].cost = _cost;

        emit RewardUpdated(_id, _name, _cost);
    }

    // ===== BATCH ADD =====
    function batchAddRewards(
        string[] memory _names,
        uint[] memory _costs
    ) public onlyOwner whenNotPaused {

        require(_names.length == _costs.length, "Mismatch!");

        for (uint i = 0; i < _names.length; i++) {
            require(bytes(_names[i]).length > 0, "Empty name!");
            require(_costs[i] > 0, "Invalid cost!");

            rewardCount++;
            rewards[rewardCount] = Reward(
                rewardCount,
                _names[i],
                _costs[i],
                true
            );

            emit RewardAdded(rewardCount, _names[i], _costs[i]);
        }
    }

    // ===== BATCH UPDATE =====
    function batchUpdateRewards(
        uint[] memory _ids,
        string[] memory _names,
        uint[] memory _costs
    ) public onlyOwner whenNotPaused {

        require(_ids.length == _names.length, "Mismatch!");
        require(_ids.length == _costs.length, "Mismatch!");

        for (uint i = 0; i < _ids.length; i++) {
            require(rewards[_ids[i]].exists, "Not found!");
            require(bytes(_names[i]).length > 0, "Empty name!");
            require(_costs[i] > 0, "Invalid cost!");

            rewards[_ids[i]].name = _names[i];
            rewards[_ids[i]].cost = _costs[i];

            emit RewardUpdated(_ids[i], _names[i], _costs[i]);
        }
    }

    // ===== BUY — مصلّح =====
    // الـ user لازم يعمل approve الأول من Python:
    //   coin.functions.approve(core_address, cost).transact({"from": user})
    // وبعدين يكال buyReward — الـ contract هتسحب منه مباشرة
    function buyReward(uint _id) public whenNotPaused {
        require(rewards[_id].exists, "Not found!");

        uint cost = rewards[_id].cost;

        require(
            coin.balanceOf(msg.sender) >= cost,
            "Not enough coins!"
        );

        // transferFrom: من wallet الـ user للـ admin مباشرة
        bool ok = coin.transferFrom(msg.sender, admin, cost);
        require(ok, "Transfer failed!");

        emit RewardPurchased(msg.sender, _id, cost);
    }

    // ===== GET =====
    function getReward(uint _id)
        public view returns (string memory, uint)
    {
        require(rewards[_id].exists, "Not found!");
        return (rewards[_id].name, rewards[_id].cost);
    }
}
