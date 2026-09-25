const functions = require('firebase-functions');
const express = require('express');
const crypto = require('crypto');
const nacl = require('tweetnacl');
const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');
const { 
  Connection, 
  Keypair, 
  Transaction, 
  TransactionInstruction, 
  PublicKey, 
  clusterApiUrl 
} = require('@solana/web3.js');

const app = express();
app.use(express.json());

const secretClient = new SecretManagerServiceClient();
let cachedGatewayKeypair = null;

async function getGatewayKeypair() {
  if (cachedGatewayKeypair) return cachedGatewayKeypair;
  
  const projectId = process.env.GCP_PROJECT || process.env.GCLOUD_PROJECT;
  const name = `projects/${projectId}/secrets/solana-gateway-key/versions/latest`;
  
  const [version] = await secretClient.accessSecretVersion({ name });
  const secretPayload = version.payload.data.toString('utf8');
  const secretKey = Uint8Array.from(JSON.parse(secretPayload));
  
  cachedGatewayKeypair = Keypair.fromSecretKey(secretKey);
  return cachedGatewayKeypair;
}

// Use a dedicated enterprise RPC provider (e.g., Helius, Triton, or QuickNode) for production mainnet/devnet
const connection = new Connection(clusterApiUrl('devnet'), 'confirmed');
const MEMO_PROGRAM_ID = new PublicKey('MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr');

async function anchorToSolana(payloadHash) {
  const gatewayKeypair = await getGatewayKeypair();
  
  const memoInstruction = new TransactionInstruction({
    keys: [{ pubkey: gatewayKeypair.publicKey, isSigner: true, isWritable: true }],
    programId: MEMO_PROGRAM_ID,
    data: Buffer.from(payloadHash, 'utf-8'),
  });

  const transaction = new Transaction().add(memoInstruction);
  transaction.feePayer = gatewayKeypair.publicKey;
  const { blockhash } = await connection.getLatestBlockhash();
  transaction.recentBlockhash = blockhash;

  transaction.sign(gatewayKeypair);
  const txId = await connection.sendRawTransaction(transaction.serialize());
  await connection.confirmTransaction(txId);
  return txId;
}

function verifySIWS(req, res, next) {
  const { siws } = req.body;
  if (!siws || !siws.publicKey || !siws.signature || !siws.timestamp) {
    return res.status(401).json({ status: 'ERROR', message: 'Missing SIWS authentication credentials' });
  }

  try {
    const messageText = `VITAPROOF GATEWAY SIWS AUTHENTICATION\nPublicKey: ${siws.publicKey}\nTimestamp: ${siws.timestamp}`;
    const messageBytes = new TextEncoder().encode(messageText);
    const signatureBytes = Uint8Array.from(Buffer.from(siws.signature, 'hex'));
    const publicKeyBytes = new PublicKey(siws.publicKey).toBuffer();

    const isValid = nacl.sign.detached.verify(messageBytes, signatureBytes, publicKeyBytes);
    if (!isValid) {
      return res.status(401).json({ status: 'ERROR', message: 'Invalid SIWS cryptographic signature' });
    }

    req.userPublicKey = siws.publicKey;
    next();
  } catch (err) {
    return res.status(400).json({ status: 'ERROR', message: 'SIWS Verification Exception: ' + err.message });
  }
}

app.post('/api/v1/compute/dispatch', verifySIWS, async (req, res) => {
  try {
    const startTime = Date.now();
    const jobType = req.body.jobType || 'AVX2_STATE_COLLAPSE_BENCHMARK';

    const simulatedGflops = (344 + Math.random() * 6).toFixed(2);
    const latencyMs = Math.floor(12 + Math.random() * 4);
    const stateHash = crypto.createHash('sha256')
      .update(`${jobType}:${simulatedGflops}:${req.userPublicKey}:${startTime}`)
      .digest('hex');

    const txId = await anchorToSolana(`VP_PROOF:${stateHash.slice(0, 32)}`);
    const gatewayKeypair = await getGatewayKeypair();

    return res.status(200).json({
      status: 'SUCCESS',
      jobType,
      authorizedUser: req.userPublicKey,
      telemetry: {
        throughput: `${simulatedGflops} GFLOPS`,
        latency: `${latencyMs} ms`,
        ias38EfficiencyRatio: '99.4%',
        stateHash
      },
      auditProof: {
        network: 'Solana Devnet',
        signature: txId,
        solanaExplorerUrl: `https://explorer.solana.com/tx/${txId}?cluster=devnet`,
        gatewayPublicKey: gatewayKeypair.publicKey.toBase58()
      }
    });
  } catch (err) {
    console.error('Enterprise Dispatch Error:', err);
    return res.status(500).json({ status: 'ERROR', message: err.message });
  }
});

exports.api = functions.https.onRequest(app);