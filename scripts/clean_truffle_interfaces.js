const fs = require("fs");
const path = require("path");

const buildDir = path.join(__dirname, "..", "build", "contracts");
const interfaceArtifacts = [
  "IRewardPointCoin.json",
  "StoreRewardsAdmin.json",
];

for (const artifact of interfaceArtifacts) {
  const artifactPath = path.join(buildDir, artifact);
  if (fs.existsSync(artifactPath)) {
    fs.unlinkSync(artifactPath);
    console.log(`Removed interface artifact: ${artifact}`);
  }
}
