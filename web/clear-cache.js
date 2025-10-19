// Clear cache and force live data fetch
localStorage.clear();
sessionStorage.clear();

// Force reload of blockchain statistics
if (typeof window !== 'undefined' && window.location) {
  window.location.reload();
}
