# provider neutral mapping

overview
• use neutral tokens in tests to decouple from real cloud providers.
• a resolver translates tokens to concrete provider identities for the test run.

files
• `infra/naming/provider_map.yaml`: base mapping
• `infra/overrides/provider_map.yaml`: environment-specific overrides
• `infra/naming/resolver.py`: token resolver api

example
• provider map (`provider_map.yaml`):
  `provider_mock: mock-provider`
• overrides (`overrides/provider_map.yaml`):
  `provider_mock: mock-provider-ci`

usage
• in tests: `from infra.naming import resolver; provider = resolver.resolve_provider("provider_mock");`
• use `region_mock_us_east`, `sku_mock_small` similarly; all tokens map via resolver
