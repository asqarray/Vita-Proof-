const express = require('express');
const { handleSettlement } = require('./src/settle');

const app = express();
const PORT = process.env.PORT || 8080;

// Essential middleware for JSON request bodies
app.use(express.json());

// Register the high-performance settlement route
app.post('/v1/settle', handleSettlement);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', engine: 'vitaproof-redis-accelerated' });
});

// Start the server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`VITAPROOF Gateway listening on port ${PORT} connected to Solana Devnet`);
});
