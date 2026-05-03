---
name: send-sol-transaction
description: Build and send SOL transfers with Phantom Connect SDK, including transaction construction, signing, and verification
---

# Send SOL Transaction

## When to use
- User asks to send SOL or transfer tokens
- User wants to build a Solana transaction
- User wants to implement a payment flow with Phantom

## Workflow

### Step 1: Build the Transaction

```ts
import {
  Connection,
  PublicKey,
  Transaction,
  SystemProgram,
  LAMPORTS_PER_SOL,
} from "@solana/web3.js";

const connection = new Connection("https://api.devnet.solana.com");

function buildTransferTransaction(
  fromPubkey: PublicKey,
  toPubkey: PublicKey,
  solAmount: number
): Transaction {
  const transaction = new Transaction().add(
    SystemProgram.transfer({
      fromPubkey,
      toPubkey,
      lamports: solAmount * LAMPORTS_PER_SOL,
    })
  );
  return transaction;
}
```

**Always use `LAMPORTS_PER_SOL` for conversion. Never hardcode `1000000000`.**

### Step 2: Sign and Send (React SDK)

```tsx
import { useSolana, useAccounts } from "@phantom/react-sdk";
import { PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } from "@solana/web3.js";

function SendSol() {
  const solana = useSolana();
  const { accounts } = useAccounts();

  const sendTransaction = async () => {
    const solanaAccount = accounts.find((a) => a.chain === "solana");
    if (!solanaAccount) {
      console.error("No Solana account connected");
      return;
    }

    const fromPubkey = new PublicKey(solanaAccount.address);
    const toPubkey = new PublicKey("RECIPIENT_ADDRESS_HERE");

    const transaction = new Transaction().add(
      SystemProgram.transfer({
        fromPubkey,
        toPubkey,
        lamports: 0.01 * LAMPORTS_PER_SOL,
      })
    );

    try {
      const { signature } = await solana.signAndSendTransaction(transaction);
      console.log("Transaction signature:", signature);
      console.log(
        `View on Explorer: https://explorer.solana.com/tx/${signature}?cluster=devnet`
      );
    } catch (error) {
      console.error("Transaction failed:", error);
    }
  };

  return <button onClick={sendTransaction}>Send 0.01 SOL</button>;
}
```

### Step 3: Sign and Send (Browser SDK)

```ts
import { PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } from "@solana/web3.js";

async function sendSol(sdk: BrowserSDK) {
  const solanaAccount = sdk.accounts.find((a) => a.chain === "solana");
  if (!solanaAccount) {
    throw new Error("No Solana account connected");
  }

  const fromPubkey = new PublicKey(solanaAccount.address);
  const toPubkey = new PublicKey("RECIPIENT_ADDRESS_HERE");

  const transaction = new Transaction().add(
    SystemProgram.transfer({
      fromPubkey,
      toPubkey,
      lamports: 0.01 * LAMPORTS_PER_SOL,
    })
  );

  try {
    const { signature } = await sdk.solana.signAndSendTransaction(transaction);
    console.log("Transaction signature:", signature);
    console.log(
      `View on Explorer: https://explorer.solana.com/tx/${signature}?cluster=devnet`
    );
  } catch (error) {
    console.error("Transaction failed:", error);
  }
}
```

### Step 4: Verify Transaction Status

```ts
async function verifyTransaction(signature: string) {
  const connection = new Connection("https://api.devnet.solana.com");

  const status = await connection.getSignatureStatus(signature);
  if (status.value?.confirmationStatus === "confirmed" ||
      status.value?.confirmationStatus === "finalized") {
    console.log("Transaction confirmed!");
  } else {
    console.log("Transaction status:", status.value);
  }
}
```

## Critical Rules

- **Use `signAndSendTransaction`** — NOT `signTransaction`. Embedded wallets do not support `signTransaction`.
- **Use `LAMPORTS_PER_SOL`** for SOL-to-lamport conversion.
- **Use devnet** (`https://api.devnet.solana.com`) for testing, **mainnet-beta** (`https://api.mainnet-beta.solana.com`) for production.
- **Always check** that a Solana account is connected before attempting to build a transaction.
- **Never expose private keys** — Phantom handles all signing internally.
