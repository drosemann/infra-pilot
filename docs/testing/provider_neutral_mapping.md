# Provider Neutral Mapping

Overview
- Use neutral tokens in tests to decouple from real cloud providers.
- A resolver translates tokens to concrete provider identities for the test run.

Files
- infra/naming/provider_map.yaml: base mapping
- infra/overrides/provider_map.yaml: environment-specific overrides
- infra/naming/resolver.py: token resolver API

Example
- Provider map (provider_map.yaml):
  PROVIDER_MOCK: mock-provider
- Overrides (overrides/provider_map.yaml):
  PROVIDER_MOCK: mock-provider-ci

Usage
- In tests: from infra.naming import resolver; provider = resolver.resolve_provider("PROVIDER_MOCK");
- Use REGION_MOCK_US_EAST, SKU_MOCK_SMALL similarly; all tokens map via resolver
