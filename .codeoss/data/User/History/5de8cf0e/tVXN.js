import { Connection, Keypair, PublicKey } from "@solana/web3.js";
import * as multisig from "@sqds/multisig";

const connection = new Connection("https://api.devnet.solana.com", "confirmed");
const adminKeypair = Keypair.generate(); // Your admin key

const createKey = Keypair.generate();
const [multisigPda] = multisig.getMultisigPda({ createKey: createKey.publicKey });
const [vaultPda] = multisig.getVaultPda({ multisigPda, index: 0 });

console.log("VITAPROOF Vault Address (Squads v4):", vaultPda.toBase58());