const express = require('express');
const { handleSettlement } = require('./src/settle');
const { verifyAuditChain } = require('./src/lib/audit');
const { startGrpcServer } = require('./src/grpcServer');

const app = express();
app.use(express.json());

// REST Settlement Endpoint
app.post('/v1/settle', handleSettlement);

// Compliance Audit Verification Endpoint
app.get('/v1/audit/verify', async (req, res) => {
  try {
    const report = await verifyAuditChain();
    res.json({
      system: "VITAPROOF Institutional Gateway",
      complianceStatus: report.valid ? "PASSED_TAMPER_RESISTANT" : "FAILED_COMPROMISED",
      auditDetails: report,
      timestamp: new Date().toISOString()
    });
  } catch (err) {
    res.status(500).json({ error: "Failed to verify audit chain integrity" });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`VITAPROOF REST Gateway listening on port ${PORT}`);
});

// Start gRPC server alongside REST
startGrpcServer();
