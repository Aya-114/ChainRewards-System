module.exports = {
  contracts_directory: "./project Crypto/contracts",
  migrations_directory: "./migrations",
  contracts_build_directory: "./build/contracts",

  networks: {
    development: {
      host: "127.0.0.1",
      port: 7545,
      network_id: "*",
      gas: 6721975,
    },
  },

  compilers: {
    solc: {
      version: "0.8.19",
      settings: {
        optimizer: {
          enabled: false,
          runs: 200,
        },
      },
    },
  },
};
