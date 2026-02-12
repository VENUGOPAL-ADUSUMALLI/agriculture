import json
import logging
from django.db.models import Sum, Avg
from petroleum.models import (
    CrudeOilProduction, RefineryProcessing,
    PetroleumProductProduction, PetroleumTrade,
)
from agri.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class PetroleumAnalyticsService:

    def __init__(self):
        self.ai_service = OpenAIService()

    # ─── Problem 1: Crude Oil Production Forecasting ────────────

    def get_crude_production_history(self, company_name=None):
        qs = CrudeOilProduction.objects.all()
        if company_name:
            qs = qs.filter(company_name=company_name)
        data = qs.values('year', 'company_name').annotate(
            total_quantity=Sum('quantity'),
        ).order_by('year', 'company_name')
        return list(data)

    def forecast_crude_production(self, company_name=None):
        historical = self.get_crude_production_history(company_name)
        if not historical:
            return {'error': 'No historical data available'}

        label = company_name or 'All Companies'
        prompt = f"""Based on this historical domestic crude oil production data
for {label} in India (quantity in 000 metric tonnes, yearly aggregated):

{json.dumps(historical, indent=2, default=str)}

India's domestic crude oil production has been declining. Predict production
for the next 3 years and assess import requirement implications.

Return ONLY valid JSON:
{{
  "forecast": [{{"year": <int>, "predicted_quantity": <float>}}],
  "trend": "<increasing|stable|declining>",
  "confidence": <0-1>,
  "import_implication": "<short paragraph>",
  "analysis": "<short paragraph>"
}}"""

        try:
            response = self.ai_service.client.chat.completions.create(
                model=self.ai_service.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are an Indian petroleum sector analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.3,
            )
            content = response.choices[0].message.content or ""
            return self.ai_service._extract_json(content)
        except Exception:
            logger.exception("Crude production forecast failed")
            return self._fallback_crude_forecast(historical, label)

    @staticmethod
    def _fallback_crude_forecast(historical, label):
        yearly = {}
        for row in historical:
            y = row['year']
            yearly.setdefault(y, 0)
            yearly[y] += row['total_quantity'] or 0
        if not yearly:
            return {'error': 'Insufficient data'}
        years = sorted(yearly.keys())
        latest = years[-1]
        latest_val = yearly[latest]
        growth = -0.02  # assume 2% decline for Indian crude
        forecast = []
        for i in range(1, 4):
            forecast.append({
                'year': latest + i,
                'predicted_quantity': round(latest_val * ((1 + growth) ** i), 2),
            })
        return {
            'forecast': forecast,
            'trend': 'declining',
            'confidence': 0.35,
            'import_implication': f'Fallback estimate: {label} production likely to continue declining.',
            'analysis': 'Fallback: AI unavailable. Estimated 2% annual decline applied.',
        }

    # ─── Problem 2: Refinery Utilization Analysis ───────────────

    def get_refinery_trends(self, refinery_name=None, year=None):
        qs = RefineryProcessing.objects.all()
        if refinery_name:
            qs = qs.filter(refinery_name=refinery_name)
        if year:
            qs = qs.filter(year=year)
        data = qs.values('year', 'refinery_name').annotate(
            total_processed=Sum('quantity'),
        ).order_by('year', 'refinery_name')
        return list(data)

    def get_refinery_seasonal_pattern(self, refinery_name=None):
        qs = RefineryProcessing.objects.all()
        if refinery_name:
            qs = qs.filter(refinery_name=refinery_name)
        data = qs.values('month').annotate(
            avg_quantity=Avg('quantity'),
        ).order_by('month')
        return list(data)

    # ─── Problem 3: Product-wise Demand-Supply Gap ──────────────

    def get_product_demand_supply_gap(self, product=None, year=None):
        prod_qs = PetroleumProductProduction.objects.all()
        if product:
            prod_qs = prod_qs.filter(product__icontains=product)
        if year:
            prod_qs = prod_qs.filter(year=year)
        production = prod_qs.values('product', 'year').annotate(
            domestic_production=Sum('quantity'),
        ).order_by('product', 'year')

        trade_qs = PetroleumTrade.objects.all()
        if product:
            trade_qs = trade_qs.filter(product__icontains=product)
        if year:
            trade_qs = trade_qs.filter(year=year)

        imports = trade_qs.filter(trade_type='Import').values(
            'product', 'year',
        ).annotate(
            import_quantity=Sum('quantity'),
            import_value_inr=Sum('value_inr_crore'),
        )
        exports = trade_qs.filter(trade_type='Export').values(
            'product', 'year',
        ).annotate(
            export_quantity=Sum('quantity'),
            export_value_inr=Sum('value_inr_crore'),
        )

        return {
            'production': list(production),
            'imports': list(imports),
            'exports': list(exports),
        }

    # ─── Problem 4: Import Dependency & Cost Analysis ───────────

    def get_import_cost_analysis(self, year=None):
        qs = PetroleumTrade.objects.filter(trade_type='Import')
        if year:
            qs = qs.filter(year=year)
        data = qs.values('year', 'product').annotate(
            total_quantity=Sum('quantity'),
            total_value_inr=Sum('value_inr_crore'),
            total_value_usd=Sum('value_usd_million'),
        ).order_by('year', 'product')
        return list(data)

    def forecast_import_costs(self):
        historical = self.get_import_cost_analysis()
        if not historical:
            return {'error': 'No import data available'}
        prompt = f"""Based on this historical petroleum import data for India
(quantity in 000 metric tonnes, value in INR Crore and USD Million):

{json.dumps(historical, indent=2, default=str)}

Predict India's crude oil and petroleum product import bill for the next 2 years.
Consider global oil price trends, domestic demand growth, and refining capacity.

Return ONLY valid JSON:
{{
  "forecast": [{{"year": <int>, "estimated_bill_inr_crore": <float>,
                  "estimated_bill_usd_million": <float>}}],
  "key_drivers": ["<string>"],
  "risk_factors": ["<string>"],
  "analysis": "<short paragraph>"
}}"""

        try:
            response = self.ai_service.client.chat.completions.create(
                model=self.ai_service.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are an Indian petroleum economics analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=600,
                temperature=0.3,
            )
            return self.ai_service._extract_json(
                response.choices[0].message.content or ""
            )
        except Exception:
            logger.exception("Import cost forecast failed")
            return {'error': 'AI forecast unavailable', 'confidence': 0.0}

    # ─── Problem 5: Trade Balance Dashboard ─────────────────────

    def get_trade_balance(self, year=None):
        qs = PetroleumTrade.objects.all()
        if year:
            qs = qs.filter(year=year)

        imports = qs.filter(trade_type='Import').values('product').annotate(
            import_qty=Sum('quantity'),
            import_value_inr=Sum('value_inr_crore'),
        )
        exports = qs.filter(trade_type='Export').values('product').annotate(
            export_qty=Sum('quantity'),
            export_value_inr=Sum('value_inr_crore'),
        )

        import_map = {r['product']: r for r in imports}
        export_map = {r['product']: r for r in exports}
        all_products = set(import_map.keys()) | set(export_map.keys())

        result = []
        for prod in sorted(all_products):
            imp = import_map.get(prod, {})
            exp = export_map.get(prod, {})
            imp_qty = imp.get('import_qty') or 0
            exp_qty = exp.get('export_qty') or 0
            net = exp_qty - imp_qty
            result.append({
                'product': prod,
                'import_quantity': imp_qty,
                'export_quantity': exp_qty,
                'net_quantity': round(net, 2),
                'status': 'net_exporter' if net > 0 else 'net_importer',
                'import_value_inr_crore': imp.get('import_value_inr') or 0,
                'export_value_inr_crore': exp.get('export_value_inr') or 0,
            })
        return result

    # ─── Problem 6: AI Market Intelligence ──────────────────────

    def generate_market_intelligence(self):
        crude = self.get_crude_production_history()
        refinery = self.get_refinery_trends()
        trade_balance = self.get_trade_balance()
        import_costs = self.get_import_cost_analysis()

        prompt = f"""You are an Indian petroleum sector intelligence analyst.

Based on the following data:

1. Domestic Crude Oil Production (000 MT, yearly):
{json.dumps(crude[-20:], indent=2, default=str)}

2. Refinery Processing (000 MT, yearly):
{json.dumps(refinery[-20:], indent=2, default=str)}

3. Trade Balance by Product:
{json.dumps(trade_balance[:15], indent=2, default=str)}

4. Import Costs:
{json.dumps(import_costs[-10:], indent=2, default=str)}

Generate a strategic market intelligence briefing.

Return ONLY valid JSON:
{{
  "headline": "<string>",
  "key_findings": [
    {{"title": "<string>", "detail": "<string>"}}
  ],
  "strategic_recommendations": ["<string>"],
  "risk_assessment": "<short paragraph>"
}}

Rules:
- 4 to 6 key findings.
- Focus on actionable insights for Indian policymakers.
- No markdown. No text outside JSON."""

        try:
            response = self.ai_service.client.chat.completions.create(
                model=self.ai_service.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are an expert petroleum sector analyst for India. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.3,
            )
            return self.ai_service._extract_json(
                response.choices[0].message.content or ""
            )
        except Exception:
            logger.exception("Market intelligence generation failed")
            return {
                'headline': 'Market Intelligence Unavailable',
                'key_findings': [
                    {'title': 'Service Error', 'detail': 'AI analysis could not be generated. Please try again later.'}
                ],
                'strategic_recommendations': [],
                'risk_assessment': 'Unable to assess at this time.',
            }
