---
name: setup-react-app
description: Scaffold a React app with Phantom Connect SDK for wallet integration, including social login and Solana support
---

# Scaffold React App with Phantom Connect

## When to use
- User asks to set up a React app with Phantom Connect
- User wants to create a wallet-connected React project
- User wants to scaffold a Phantom integration in React

## Workflow

### Step 1: Install Dependencies

```bash
npm install @phantom/react-sdk @solana/web3.js
```

### Step 2: Configure PhantomProvider

Wrap your app's root component in `PhantomProvider` with the required configuration:

```tsx
import { PhantomProvider } from "@phantom/react-sdk";

function App() {
  return (
    <PhantomProvider
      config={{
        appId: "your-app-id-from-phantom-portal",
        providers: ["google", "apple"],
        addressTypes: ["solana", "ethereum"],
      }}
    >
      <YourApp />
    </PhantomProvider>
  );
}
```

**Required config fields:**
- `appId` — Register at [Phantom Portal](https://portal.phantom.com) to obtain this.
- `providers` — Social login providers to enable (e.g. `["google", "apple"]`).
- `addressTypes` — Blockchain address types to request (e.g. `["solana"]`, `["solana", "ethereum"]`).

### Step 3: Add the Connect Button

Use the built-in `ConnectButton` component for the simplest integration:

```tsx
import { ConnectButton } from "@phantom/react-sdk";

function Navbar() {
  return (
    <nav>
      <ConnectButton />
    </nav>
  );
}
```

### Step 4: Use Hooks for Wallet State

Wire up the core hooks to access wallet state and chain-specific APIs:

```tsx
import {
  useConnect,
  useAccounts,
  useDisconnect,
  useSolana,
} from "@phantom/react-sdk";

function WalletInfo() {
  const { isConnected } = useConnect();
  const { accounts } = useAccounts();
  const { disconnect } = useDisconnect();
  const solana = useSolana();

  if (!isConnected) {
    return <p>Not connected</p>;
  }

  const solanaAccount = accounts.find((a) => a.chain === "solana");

  return (
    <div>
      <p>Address: {solanaAccount?.address}</p>
      <button onClick={disconnect}>Disconnect</button>
    </div>
  );
}
```

### Step 5: Handle Connection Errors

Always wrap connection logic in try-catch:

```tsx
import { useConnect } from "@phantom/react-sdk";

function ConnectFlow() {
  const { connect } = useConnect();

  const handleConnect = async () => {
    try {
      await connect();
    } catch (error) {
      console.error("Connection failed:", error);
    }
  };

  return <button onClick={handleConnect}>Connect Wallet</button>;
}
```

## Key Hooks Reference

| Hook             | Purpose                                      |
| ---------------- | -------------------------------------------- |
| `useConnect`     | Connect/disconnect, check `isConnected`      |
| `useAccounts`    | Access connected wallet accounts             |
| `useDisconnect`  | Disconnect the current session               |
| `useSolana`      | Access Solana-specific APIs (sign, send)      |
| `useEthereum`    | Access EVM-specific APIs                      |

## Important Notes

- Always use `signAndSendTransaction` — `signTransaction` is NOT supported for embedded wallets.
- Sessions persist for 7 days from last authentication.
- Register your app at [Phantom Portal](https://portal.phantom.com) to get an `appId`.
