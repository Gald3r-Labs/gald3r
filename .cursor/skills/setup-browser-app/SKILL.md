---
name: setup-browser-app
description: Scaffold a vanilla JS/TS app with Phantom Browser SDK for wallet integration, without any framework dependency
---

# Scaffold Browser App with Phantom Connect

## When to use
- User asks to set up a vanilla JS app with Phantom Connect
- User wants to create a framework-agnostic wallet integration
- User wants to use the Browser SDK directly

## Workflow

### Step 1: Install Dependencies

```bash
npm install @phantom/browser-sdk @solana/web3.js
```

### Step 2: Create the SDK Singleton

Initialize a single `BrowserSDK` instance for your application:

```ts
import { BrowserSDK, AddressType } from "@phantom/browser-sdk";

const sdk = new BrowserSDK({
  appId: "your-app-id-from-phantom-portal",
  providers: ["google", "apple"],
  addressTypes: [AddressType.Solana, AddressType.Ethereum],
});
```

**Important:** Create only ONE `BrowserSDK` instance per application. Reuse this singleton everywhere.

### Step 3: Implement Connect / Disconnect

```ts
async function connectWallet() {
  try {
    const accounts = await sdk.connect();
    console.log("Connected accounts:", accounts);

    const solanaAccount = accounts.find((a) => a.chain === "solana");
    if (solanaAccount) {
      console.log("Solana address:", solanaAccount.address);
    }
  } catch (error) {
    console.error("Connection failed:", error);
  }
}

async function disconnectWallet() {
  try {
    await sdk.disconnect();
    console.log("Disconnected");
  } catch (error) {
    console.error("Disconnect failed:", error);
  }
}
```

### Step 4: Access Chain-Specific APIs

Use `sdk.solana` for Solana operations and `sdk.ethereum` for EVM operations:

```ts
// Solana operations
const solana = sdk.solana;

// Sign and send a transaction
const { signature } = await solana.signAndSendTransaction(transaction);

// Sign a message
const { signature: msgSig } = await solana.signMessage(
  new TextEncoder().encode("Hello from Phantom!")
);
```

### Step 5: Check Connection State

```ts
function isWalletConnected(): boolean {
  return sdk.isConnected;
}

function getAccounts() {
  return sdk.accounts;
}
```

### Step 6: HTML Setup (Minimal Example)

```html
<!DOCTYPE html>
<html>
  <body>
    <button id="connect">Connect Wallet</button>
    <button id="disconnect" style="display:none">Disconnect</button>
    <p id="address"></p>
    <script type="module" src="./main.ts"></script>
  </body>
</html>
```

## Important Notes

- Import `AddressType` from `@phantom/browser-sdk`, not from other packages.
- Always use `signAndSendTransaction` — `signTransaction` is NOT supported for embedded wallets.
- The SDK singleton should be created once and reused across your application.
- Register your app at [Phantom Portal](https://portal.phantom.com) to get an `appId`.
