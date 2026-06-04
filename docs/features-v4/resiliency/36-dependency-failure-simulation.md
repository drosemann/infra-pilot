# Feature 36: Dependency Failure Simulation

## Overview
Simulate failure of upstream dependencies (database, API, queue) to test circuit breaker, retry, and fallback logic. Report blast radius.

## Components
- `dependency_simulator.py` - Simulation engine with 8 failure types
- `DependencySimulatorCog` - Discord commands
- `DependencySimulator.tsx` - Management panel UI

## Failure Types
- Timeout, error response, slow response
- Connection refused, DNS failure
- Rate limiting, data corruption
- Circuit breaker open

## API Endpoints
- `GET /api/v1/resiliency/dependency/simulations` - List simulations
- `POST /api/v1/resiliency/dependency/simulations` - Create simulation
- `POST /api/v1/resiliency/dependency/simulations/{id}/run` - Run simulation
