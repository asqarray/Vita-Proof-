module.exports = {
  logEvent: (action, details) => {
    console.log(`[AUDIT] ${action}:`, JSON.stringify(details));
  }
};
