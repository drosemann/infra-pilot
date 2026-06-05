# Feature 31: Resource Trading Platform

## Overview
Peer-to-peer marketplace where users can buy and sell unused CPU, RAM, and storage resources. Smart contract-based escrow, provider reputation scores, and automated resource allocation.

## Components

### Integration Service: `marketplace/resource_trading.py`
- `ResourceTradingManager` - Core trading platform
  - Listing management (create/update/delete listings)
  - Order lifecycle (buy/sell/fulfill/dispute/complete)
  - Smart contract escrow integration
  - Provider reputation scoring
  - Resource validation and allocation
  - Transaction history
  - Dispute resolution workflow
  - Automated pricing suggestions

### Orchestrator Agent: `cogs/trading_manager.py`
- Discord commands:
  - `/trading list create` - Create resource listing
  - `/trading list cancel` - Cancel listing
  - `/trading search` - Search resources
  - `/trading order buy` - Buy resources
  - `/trading order status` - Check order status
  - `/trading reputation` - Check provider reputation

### Management Panel: `pages/marketplace/TradingPage.tsx`
- Marketplace overview with search/filter
- Listing creation wizard
- Order management dashboard
- Reputation scores and reviews
- Transaction history
- Dispute center
- Pricing analytics

### CLI Commands
- `ipilot trading list --type sell --cpu 4 --ram 8 --price 0.05`
- `ipilot trading search --cpu > 2`
- `ipilot trading order <listing_id> --hours 24`

## API Endpoints
- `GET /api/marketplace/trading/listings` - Search listings
- `POST /api/marketplace/trading/listings` - Create listing
- `PUT /api/marketplace/trading/listings/{id}` - Update listing
- `DELETE /api/marketplace/trading/listings/{id}` - Delete listing
- `GET /api/marketplace/trading/listings/{id}` - Get listing
- `POST /api/marketplace/trading/orders` - Create order
- `GET /api/marketplace/trading/orders` - User's orders
- `GET /api/marketplace/trading/orders/{id}` - Order details
- `PUT /api/marketplace/trading/orders/{id}/fulfill` - Fulfill order
- `PUT /api/marketplace/trading/orders/{id}/dispute` - Open dispute
- `PUT /api/marketplace/trading/orders/{id}/complete` - Complete order
- `GET /api/marketplace/trading/reputation/{user_id}` - Get reputation
- `GET /api/marketplace/trading/transactions` - Transaction history

## Data Models

### ResourceListing
- id, seller_id, resource_type (cpu/ram/storage/gpu)
- quantity, unit (core/gb/tb), price_per_unit_hour
- total_available, available_now
- location, provider, server_id
- min_duration_hours, max_duration_hours
- status (active/paused/sold/expired)
- tags, description
- created_at, expires_at

### TradeOrder
- id, listing_id, buyer_id, seller_id
- quantity, duration_hours, total_price
- status (pending/active/fulfilled/dispute/completed/cancelled)
- escrow_status (funded/released/refunded)
- dispute_reason, dispute_evidence
- created_at, completed_at

### ReputationScore
- user_id, overall_score (1-5)
- total_trades, completed_trades
- cancelled_trades, disputed_trades
- response_time_avg, fulfillment_rate
- recent_reviews (list of Review objects)

## Implementation Details
- Escrow via smart contracts (Ethereum/L2)
- Resource allocation via Docker/Kubernetes
- Reputation scoring with time decay
- Automated pricing based on supply/demand
- Dispute resolution with mediation
- Resource validation before listing
- Scheduled fulfillment with start/end times
- Integration with billing system for payments

## Testing
- Listing CRUD operations
- Order lifecycle state machine
- Escrow fund/release mechanics
- Reputation scoring algorithm
- Pricing suggestion accuracy
- Dispute resolution workflow
