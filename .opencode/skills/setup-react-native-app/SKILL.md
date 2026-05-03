---
name: setup-react-native-app
description: Scaffold a React Native (Expo) app with Phantom React Native SDK for mobile wallet integration, including polyfills and deep linking
---

# Scaffold React Native App with Phantom Connect

## When to use
- User asks to set up a React Native app with Phantom Connect
- User wants to create a mobile wallet integration
- User wants to scaffold a Phantom integration for iOS/Android

## Workflow

### Step 1: Install Dependencies

```bash
npx expo install @phantom/react-native-sdk react-native-get-random-values @expo/browser expo-web-browser expo-crypto
```

### Step 2: Add the Polyfill (CRITICAL — Must Be First Import)

In your app's entry file (e.g. `App.tsx` or `index.ts`), add this as the **very first import**:

```tsx
import "react-native-get-random-values"; // MUST be the first import

import { PhantomProvider } from "@phantom/react-native-sdk";
// ... other imports
```

**This is non-negotiable.** The polyfill must execute before any other code that uses crypto.

### Step 3: Configure `app.json`

Add the custom URL scheme and required plugins:

```json
{
  "expo": {
    "scheme": "your-app-scheme",
    "plugins": [
      [
        "expo-web-browser"
      ]
    ]
  }
}
```

### Step 4: Wrap App in PhantomProvider

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
        redirectUrl: "your-app-scheme://callback",
      }}
    >
      <YourApp />
    </PhantomProvider>
  );
}
```

**Mobile-specific config fields:**
- `scheme` — Your app's custom URL scheme, must match `app.json`.
- `redirectUrl` — Deep link URL using your custom scheme for OAuth callbacks.

### Step 5: Use Hooks (Same as React SDK)

The hooks API is identical to `@phantom/react-sdk`:

```tsx
import {
  useConnect,
  useAccounts,
  useDisconnect,
  useSolana,
} from "@phantom/react-native-sdk";

function WalletScreen() {
  const { connect, isConnected } = useConnect();
  const { accounts } = useAccounts();
  const { disconnect } = useDisconnect();

  const handleConnect = async () => {
    try {
      await connect();
    } catch (error) {
      console.error("Connection failed:", error);
    }
  };

  if (!isConnected) {
    return <Button title="Connect" onPress={handleConnect} />;
  }

  const solanaAccount = accounts.find((a) => a.chain === "solana");

  return (
    <View>
      <Text>Address: {solanaAccount?.address}</Text>
      <Button title="Disconnect" onPress={disconnect} />
    </View>
  );
}
```

## Important Notes

- `react-native-get-random-values` **MUST** be the very first import in your entry file.
- Always use `signAndSendTransaction` — `signTransaction` is NOT supported for embedded wallets.
- The `scheme` in `PhantomProvider` config must match the `scheme` in `app.json`.
- Register your app at [Phantom Portal](https://portal.phantom.com) to get an `appId`.
- Test deep linking on a physical device or Expo Dev Client — deep links do not work in Expo Go.
