const functions = require('firebase-functions');
const express = require('express');
const { PublicKey } = require('@solana/web3.js');
const nacl = require('tweetnacl');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json());

app.post('/api/v1/auth/siws', (req, res) => {
  const { publicKey, signature, message } = req.body;

  if (!publicKey || !signature || !message) {
    return res.status(400).json({ error: 'Missing required parameters' });
  }

  try {
    const messageBytes = new TextEncoder().encode(message);
    const signatureBytes = new Uint8Array(signature);
    const pubKeyBytes = new PublicKey(publicKey).toBytes();

    const isValid = nacl.sign.detached.verify(messageBytes, signatureBytes, pubKeyBytes);

    if (!isValid) {
      return res.status(401).json({ error: 'Invalid SIWS signature' });
    }

    const sessionToken = jwt.sign(
      { sub: publicKey, scope: 'compute:execute' },
      process.env.JWT_GATEWAY_SECRET || 'dev_secret',
      { expiresIn: '1h' }
    );

    return res.json({ status: 'AUTHENTICATED', sessionToken });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

exports.api = functions.https.onRequest(app);