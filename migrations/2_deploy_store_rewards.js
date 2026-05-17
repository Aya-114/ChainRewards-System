const fs = require("fs");
const path = require("path");

const RewardPointCoin = artifacts.require("RewardPointCoin");
const StoreRewards = artifacts.require("StoreRewards");

module.exports = async function (deployer, network, accounts) {
  const admin = accounts[0];
  const user1 = accounts[1];
  const user2 = accounts[2];

  await deployer.deploy(RewardPointCoin, { from: admin });
  const coin = await RewardPointCoin.deployed();

  await deployer.deploy(StoreRewards, coin.address, { from: admin });
  const core = await StoreRewards.deployed();

  await coin.setStoreRewardsContract(core.address, { from: admin });

  const rewards = [
    ["Free Coffee", 10],
    ["10% Discount", 25],
    ["Free Shipping", 15],
    ["Gift Card", 50],
    ["Free Sandwich", 30],
  ];

  for (const [name, cost] of rewards) {
    await core.addReward(name, cost, { from: admin });
  }

  await coin.mint(user1, 100, { from: admin });
  await coin.mint(user2, 50, { from: admin });

  const addressFile = path.join(__dirname, "..", "project Crypto", "contract_addresses.txt");
  const contents = [
    `CORE_ADDRESS=${core.address}`,
    `COIN_ADDRESS=${coin.address}`,
    `ADMIN=${admin}`,
    `USER1=${user1}`,
    `USER2=${user2}`,
    "",
  ].join("\n");

  fs.writeFileSync(addressFile, contents);

  console.log("");
  console.log("Store Rewards Truffle deployment complete");
  console.log(`Core: ${core.address}`);
  console.log(`Coin: ${coin.address}`);
  console.log(`Admin: ${admin}`);
  console.log(`User1: ${user1} minted 100 RPC`);
  console.log(`User2: ${user2} minted 50 RPC`);
  console.log(`Addresses saved to: ${addressFile}`);
};
