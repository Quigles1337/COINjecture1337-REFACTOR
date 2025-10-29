// COINjecture Web Interface - Constants and Configuration
// Version: 3.16.0

// API Configuration
export const API_CONFIG = {
  BASE_URL: 'https://api.coinjecture.com',
  FALLBACK_URL: 'http://167.172.213.70:12346',
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3
};

// API Endpoints
export const API_ENDPOINTS = {
  // Blockchain Data
  METRICS_DASHBOARD: '/v1/metrics/dashboard',
  BLOCK_LATEST: '/v1/data/block/latest',
  BLOCK_BY_INDEX: (index) => `/v1/data/block/${index}`,
  BLOCK_PROOF: (cid) => `/v1/data/proof/${cid}`,
  
  // Mining & Rewards
  INGEST_BLOCK: '/v1/ingest/block',
  REWARDS_USER: (address) => `/v1/rewards/${address}`,
  REWARDS_LEADERBOARD: '/v1/rewards/leaderboard',
  
  // Wallet Management
  WALLET_REGISTER: '/v1/wallet/register',
  WALLET_VERIFY: '/v1/wallet/verify',
  WALLET_BALANCE: (address) => `/v1/wallet/${address}/balance`,
  WALLET_TRANSACTIONS: (address) => `/v1/wallet/${address}/transactions`,
  
  // IPFS Data
  IPFS_USER: (address) => `/v1/ipfs/user/${address}`,
  IPFS_STATS: (address) => `/v1/ipfs/stats/${address}`,
  IPFS_DOWNLOAD: (address) => `/v1/ipfs/download/${address}`,
  IPFS_CONTENT: (cid) => `/v1/ipfs/${cid}`,
  
  // Problem Submission
  PROBLEM_SUBMIT: '/v1/problem/submit',
  PROBLEM_LIST: '/v1/problem/list',
  PROBLEM_STATUS: (id) => `/v1/problem/${id}`,
  
  // User Management
  USER_REGISTER: '/v1/user/register',
  USER_PROFILE: (address) => `/v1/user/profile/${address}`,
  
  // Transaction
  TRANSACTION_SEND: '/v1/transaction/send',
  
  // Telemetry
  TELEMETRY_LATEST: '/v1/display/telemetry/latest',
  
  // Health
  HEALTH: '/health'
};

// IPFS Gateways (ordered by reliability)
export const IPFS_GATEWAYS = [
  'https://ipfs.io/ipfs/',
  'https://cloudflare-ipfs.com/ipfs/',
  'https://gateway.pinata.cloud/ipfs/',
  'https://dweb.link/ipfs/',
  'https://gateway.ipfs.io/ipfs/',
  'http://167.172.213.70:8080/ipfs/' // Local gateway as fallback
];

// Cache Configuration
export const CACHE_CONFIG = {
  BUSTER: '?v=3.16.1&t=' + Date.now(),
  FORCE_REFRESH: true,
  METRICS_REFRESH_INTERVAL: 15000, // 15 seconds
  BLOCK_REFRESH_INTERVAL: 5000     // 5 seconds
};

// Mining Configuration
export const MINING_CONFIG = {
  // Mobile optimization
  MOBILE_MAX_PROBLEM_SIZE: 15,
  MOBILE_MAX_SOLVE_TIME: 10000, // 10 seconds
  
  // Desktop optimization
  DESKTOP_MAX_PROBLEM_SIZE: 25,
  DESKTOP_MAX_SOLVE_TIME: 15000, // 15 seconds
  
  // Consensus validation
  MIN_WORK_SCORE: 1,
  MAX_ATTEMPTS: 1000
};

// UI Configuration
export const UI_CONFIG = {
  ANIMATION_DURATION: 300,
  TOAST_DURATION: 3000,
  MODAL_Z_INDEX: 1000,
  TOOLTIP_DELAY: 500
};

// Device Detection
export const DEVICE_CONFIG = {
  MOBILE_BREAKPOINT: 768,
  TABLET_BREAKPOINT: 1024
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection failed. Please check your internet connection.',
  API_ERROR: 'API request failed. Please try again later.',
  WALLET_ERROR: 'Wallet operation failed. Please check your wallet configuration.',
  MINING_ERROR: 'Mining operation failed. Please try again.',
  VALIDATION_ERROR: 'Input validation failed. Please check your data.',
  TIMEOUT_ERROR: 'Request timed out. Please try again.'
};

// Success Messages
export const SUCCESS_MESSAGES = {
  WALLET_CREATED: 'Wallet created successfully!',
  BLOCK_MINED: 'Block mined successfully!',
  TRANSACTION_SENT: 'Transaction sent successfully!',
  DATA_SAVED: 'Data saved successfully!'
};

// Version Information
export const VERSION_INFO = {
  VERSION: '3.16.1',
  BUILD_DATE: '2024-12-25',
  API_VERSION: 'v1',
  FEATURES: [
    'CLI Package Fixes',
    'Dynamic Gas Calculation',
    'IPFS Integration',
    'Mobile Optimization',
    'Real-time Metrics',
    'Blockchain Explorer',
    'Data Marketplace'
  ]
};
