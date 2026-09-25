const { Connection, PublicKey, Keypair, Transaction, sendAndConfirmTransaction } = require("@solana/web3.js");
const multisig = require("@sqds/multisig");
const fs = require("fs");
const path = require("path");
const os = require("os");

async function main() {
  const connection = new Connection("https://api.devnet.solana.com", "confirmed");
  const SQDS_PROGRAM_ID = new PublicKey("SQDS4ep65T869zMMBKyuUq6aD6EgTu8psMjkvj52pCf");

  const keypairPath = path.join(os.homedir(), ".config", "solana", "id.json");
  const secretKey = Uint8Array.from(JSON.parse(fs.readFileSync(keypairPath, "utf8")));
  const feePayer = Keypair.fromSecretKey(secretKey);
  console.log(`[+] Loaded Keypair: ${feePayer.publicKey.toBase58()}`);

  const createKey = Keypair.generate();
  const [multisigPda] = multisig.getMultisigPda({
    createKey: createKey.publicKey,
    programId: SQDS_PROGRAM_ID,
  });
  console.log(`[+] Creating Squads v4 Vault PDA: ${multisigPda.toBase58()}...`);

  // Fetch the program config PDA and extract its treasury property safely
  const [programConfigPda] = multisig.getProgramConfigPda({ programId: SQDS_PROGRAM_ID });
  const programConfig = await multisig.accounts.ProgramConfig.fromAccountAddress(
    connection,
    programConfigPda
  );
  const treasuryPda = programConfig.treasury;

  const createIx = multisig.instructions.multisigCreateV2({
    createKey: createKey.publicKey,
    creator: feePayer.publicKey,
    multisigPda,
    configAuthority: feePayer.publicKey,
    timeLock: 0,
    threshold: 1,
    members: [{
      key: feePayer.publicKey,
      permissions: multisig.types.Permissions.all()
    }],
    rentPayer: feePayer.publicKey,
    treasury: treasuryPda,
    programConfigPda: programConfigPda,
    programId: SQDS_PROGRAM_ID,
  });

  const tx = new Transaction().add(createIx);

  try {
    const txSig = await sendAndConfirmTransaction(connection, tx, [feePayer, createKey]);
    console.log(`[+] Vault created successfully! Tx: https://explorer.solana.com/tx/${txSig}?cluster=devnet`);
  } catch (err) {
    console.error("[-] Pipeline Error:", err);
  }
}

main();
