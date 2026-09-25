const fs = require('fs');
const path = require('path');
const { Keypair } = require('@solana/web3.js');

const possiblePaths = [
  path.join(process.env.HOME, 'functions', 'gateway-key.json'),
  path.join(process.env.HOME, 'vitaproof-gateway', 'functions', 'gateway-key.json'),
  path.join(process.cwd(), 'functions', 'gateway-key.json'),
  path.join(process.cwd(), 'gateway-key.json')
];

let keyPath = possiblePaths.find(p => fs.existsSync(p));

if (!keyPath) {
  const targetDir = path.join(process.env.HOME, 'functions');
  if (!fs.existsSync(targetDir)) fs.mkdirSync(targetDir, { recursive: true });
  keyPath = path.join(targetDir, 'gateway-key.json');
  const kp = Keypair.generate();
  fs.writeFileSync(keyPath, JSON.stringify(Array.from(kp.secretKey)));
}

const secret = Uint8Array.from(JSON.parse(fs.readFileSync(keyPath, 'utf8')));
const kp = Keypair.fromSecretKey(secret);

console.log('\n==================================================');
console.log('YOUR SOLANA DEVNET WALLET ADDRESS:');
console.log(kp.publicKey.toBase58());
console.log('==================================================\n');
