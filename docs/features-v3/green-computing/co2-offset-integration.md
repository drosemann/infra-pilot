# Feature 20: CO2 Offset Integration

## Overview
One-click purchase of carbon offsets via Patch or ClimateTech API. Auto-offset based on monthly usage. Certificate generation for ESG reporting.

## Capabilities
- One-click carbon offset purchase
- Integration with Patch API (carbon offset marketplace)
- Integration with ClimateTech / CarbonJack API
- Monthly auto-offset based on measured energy usage
- Offset project selection (reforestation, renewable energy, direct air capture)
- Offset cost estimation pre-purchase
- Carbon offset certificate generation (PDF)
- Offset history and tracking
- Tax receipt generation
- Budget limits for offset spending

## Offset Providers

| Provider | Projects | Minimum Purchase | API Availability |
|----------|----------|-----------------|-----------------|
| Patch | Reforestation, Renewable, DAC, Soil | $1.00 | REST API |
| ClimateTech | Reforestation, Renewable | $5.00 | REST API |
| CarbonJack | Reforestation, Blue Carbon | $10.00 | REST API |
| Terrapass | Renewable, Methane | $5.00 | REST API |

## Offset Flow

```python
class CO2OffsetManager:
    """Manage carbon offset purchases."""
    
    async def calculate_offset_amount(self, 
                                      period_start: datetime,
                                      period_end: datetime) -> OffsetQuote:
        """Calculate CO2 emitted in period and offset cost."""
        # Get energy consumption for period
        energy_data = await self.energy_tracker.get_period_consumption(
            period_start, period_end
        )
        
        total_kwh = sum(m.total_energy_kwh for m in energy_data)
        total_co2_kg = sum(m.co2_grams for m in energy_data) / 1000
        
        # Get quote
        quote = await self.provider.get_quote(
            co2_kg=total_co2_kg,
            project_type="reforestation"
        )
        
        return OffsetQuote(
            co2_kg=total_co2_kg,
            energy_kwh=total_kwh,
            project_name=quote.project_name,
            cost_per_ton=quote.cost_per_ton,
            total_cost=quote.total_cost,
            currency=quote.currency,
            valid_until=quote.valid_until
        )
    
    async def purchase_offset(self, 
                              quote: OffsetQuote,
                              auto_approve: bool = False) -> OffsetCertificate:
        """Purchase carbon offset."""
        if not auto_approve:
            await self._require_approval(quote)
        
        if quote.total_cost > self.config.max_offset_budget:
            raise BudgetExceededError(
                f"Offset cost ${quote.total_cost:.2f} exceeds "
                f"budget ${self.config.max_offset_budget:.2f}"
            )
        
        # Purchase
        receipt = await self.provider.purchase(
            co2_kg=quote.co2_kg,
            project_id=quote.project_id,
            metadata={
                "source": "infra_pilot",
                "period": self._current_period()
            }
        )
        
        # Generate certificate
        cert = await self._generate_certificate(
            receipt=receipt,
            project=quote.project_name,
            co2_kg=quote.co2_kg
        )
        
        # Record in history
        await self._record_purchase(receipt, cert)
        
        return cert
    
    async def setup_auto_offset(self, 
                                 budget_monthly: float,
                                 project_type: str = "reforestation"):
        """Setup monthly automatic offset."""
        config = AutoOffsetConfig(
            enabled=True,
            budget_monthly=budget_monthly,
            project_type=project_type,
            day_of_month=1,
            notify_before=True,
            notify_after=True,
            max_price_per_ton=50.0
        )
        
        await self.config_store.set("auto_offset", config.to_dict())
        
        # Schedule monthly job
        await self.scheduler.add_job(
            name="auto_co2_offset",
            cron="0 12 1 * *",
            job_func=self._execute_auto_offset
        )
```

## Offset Certificate

The generated certificate includes:
- Certificate ID (UUID)
- Infra Pilot user/org name
- Offset amount (kg CO2)
- Project name and location
- Project type (reforestation, renewable, DAC)
- Vintage year
- Serial numbers (from registry)
- Purchase date
- QR code for verification

## Implementation
- Primary service: Integration Service
- Module: `services/integration-service/src/co2_offset_integration.py`
- CLI commands for offset purchase
- Management panel for offset dashboard
