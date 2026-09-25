const express = require('express');
const { execFile } = require('child_process');
const app = express();
app.use(express.json());

app.post('/run', (req, res) => {
  execFile('./engine', (error, stdout, stderr) => {
    if (error) {
      return res.status(500).json({ error: error.message, stderr });
    }
    try {
      const result = JSON.parse(stdout);
      res.json(result);
    } catch (e) {
      res.status(500).json({ error: 'Failed to parse binary output', raw: stdout });
    }
  });
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`Worker listening on port ${PORT}`));
