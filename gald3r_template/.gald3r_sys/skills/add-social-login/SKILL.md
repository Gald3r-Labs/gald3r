---
name: add-social-login
description: Configure Google and Apple social login with Phantom Connect SDK to enable embedded wallet creation
---

# Add Social Login Authentication

## When to use
- User asks to add social login or enable Google/Apple sign-in
- User wants to set up embedded wallets
- User wants to add passwordless authentication with Phantom

## Workflow

### Step 1: Register at Phantom Portal

1. Go to [Phantom Portal](https://portal.phantom.com).
2. Create a new app and obtain your `appId`.
3. Configure your allowed redirect URLs.

**You must have a valid `appId` for social login to work.**

### Step 2: Configure Providers (React SDK)

```tsx
import { PhantomProvider } from "@phantom/react-sdk";

function App() {
  return (
    <PhantomProvider
      config={{
        appId: "your-app-id-from-phantom-portal",
        providers: ["google", "apple"],
        addressTypes: ["solana"],
        authOptions: {
          redirectUrl: "https://your-app.com/auth/callback",
        },
      }}
    >
      <YourApp />
    </PhantomProvider>
  );
}
```

### Step 3: Configure Providers (Browser SDK)

```ts
import { BrowserSDK, AddressType } from "@phantom/browser-sdk";

const sdk = new BrowserSDK({
  appId: "your-app-id-from-phantom-portal",
  providers: ["google", "apple"],
  addressTypes: [AddressType.Solana],
  authOptions: {
    redirectUrl: "https://your-app.com/auth/callback",
  },
});
```

### Step 4: Configure Providers (React Native SDK)

```tsx
import "react-native-get-random-values";
import { PhantomProvider } from "@phantom/react-native-sdk";

export default function App() {
  return (
    <PhantomProvider
      config={{
        appId: "your-app-id-from-phantom-portal",
        providers: ["google", "apple"],
        addressTypes: ["solana"],
        scheme: "your-app-scheme",
        redirectUrl: "your-app-scheme://auth/callback",
      }}
    >
      <YourApp />
    </PhantomProvider>
  );
}
```

### Step 5: Handle the Connect Button

The `ConnectButton` component automatically presents social login options when `providers` are configured:

```tsx
import { ConnectButton } from "@phantom/react-sdk";

function LoginPage() {
  return (
    <div>
      <h1>Welcome</h1>
      <p>Sign in with your Google or Apple account to get started.</p>
      <ConnectButton />
    </div>
  );
}
```

### Step 6: Handle Session Persistence

Social login sessions persist for **7 days** from the last authentication. Handle re-authentication gracefully:

```tsx
import { useConnect } from "@phantom/react-sdk";

function SessionGuard({ children }: { children: React.ReactNode }) {
  const { isConnected, connect } = useConnect();

  if (!isConnected) {
    return (
      <div>
        <p>Your session has expired. Please sign in again.</p>
        <button onClick={() => connect()}>Reconnect</button>
      </div>
    );
  }

  return <>{children}</>;
}
```

## Important Notes

- **`appId` is required** — social login will not work without a valid app ID from Phantom Portal.
- **Sessions last 7 days** from the last authentication event.
- **Default spending limit** for embedded wallets is $1,000 USD/day per app per user.
- `providers` accepts `"google"` and `"apple"` — these are the supported social login methods.
- The `redirectUrl` in `authOptions` must be whitelisted in your Phantom Portal app settings.
