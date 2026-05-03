---
name: sign-message
description: Implement message signing with Phantom Connect SDK for Solana and EVM, including Sign-in with Solana (SIWS) authentication
---

# Sign Message

## When to use
- User asks to sign a message
- User wants to implement SIWS (Sign-in with Solana)
- User wants to verify wallet ownership or add wallet-based authentication

## Workflow

### Step 1: Sign a Message on Solana (React SDK)

```tsx
import { useSolana } from "@phantom/react-sdk";

function SignMessage() {
  const solana = useSolana();

  const handleSign = async () => {
    const message = new TextEncoder().encode("Hello from my dApp!");

    try {
      const { signature } = await solana.signMessage(message);
      console.log("Signature:", signature);
    } catch (error) {
      console.error("Signing failed:", error);
    }
  };

  return <button onClick={handleSign}>Sign Message</button>;
}
```

### Step 2: Sign a Message on Solana (Browser SDK)

```ts
async function signMessage(sdk: BrowserSDK) {
  const message = new TextEncoder().encode("Hello from my dApp!");

  try {
    const { signature } = await sdk.solana.signMessage(message);
    console.log("Signature:", signature);
  } catch (error) {
    console.error("Signing failed:", error);
  }
}
```

### Step 3: Sign a Message on EVM

For Ethereum/EVM chains, use `signPersonalMessage`:

```tsx
import { useEthereum } from "@phantom/react-sdk";

function SignEVMMessage() {
  const ethereum = useEthereum();

  const handleSign = async () => {
    try {
      const { signature } = await ethereum.signPersonalMessage("Hello from my dApp!");
      console.log("Signature:", signature);
    } catch (error) {
      console.error("Signing failed:", error);
    }
  };

  return <button onClick={handleSign}>Sign EVM Message</button>;
}
```

### Step 4: Sign-in with Solana (SIWS)

SIWS provides a standardized authentication flow — proving wallet ownership to your backend:

```tsx
import { useSolana, useAccounts } from "@phantom/react-sdk";

function SignInWithSolana() {
  const solana = useSolana();
  const { accounts } = useAccounts();

  const handleSIWS = async () => {
    const solanaAccount = accounts.find((a) => a.chain === "solana");
    if (!solanaAccount) return;

    // Construct the SIWS message
    const domain = window.location.host;
    const uri = window.location.origin;
    const nonce = crypto.randomUUID(); // Or fetch from your backend
    const issuedAt = new Date().toISOString();

    const message = [
      `${domain} wants you to sign in with your Solana account:`,
      solanaAccount.address,
      "",
      "Sign in to access your account.",
      "",
      `URI: ${uri}`,
      `Version: 1`,
      `Nonce: ${nonce}`,
      `Issued At: ${issuedAt}`,
    ].join("\n");

    try {
      const { signature } = await solana.signMessage(
        new TextEncoder().encode(message)
      );

      // Send signature + message to your backend for verification
      const response = await fetch("/api/auth/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          signature,
          publicKey: solanaAccount.address,
        }),
      });

      if (response.ok) {
        console.log("Authenticated successfully!");
      }
    } catch (error) {
      console.error("SIWS failed:", error);
    }
  };

  return <button onClick={handleSIWS}>Sign in with Solana</button>;
}
```

## API Reference

| Chain    | Method                          | Input                | Output        |
| -------- | ------------------------------- | -------------------- | ------------- |
| Solana   | `solana.signMessage(bytes)`     | `Uint8Array`         | `{ signature }` |
| Ethereum | `ethereum.signPersonalMessage(msg)` | `string`         | `{ signature }` |

## Important Notes

- Solana `signMessage` expects a `Uint8Array` — use `new TextEncoder().encode(...)` to convert strings.
- EVM `signPersonalMessage` accepts a plain string.
- For SIWS, always generate a unique nonce per sign-in attempt to prevent replay attacks.
- Always wrap signing calls in try-catch to handle user rejections.
