---
name: web3-blockchain
description: Blockchain dev—EVM, Solana, Cosmos, Bitcoin; Solidity, DeFi, NFTs, tokens, cross-chain.
version: 1.0.0
---

# Web3 & Blockchain Development Skill

Comprehensive reference for blockchain development across all major ecosystems. This skill supports the `web3-blockchain-developer` agent.

## Ecosystem Overview

### Chain Comparison

| Chain | Language | TPS | Finality | Gas Cost | Best For |
|-------|----------|-----|----------|----------|----------|
| Ethereum | Solidity | ~15 | 12 min | $1-50 | DeFi, NFTs, DAOs |
| Polygon | Solidity | ~7000 | 2 min | $0.01 | Scaling, gaming |
| Arbitrum | Solidity | ~4000 | ~1 min | $0.10 | DeFi, low cost |
| Solana | Rust | ~65000 | 400ms | $0.0001 | High-freq, gaming |
| Cosmos | Rust/Go | ~10000 | 6s | $0.01 | App chains, IBC |
| Bitcoin | Script | ~7 | 60 min | $1-10 | Store of value |

### Development Stack by Chain

**EVM Chains (Ethereum, Polygon, Arbitrum, etc.)**
```
Language: Solidity, Vyper
Frameworks: Hardhat, Foundry, Truffle
Testing: Mocha, Forge
Wallet: MetaMask, WalletConnect
Libraries: ethers.js, viem, web3.js
```

**Solana**
```
Language: Rust
Framework: Anchor
Testing: Bankrun, solana-test-validator
Wallet: Phantom, Solflare
Libraries: @solana/web3.js, @coral-xyz/anchor
```

**Cosmos**
```
Language: Rust (CosmWasm), Go (Cosmos SDK)
Framework: CosmWasm, Cosmos SDK
Testing: cw-multi-test
Wallet: Keplr
Libraries: CosmJS
```

## Solidity Development

### Contract Patterns

#### ERC-20 Token (Minimal)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MyToken is ERC20 {
    constructor(uint256 initialSupply) ERC20("MyToken", "MTK") {
        _mint(msg.sender, initialSupply);
    }
}
```

#### ERC-721 NFT (Minimal)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyNFT is ERC721, Ownable {
    uint256 private _tokenIdCounter;
    
    constructor() ERC721("MyNFT", "MNFT") Ownable(msg.sender) {}
    
    function mint(address to) public onlyOwner {
        _safeMint(to, _tokenIdCounter++);
    }
}
```

#### Upgradeable Contract Pattern
```solidity
// Implementation
contract MyContractV1 is Initializable, UUPSUpgradeable, OwnableUpgradeable {
    uint256 public value;
    
    function initialize() public initializer {
        __Ownable_init(msg.sender);
        __UUPSUpgradeable_init();
    }
    
    function setValue(uint256 _value) public {
        value = _value;
    }
    
    function _authorizeUpgrade(address) internal override onlyOwner {}
}
```

### Security Checklist

```
□ Reentrancy Protection
  □ Use ReentrancyGuard or checks-effects-interactions
  □ External calls last
  □ State changes before external calls

□ Access Control
  □ onlyOwner or role-based access
  □ Multi-sig for critical functions
  □ Timelock for governance

□ Input Validation
  □ Check zero addresses
  □ Validate array lengths
  □ Bound numeric inputs

□ Integer Safety
  □ Solidity 0.8+ (built-in overflow checks)
  □ Use SafeMath for older versions

□ External Calls
  □ Check return values
  □ Handle failed calls
  □ Limit gas for calls

□ Upgrades
  □ Storage layout compatibility
  □ Initializer protection
  □ Upgrade authorization
```

### Common Vulnerabilities

| Vulnerability | Description | Prevention |
|---------------|-------------|------------|
| Reentrancy | External call re-enters contract | ReentrancyGuard, CEI pattern |
| Front-running | MEV bots exploit pending txs | Commit-reveal, private mempools |
| Oracle manipulation | Price oracle attacks | TWAP, multiple oracles |
| Flash loan attacks | Borrow-attack-repay | Time-weighted checks |
| Access control | Missing permission checks | OpenZeppelin AccessControl |

### Gas Optimization

```solidity
// ❌ Expensive
for (uint256 i = 0; i < array.length; i++) {
    // array.length read every iteration
}

// ✅ Optimized
uint256 len = array.length;
for (uint256 i = 0; i < len; ) {
    // ... logic
    unchecked { ++i; }
}

// ❌ Expensive storage writes
function bad() public {
    counter = counter + 1;  // SSTORE every time
    counter = counter + 1;
}

// ✅ Batch storage writes
function good() public {
    uint256 _counter = counter;  // SLOAD once
    _counter = _counter + 2;
    counter = _counter;  // SSTORE once
}

// ❌ String errors (expensive)
require(condition, "This is an expensive error message");

// ✅ Custom errors (cheap)
error InsufficientBalance(uint256 available, uint256 required);
if (balance < amount) revert InsufficientBalance(balance, amount);
```

## Solana Development

### Program Structure (Anchor)

```rust
use anchor_lang::prelude::*;

declare_id!("YOUR_PROGRAM_ID");

#[program]
pub mod my_program {
    use super::*;
    
    pub fn initialize(ctx: Context<Initialize>, data: u64) -> Result<()> {
        let account = &mut ctx.accounts.my_account;
        account.data = data;
        account.authority = ctx.accounts.authority.key();
        Ok(())
    }
    
    pub fn update(ctx: Context<Update>, new_data: u64) -> Result<()> {
        let account = &mut ctx.accounts.my_account;
        account.data = new_data;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + MyAccount::INIT_SPACE
    )]
    pub my_account: Account<'info, MyAccount>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Update<'info> {
    #[account(
        mut,
        has_one = authority
    )]
    pub my_account: Account<'info, MyAccount>,
    
    pub authority: Signer<'info>,
}

#[account]
#[derive(InitSpace)]
pub struct MyAccount {
    pub authority: Pubkey,
    pub data: u64,
}
```

### Key Solana Concepts

| Concept | Description |
|---------|-------------|
| Account | Data storage unit (like contract storage) |
| Program | Smart contract (stateless) |
| PDA | Program Derived Address (deterministic) |
| CPI | Cross-Program Invocation |
| Rent | Storage cost (refundable) |

### PDA (Program Derived Address)

```rust
// Derive PDA
let (pda, bump) = Pubkey::find_program_address(
    &[b"seed", user.key().as_ref()],
    program_id
);

// In Anchor
#[account(
    seeds = [b"seed", user.key().as_ref()],
    bump
)]
pub pda_account: Account<'info, MyAccount>,
```

## DeFi Patterns

### AMM (Automated Market Maker)

```solidity
// Constant Product: x * y = k
contract SimpleAMM {
    uint256 public reserveA;
    uint256 public reserveB;
    
    function swap(uint256 amountIn, bool aToB) external returns (uint256) {
        uint256 reserveIn = aToB ? reserveA : reserveB;
        uint256 reserveOut = aToB ? reserveB : reserveA;
        
        // Calculate output: dy = (y * dx) / (x + dx)
        uint256 amountOut = (reserveOut * amountIn) / (reserveIn + amountIn);
        
        // Apply 0.3% fee
        amountOut = amountOut * 997 / 1000;
        
        // Update reserves
        if (aToB) {
            reserveA += amountIn;
            reserveB -= amountOut;
        } else {
            reserveB += amountIn;
            reserveA -= amountOut;
        }
        
        return amountOut;
    }
}
```

### Lending Protocol Pattern

```solidity
contract SimpleLending {
    mapping(address => uint256) public deposits;
    mapping(address => uint256) public borrows;
    
    uint256 public totalDeposits;
    uint256 public totalBorrows;
    uint256 public collateralFactor = 75; // 75%
    
    function deposit() external payable {
        deposits[msg.sender] += msg.value;
        totalDeposits += msg.value;
    }
    
    function borrow(uint256 amount) external {
        uint256 maxBorrow = deposits[msg.sender] * collateralFactor / 100;
        require(borrows[msg.sender] + amount <= maxBorrow, "Undercollateralized");
        
        borrows[msg.sender] += amount;
        totalBorrows += amount;
        payable(msg.sender).transfer(amount);
    }
    
    function liquidate(address user) external {
        uint256 maxBorrow = deposits[user] * collateralFactor / 100;
        require(borrows[user] > maxBorrow, "Not liquidatable");
        
        // Liquidation logic...
    }
}
```

## NFT Development

### Metadata Standards

**ERC-721 Metadata (OpenSea)**
```json
{
  "name": "My NFT #1",
  "description": "Description of the NFT",
  "image": "ipfs://QmXxx.../1.png",
  "external_url": "https://myproject.com/nft/1",
  "attributes": [
    {
      "trait_type": "Background",
      "value": "Blue"
    },
    {
      "trait_type": "Rarity",
      "value": "Legendary"
    },
    {
      "display_type": "number",
      "trait_type": "Generation",
      "value": 1
    }
  ]
}
```

### Royalties (EIP-2981)

```solidity
import "@openzeppelin/contracts/interfaces/IERC2981.sol";

contract NFTWithRoyalties is ERC721, IERC2981 {
    address public royaltyReceiver;
    uint96 public royaltyFee = 500; // 5%
    
    function royaltyInfo(uint256, uint256 salePrice) 
        external view override 
        returns (address, uint256) 
    {
        return (royaltyReceiver, (salePrice * royaltyFee) / 10000);
    }
    
    function supportsInterface(bytes4 interfaceId) 
        public view override(ERC721, IERC165) 
        returns (bool) 
    {
        return interfaceId == type(IERC2981).interfaceId 
            || super.supportsInterface(interfaceId);
    }
}
```

## Bitcoin & Script

### Bitcoin Script Basics

```
# P2PKH (Pay to Public Key Hash) - Standard transaction
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG

# P2SH (Pay to Script Hash) - Multi-sig example
OP_2 <pubKey1> <pubKey2> <pubKey3> OP_3 OP_CHECKMULTISIG

# OP_RETURN (Data storage)
OP_RETURN <data up to 80 bytes>
```

### Ordinals & BRC-20

```json
// BRC-20 Deploy
{
  "p": "brc-20",
  "op": "deploy",
  "tick": "ordi",
  "max": "21000000",
  "lim": "1000"
}

// BRC-20 Mint
{
  "p": "brc-20",
  "op": "mint",
  "tick": "ordi",
  "amt": "1000"
}

// BRC-20 Transfer
{
  "p": "brc-20",
  "op": "transfer",
  "tick": "ordi",
  "amt": "100"
}
```

## Testing & Deployment

### Hardhat Testing

```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MyToken", function () {
    let token, owner, addr1;
    
    beforeEach(async function () {
        [owner, addr1] = await ethers.getSigners();
        const Token = await ethers.getContractFactory("MyToken");
        token = await Token.deploy(ethers.parseEther("1000000"));
    });
    
    it("Should transfer tokens", async function () {
        await token.transfer(addr1.address, ethers.parseEther("100"));
        expect(await token.balanceOf(addr1.address))
            .to.equal(ethers.parseEther("100"));
    });
    
    it("Should fail if insufficient balance", async function () {
        await expect(
            token.connect(addr1).transfer(owner.address, 1)
        ).to.be.revertedWithCustomError(token, "ERC20InsufficientBalance");
    });
});
```

### Foundry Testing

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/MyToken.sol";

contract MyTokenTest is Test {
    MyToken token;
    address alice = makeAddr("alice");
    address bob = makeAddr("bob");
    
    function setUp() public {
        token = new MyToken(1000000 ether);
    }
    
    function testTransfer() public {
        token.transfer(alice, 100 ether);
        assertEq(token.balanceOf(alice), 100 ether);
    }
    
    function testFuzz_Transfer(uint256 amount) public {
        amount = bound(amount, 0, token.balanceOf(address(this)));
        token.transfer(alice, amount);
        assertEq(token.balanceOf(alice), amount);
    }
}
```

### Deployment Checklist

```
□ Pre-Deployment
  □ All tests passing
  □ Code audited (if handling value)
  □ Gas optimized
  □ Verified on testnet

□ Deployment
  □ Correct network selected
  □ Sufficient gas/funds
  □ Constructor args verified
  □ Transaction confirmed

□ Post-Deployment
  □ Verify on block explorer
  □ Test basic functions
  □ Transfer ownership (if applicable)
  □ Update frontend/docs with addresses

□ Security
  □ Renounce unnecessary permissions
  □ Set up multi-sig (if applicable)
  □ Monitor for unusual activity
```

## Resources

### Reference Documents
- `reference/solidity_patterns.md` - Common Solidity patterns
- `reference/security_checklist.md` - Security audit checklist
- `reference/gas_optimization.md` - Gas optimization techniques
- `reference/chain_comparison.md` - Detailed chain comparison

### Templates
- `templates/erc20_token.sol` - ERC-20 template
- `templates/erc721_nft.sol` - ERC-721 template
- `templates/hardhat_config.js` - Hardhat configuration
- `templates/foundry_config.toml` - Foundry configuration

### External Resources
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts)
- [Solidity Docs](https://docs.soliditylang.org)
- [Anchor Book](https://book.anchor-lang.com)
- [Ethereum.org](https://ethereum.org/developers)

---
*This skill supports: web3-blockchain-developer agent*
