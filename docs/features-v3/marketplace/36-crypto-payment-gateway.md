# Feature 36: Crypto Payment Gateway

## Overview
Accept Bitcoin, Ethereum, Solana, and USDC for hosting payments. On-chain invoice verification with automatic conversion to fiat.

## Components

### Integration Service: `marketplace/crypto_gateway.py`
- `CryptoPaymentManager` - Core crypto payment processing
  - Wallet management (generate addresses per invoice)
  - Invoice generation with crypto amounts
  - On-chain payment verification (BTC, ETH, SOL, USDC)
  - Transaction monitoring and confirmation tracking
  - Automatic fiat conversion (via exchange API)
  - Refund processing (crypto-to-crypto)
  - Exchange rate caching and management
  - Payment history and reconciliation

### Management Panel: `pages/marketplace/CryptoPage.tsx`
- Crypto payment settings
- Wallet management (view addresses, balances)
- Payment history with blockchain explorer links
- Exchange rate overview
- Invoice verification status
- Fiat conversion settings

### CLI Commands
- `ipilot crypto balance`
- `ipilot crypto invoice create --amount 50 --currency BTC`
- `ipilot crypto invoice status <invoice_id>`
- `ipilot crypto transactions`

## API Endpoints
- `GET /api/marketplace/crypto/wallets` - List wallets
- `POST /api/marketplace/crypto/wallets` - Create wallet
- `GET /api/marketplace/crypto/wallets/{id}/balance` - Wallet balance
- `GET /api/marketplace/crypto/rates` - Exchange rates
- `POST /api/marketplace/crypto/invoices` - Create invoice
- `GET /api/marketplace/crypto/invoices` - List invoices
- `GET /api/marketplace/crypto/invoices/{id}` - Invoice status
- `GET /api/marketplace/crypto/transactions` - Transaction history
- `POST /api/marketplace/crypto/transactions/{id}/verify` - Verify tx
- `POST /api/marketplace/crypto/settings` - Update settings

## Data Models

### CryptoWallet
- id, user_id, currency (BTC/ETH/SOL/USDC)
- address, address_type (p2pkh/p2sh/bech32)
- label, is_default
- balance_confirmed, balance_unconfirmed
- total_received, total_sent
- created_at

### CryptoInvoice
- id, user_id, fiat_amount, fiat_currency
- crypto_amount, crypto_currency
- wallet_address, payment_uri (BIP21/EIP681)
- status (pending/partial/confirmed/completed/expired/refunded)
- required_confirmations, current_confirmations
- tx_hash, block_number
- created_at, expires_at, paid_at

### CryptoTransaction
- id, invoice_id, currency
- tx_hash, from_address, to_address
- amount, fee, confirmations
- status (pending/confirmed/failed)
- block_number, block_timestamp
- explorer_url

## Implementation Details
- Bitcoin: Electrum/bitcoind RPC for wallet management
- Ethereum: Web3.py for contract interaction
- Solana: solana-py for blockchain interaction
- USDC: ERC-20 contract interaction on Ethereum/Solana
- Exchange rates via CoinGecko/CoinMarketCap API
- Confirmation monitoring with configurable thresholds
- Invoice expiry (default 60 minutes)
- HD wallet derivation (BIP32/BIP44)
- Payment URI generation (BIP21 for BTC, EIP681 for ETH)
- Auto-conversion via exchange API (optional)

## Testing
- Wallet creation and address derivation
- Invoice generation with correct amounts
- Transaction verification (mock blockchain)
- Exchange rate fetching and caching
- Invoice expiry handling
- Partial payment detection
- Refund processing
