# 🏆 BOUNTY: Fix Web Wallet Loading Bug

**Reward**: 100 COIN tokens  
**Status**: Open  
**Priority**: High  
**Difficulty**: Medium  

## Problem Description

The COINjecture web interface has a wallet loading bug that prevents existing wallets from being loaded properly. The error occurs when trying to import Ed25519 keys from localStorage:

```
DataError: Ed25519 key data must be 256 bits
```

## Technical Details

### Current Issue
- **Error Location**: `web/app.js` line 660 in `createOrLoadWallet()` method
- **Error Type**: `DataError` during `crypto.subtle.importKey()` call
- **Affected Users**: Users with existing wallets created before v3.9.10
- **New Wallets**: Work correctly (not affected)

### Root Cause
The issue appears to be related to the format of stored Ed25519 keys in localStorage. The error suggests that the key data is not exactly 256 bits (32 bytes) as expected by the Web Crypto API.

### Expected Behavior
- Existing wallets should load without errors
- Ed25519 keys should import successfully
- Wallet functionality should work normally

## Files to Investigate

- `web/app.js` - Lines 649-666 (wallet loading logic)
- Focus on `crypto.subtle.importKey()` calls for both private and public keys

## Current Code (Problematic Section)

```javascript
// Reimport Ed25519 key from stored hex using browser's crypto.subtle
const privateKeyBytes = new Uint8Array(
    walletData.privateKey.match(/.{1,2}/g).map(byte => parseInt(byte, 16))
);
const publicKeyBytes = new Uint8Array(
    walletData.publicKey.match(/.{1,2}/g).map(byte => parseInt(byte, 16))
);

const privateKey = await crypto.subtle.importKey(
    "pkcs8",
    privateKeyBytes,
    { name: "Ed25519" },
    true,
    ["sign"]
);

const publicKey = await crypto.subtle.importKey(
    "raw",
    publicKeyBytes,
    { name: "Ed25519" },
    true,
    ["verify"]
);
```

## Success Criteria

1. **Fix the wallet loading error** - No more "Ed25519 key data must be 256 bits" errors
2. **Maintain compatibility** - Existing wallets should load without requiring recreation
3. **Preserve functionality** - All wallet operations (signing, verification) should work
4. **Add error handling** - Graceful fallback for corrupted wallet data

## Submission Requirements

1. **Working Solution**: Provide a complete fix that resolves the issue
2. **Code Changes**: Submit the modified `web/app.js` file
3. **Testing**: Demonstrate that existing wallets load successfully
4. **Documentation**: Explain the root cause and solution approach

## How to Submit

1. Fork the COINjecture repository
2. Create a branch: `fix/wallet-loading-bug`
3. Implement your solution
4. Test thoroughly with existing wallets
5. Submit a pull request with:
   - Clear description of the fix
   - Before/after code comparison
   - Test results showing successful wallet loading

## Additional Context

- **Browser Support**: Must work in modern browsers (Chrome, Firefox, Safari, Edge)
- **Key Formats**: Ed25519 keys stored as hex strings in localStorage
- **Backward Compatibility**: Solution should not break existing wallet functionality
- **Performance**: Solution should not significantly impact wallet loading time

## Questions?

- Join the COINjecture Discord: [discord.gg/coinjecture]
- Open an issue on GitHub with the `bounty` label
- Contact: bounty@coinjecture.org

---

**Good luck, and happy coding! 🚀**

