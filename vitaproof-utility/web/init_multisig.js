const { Connection, Keypair } = require("@solana/web3.js");
const multisig = require("@sqds/multisig");
const fs = require("fs");
const path = require("path");
const os = require("os");

async function main() {
  const connection = new Connection("https://api.devnet.solana.com", "confirmed");
  const keypairPath = path.join(os.homedir(), ".config", "solana", "id.json");
  const secretKey = Uint8Array.from(JSON.parse(fs.readFileSync(keypairPath, "utf8")));
  const creator = Keypair.fromSecretKey(secretKey);

  const createKey = Keypair.generate();
  const [multisigPda] = multisig.getMultisigPda({ createKey: createKey.publicKey });

  console.log(`[+] Initializing Squads v4 Multisig PDA: ${multisigPda.toBase58()}`);

  const txSig = await multisig.rpc.multisigCreateV2({
    connection,
    feePayer: creator,
    rentPayer: creator,
    creator: creator,
    multisigPda,
    configAuthority: creator.publicKey,
    threshold: 1,
    members: [{
      key: creator.publicKey,
      permissions: multisig.types.Permissions.all(),
    }],
    timeLock: 0,
    createKey,
  });

  console.log("\n====================================================");
  console.log("   SQUADS V4 MULTISIG CREATED SUCCESSFULLY          ");
  console.log("====================================================");
  console.log(`MULTISIG_PDA: ${multisigPda.toBase58()}`);
  console.log(`Tx Signature: ${txSig}`);
  console.log(`Explorer    : https://explorer.solana.com/tx/${txSig}?cluster=devnet`);
  console.log("====================================================\n");
}

main().catch(err => console.error("[-] Multisig Creation Error:", err));
