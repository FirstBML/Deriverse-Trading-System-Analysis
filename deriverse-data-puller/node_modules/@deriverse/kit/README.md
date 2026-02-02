# Deriverse SDK

TypeScript SDK for interacting with the Deriverse decentralized exchange (DEX) on Solana. This SDK provides a comprehensive interface for trading spot and perpetual futures, managing liquidity, and interacting with the Deriverse smart contract.

Based on [`@solana/kit`](https://www.npmjs.com/package/@solana/kit)

## Features

- **Spot Trading**
  - Place and cancel spot orders
  - Manage spot liquidity positions
  - Query spot order book and market data
  - Handle spot deposits and withdrawals

- **Perpetual Futures Trading**
  - Trade perpetual futures with leverage
  - Manage perpetual positions
  - Place and cancel perpetual orders
  - Handle perpetual deposits and withdrawals
  - Adjust leverage on positions

- **Account Management**
  - Create and manage trading accounts
  - Handle token deposits and withdrawals
  - Manage associated token accounts
  - Query account balances and positions

- **Market Data**
  - Access order book data
  - Query market depth
  - Get price steps and market information
  - Access historical trade data

## Installation

```bash
npm install @deriverse/kit
```

## Examples

We prepared a comprehensive example that is available here: https://github.com/deriverse/kit-example

## Development

### Prerequisites

- Node.js (v20 or higher)
- npm or yarn
- TypeScript (v5.4.3 or higher)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/deriverse/kit.git
cd kit
```

2. Install dependencies:
```bash
npm install
```

3. Build the project:
```bash
npm run build
```

## License

Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
