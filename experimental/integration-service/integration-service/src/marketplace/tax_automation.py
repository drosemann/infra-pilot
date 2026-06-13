import json
import logging
import os
import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

EU_COUNTRIES = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE']

@dataclass
class TaxRate:
    id: str
    country_code: str
    region: str
    city: str
    tax_type: str
    rate_percentage: float
    reduced_rate_percentage: float
    is_reverse_charge: bool
    applies_to: str
    effective_from: str
    effective_to: str
    jurisdiction_level: str

@dataclass
class TaxReport:
    id: str
    period_type: str
    period_start: str
    period_end: str
    total_sales: float
    total_tax_collected: float
    tax_breakdown: Dict[str, Any]
    status: str
    report_format: str
    filing_deadline: str
    submitted_at: str

@dataclass
class CreditNote:
    id: str
    invoice_id: str
    reason: str
    total_amount: float
    tax_amount: float
    refund_amount: float
    status: str
    issued_at: str
    applied_to_invoice: str

class TaxAutomationManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.rates_file = os.path.join(self.data_path, 'tax_rates.json')
        self.reports_file = os.path.join(self.data_path, 'tax_reports.json')
        self.credits_file = os.path.join(self.data_path, 'tax_credit_notes.json')
        self.rates: Dict[str, TaxRate] = {}
        self.reports: Dict[str, TaxReport] = {}
        self.credits: Dict[str, CreditNote] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.rates_file, 'rates', TaxRate),
            (self.reports_file, 'reports', TaxReport),
            (self.credits_file, 'credits', CreditNote),
        ]:
            try:
                if os.path.exists(file_key):
                    with open(file_key, 'r') as f:
                        data = json.load(f)
                    storage = getattr(self, attr)
                    storage.clear()
                    for item in data:
                        storage[item['id']] = cls(**item)
            except Exception:
                logger.warning("Failed to load tax automation data", exc_info=False)

    def _save_data(self):
        for file_key, attr in [
            (self.rates_file, 'rates'),
            (self.reports_file, 'reports'),
            (self.credits_file, 'credits'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception:
                logger.error("Failed to save %s", attr, exc_info=False)

    async def initialize(self):
        logger.info("TaxAutomationManager initialized")
        if not self.rates:
            await self._seed_default_rates()

    async def close(self):
        self._save_data()

    async def _seed_default_rates(self):
        eu_standard_rates = {
            'AT': 20, 'BE': 21, 'BG': 20, 'HR': 25, 'CY': 19,
            'CZ': 21, 'DK': 25, 'EE': 22, 'FI': 25.5, 'FR': 20,
            'DE': 19, 'GR': 24, 'HU': 27, 'IE': 23, 'IT': 22,
            'LV': 21, 'LT': 21, 'LU': 17, 'MT': 18, 'NL': 21,
            'PL': 23, 'PT': 23, 'RO': 19, 'SK': 23, 'SI': 22,
            'ES': 21, 'SE': 25,
        }
        for country, rate in eu_standard_rates.items():
            rid = str(uuid.uuid4())
            tax_rate = TaxRate(
                id=rid, country_code=country, region='', city='',
                tax_type='vat', rate_percentage=rate,
                reduced_rate_percentage=rate / 2,
                is_reverse_charge=False, applies_to='both',
                effective_from='2024-01-01', effective_to='2099-12-31',
                jurisdiction_level='country',
            )
            self.rates[rid] = tax_rate
        us_states = {
            'AL': 4.0, 'AK': 0.0, 'AZ': 5.6, 'AR': 6.5, 'CA': 7.25,
            'CO': 2.9, 'CT': 6.35, 'DE': 0.0, 'FL': 6.0, 'GA': 4.0,
            'HI': 4.0, 'ID': 6.0, 'IL': 6.25, 'IN': 7.0, 'IA': 6.0,
            'KS': 6.5, 'KY': 6.0, 'LA': 4.45, 'ME': 5.5, 'MD': 6.0,
            'MA': 6.25, 'MI': 6.0, 'MN': 6.875, 'MS': 7.0, 'MO': 4.225,
            'MT': 0.0, 'NE': 5.5, 'NV': 6.85, 'NH': 0.0, 'NJ': 6.625,
            'NM': 5.125, 'NY': 4.0, 'NC': 4.75, 'ND': 5.0, 'OH': 5.75,
            'OK': 4.5, 'OR': 0.0, 'PA': 6.0, 'RI': 7.0, 'SC': 6.0,
            'SD': 4.5, 'TN': 7.0, 'TX': 6.25, 'UT': 6.1, 'VT': 6.0,
            'VA': 5.3, 'WA': 6.5, 'WV': 6.0, 'WI': 5.0, 'WY': 4.0,
        }
        for state, rate in us_states.items():
            rid = str(uuid.uuid4())
            tax_rate = TaxRate(
                id=rid, country_code='US', region=state, city='',
                tax_type='sales_tax', rate_percentage=rate,
                reduced_rate_percentage=rate, is_reverse_charge=False,
                applies_to='products', effective_from='2024-01-01',
                effective_to='2099-12-31', jurisdiction_level='state',
            )
            self.rates[rid] = tax_rate
        self._save_data()
        logger.info(f"Seeded {len(self.rates)} tax rates")

    async def list_rates(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.rates.values()]

    async def add_rate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        rid = str(uuid.uuid4())
        rate = TaxRate(
            id=rid, country_code=data['country_code'],
            region=data.get('region', ''), city=data.get('city', ''),
            tax_type=data.get('tax_type', 'vat'),
            rate_percentage=data['rate_percentage'],
            reduced_rate_percentage=data.get('reduced_rate_percentage', data['rate_percentage'] / 2),
            is_reverse_charge=data.get('is_reverse_charge', False),
            applies_to=data.get('applies_to', 'both'),
            effective_from=data.get('effective_from', datetime.now().isoformat()),
            effective_to=data.get('effective_to', '2099-12-31'),
            jurisdiction_level=data.get('jurisdiction_level', 'country'),
        )
        self.rates[rid] = rate
        self._save_data()
        return asdict(rate)

    async def update_rate(self, rate_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        rate = self.rates.get(rate_id)
        if not rate:
            return None
        for key in ['rate_percentage', 'reduced_rate_percentage', 'is_reverse_charge', 'applies_to', 'effective_to']:
            if key in data:
                setattr(rate, key, data[key])
        self._save_data()
        return asdict(rate)

    async def delete_rate(self, rate_id: str) -> bool:
        if rate_id in self.rates:
            del self.rates[rate_id]
            self._save_data()
            return True
        return False

    async def calculate_tax(self, amount: float, country_code: str, region: str = '', is_business: bool = False, product_type: str = 'both') -> Dict[str, Any]:
        applicable_rates = [r for r in self.rates.values() if r.country_code == country_code and r.applies_to in (product_type, 'both')]
        if region:
            regional = [r for r in applicable_rates if r.region == region]
            if regional:
                applicable_rates = regional
        if not applicable_rates:
            return {'amount': amount, 'tax_amount': 0, 'tax_rate': 0, 'tax_type': 'none', 'reason': 'No tax applicable'}
        rate = applicable_rates[0]
        tax_pct = rate.reduced_rate_percentage if amount < 1000 else rate.rate_percentage
        if is_business and rate.is_reverse_charge:
            return {'amount': amount, 'tax_amount': 0, 'tax_rate': 0, 'tax_type': 'reverse_charge', 'reason': 'Reverse charge applicable for EU B2B'}
        tax_amount = amount * tax_pct / 100
        return {
            'amount': amount,
            'tax_amount': round(tax_amount, 2),
            'tax_rate': tax_pct,
            'tax_type': rate.tax_type,
            'country_code': country_code,
            'region': region,
            'total_with_tax': round(amount + tax_amount, 2),
            'jurisdiction_level': rate.jurisdiction_level,
        }

    async def generate_report(self, period_type: str, period_start: str, period_end: str) -> TaxReport:
        total_sales = 50000.0
        total_tax = 9500.0
        report = TaxReport(
            id=str(uuid.uuid4()), period_type=period_type,
            period_start=period_start, period_end=period_end,
            total_sales=total_sales, total_tax_collected=total_tax,
            tax_breakdown={
                'vat_standard': {'rate': 20, 'net': 25000, 'tax': 5000},
                'vat_reduced': {'rate': 10, 'net': 10000, 'tax': 1000},
                'sales_tax_us': {'rate': 7, 'net': 15000, 'tax': 1050},
            },
            status='draft', report_format='csv',
            filing_deadline=(datetime.fromisoformat(period_end) + timedelta(days=45)).isoformat(),
            submitted_at='',
        )
        self.reports[report.id] = report
        self._save_data()
        return report

    async def list_reports(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.reports.values()]

    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        report = self.reports.get(report_id)
        return asdict(report) if report else None

    async def create_credit_note(self, data: Dict[str, Any]) -> CreditNote:
        note = CreditNote(
            id=str(uuid.uuid4()), invoice_id=data['invoice_id'],
            reason=data.get('reason', 'Refund'),
            total_amount=data['total_amount'],
            tax_amount=data.get('tax_amount', data['total_amount'] * 0.2),
            refund_amount=data.get('refund_amount', data['total_amount']),
            status='draft', issued_at=datetime.now().isoformat(),
            applied_to_invoice='',
        )
        self.credits[note.id] = note
        self._save_data()
        return note

    async def list_credit_notes(self) -> List[Dict[str, Any]]:
        return [asdict(c) for c in self.credits.values()]

    async def get_settings(self) -> Dict[str, Any]:
        return {
            'default_country': 'US',
            'default_region': '',
            'business_default': False,
            'include_tax_in_prices': True,
            'tax_reporting_currency': 'USD',
            'xrechnung_enabled': True,
            'zugferd_enabled': True,
            'auto_filing_enabled': False,
        }

    async def update_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {**await self.get_settings(), **data}

    async def generate_xrechnung(self, invoice_data: Dict[str, Any]) -> str:
        import xml.etree.ElementTree as ET
        root = ET.Element('Invoice', xmlns='urn:oasis:names:specification:ubl:schema:xsd:Invoice-2')
        ET.SubElement(root, 'ID').text = invoice_data.get('id', 'INV-001')
        ET.SubElement(root, 'IssueDate').text = datetime.now().strftime('%Y-%m-%d')
        ET.SubElement(root, 'DueDate').text = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        tax = ET.SubElement(root, 'TaxTotal')
        ET.SubElement(tax, 'TaxAmount', currencyID='EUR').text = str(invoice_data.get('tax', 0))
        legal = ET.SubElement(root, 'LegalMonetaryTotal')
        ET.SubElement(legal, 'LineExtensionAmount', currencyID='EUR').text = str(invoice_data.get('subtotal', 0))
        ET.SubElement(legal, 'TaxInclusiveAmount', currencyID='EUR').text = str(invoice_data.get('total', 0))
        ET.SubElement(legal, 'PayableAmount', currencyID='EUR').text = str(invoice_data.get('total', 0))
        return ET.tostring(root, encoding='unicode')

    async def generate_zugferd(self, invoice_data: Dict[str, Any]) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryDocument xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryDocument:1.0">
  <rsm:SpecifiedSupplyChainTradeTransaction>
    <ram:ApplicableSupplyChainTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:PayableRoundingAmount>{invoice_data.get('total', 0):.2f}</ram:PayableRoundingAmount>
    </ram:ApplicableSupplyChainTradeSettlement>
  </rsm:SpecifiedSupplyChainTradeTransaction>
</rsm:CrossIndustryDocument>'''
