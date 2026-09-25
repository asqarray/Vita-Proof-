const { Connection, PublicKey, Keypair, TransactionInstruction } = require("@solana/web3.js");
const multisig = require("@sqds/multisig");
const fs = require("fs");
const path = require("path");
const os = require("os");

async function main() {
  const SERVICE_URL = process.env.SERVICE_URL || "https://vitaproof-gateway-869469225283.us-central1.run.app";
  const API_KEY = process.env.API_KEY || "vp_secure_dev_key_2026";
  const MULTISIG_PDA = process.env.MULTISIG_PDA;

  if (!MULTISIG_PDA) {
    console.error("[-] Error: MULTISIG_PDA environment variable is not set.");
    console.error("    Set it via: export MULTISIG_PDA=\"<YOUR_SQUADS_VAULT_PDA>\"");
    process.exit(1);
  }

  const keypairPath = path.join(os.homedir(), ".config", "solana", "id.json");
  const secretKey = Uint8Array.from(JSON.parse(fs.readFileSync(keypairPath, "utf8")));
  const feePayer = Keypair.fromSecretKey(secretKey);

  console.log(`[+] Loaded Member Keypair : ${feePayer.publicKey.toBase58()}`);

  const res = await fetch(`${SERVICE_URL}/records`, { headers: { "X-API-Key": API_KEY } });
  const records = await res.json();
  if (!records || records.length === 0) {
    console.log("[-] No records found to propose.");
    return;
  }

  const latest = records[0];
  console.log(`[+] Fetched Record ID #${latest.id} (${latest.cert_id})`);

  const connection = new Connection("https://api.devnet.solana.com", "confirmed");
  const multisigPda = new PublicKey(MULTISIG_PDA);

  const multisigAccount = await multisig.accounts.Multisig.fromAccountAddress(connection, multisigPda);
  const transactionIndex = BigInt(multisigAccount.transactionIndex + 1);

  const memoText = `VITAPROOF_VAULT|ID:${latest.id}|CERT:${latest.cert_id}|HASH:${latest.state_hash.slice(0, 16)}`;
  const memoIx = new TransactionInstruction({
    keys: [],
    programId: new PublicKey("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"),
    data: Buffer.from(memoText, "utf-8"),
  });

  console.log(`[+] Creating Squads v4 vault transaction proposal #${transactionIndex}...`);

  const txSig = await multisig.transactions.vaultTransactionCreate({
    connection,
    feePayer,
    multisigPda,
    transactionIndex,
    creator: feePayer.publicKey,
    vaultIndex: 0,
    ephemeralSigners: 0,
    instructions: [memoIx],
  });

  console.log("\n====================================================");
  console.log("   SQUADS V4 VAULT PROPOSAL CREATED SUCCESSFULLY    ");
  console.log("====================================================");
  console.log(`Multisig PDA     : ${MULTISIG_PDA}`);
  console.log(`Transaction Index: ${transactionIndex}`);
  console.log(`Tx Signature     : ${txSig}`);
  console.log(`Explorer         : https://explorer.solana.com/tx/${txSig}?cluster=devnet`);
  console.log("====================================================\n");
}

main().catch(err => console.error("[-] Squads Proposal Error:", err));
