import json
import logging
import re
from datetime import datetime
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    MODEL_NAME = "gpt-4o-mini"
    MAX_POINT_COUNT = 6

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_procurement_summary(self, query, results):
        results_data = []
        for r in results:
            results_data.append({
                'state': r.supplier_state.name,
                'supply_tonnes': r.available_supply_tonnes,
                'price_per_tonne': float(r.price_per_tonne),
                'transport_cost': float(r.transportation_cost),
                'total_cost': float(r.total_cost),
                'distance_km': r.distance_km,
                'delivery_days': r.estimated_delivery_days,
                'carbon_kg': r.carbon_footprint_kg,
                'ranking': r.ranking_category,
                'transport_mode': r.transport_mode,
            })

        prompt = f"""You are an agricultural procurement advisor for the Indian government.

A state official from {query.source_state.name}, {query.source_district.name} needs
{query.required_quantity_tonnes} tonnes of {query.crop.name}.

Here are the available procurement options:
{json.dumps(results_data, indent=2)}

Return ONLY valid JSON in this exact shape:
{{
  "headline": "string",
  "points": [
    {{"title": "string", "detail": "string"}}
  ]
}}

Rules:
- Provide 4 to 6 points.
- Keep point details short and user-friendly.
- No markdown.
- No paragraphs outside JSON."""

        response = self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert agricultural advisor."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.3,
        )

        content = response.choices[0].message.content or ""
        return self._normalize_summary(content, query, results_data)

    def _normalize_summary(self, content, query, results_data):
        try:
            parsed = self._extract_json(content)
            headline = str(parsed.get('headline', '')).strip()
            points = parsed.get('points', [])
            if not headline or not isinstance(points, list):
                raise ValueError("Missing required summary fields")

            cleaned_points = []
            for item in points[:self.MAX_POINT_COUNT]:
                if not isinstance(item, dict):
                    continue
                title = str(item.get('title', '')).strip()[:120]
                detail = str(item.get('detail', '')).strip()[:500]
                if title and detail:
                    cleaned_points.append({'title': title, 'detail': detail})

            if len(cleaned_points) < 2:
                raise ValueError("Insufficient valid points in summary payload")

            return {
                'headline': headline[:200],
                'points': cleaned_points,
            }
        except Exception:
            logger.exception("Failed to parse AI procurement summary, using fallback.")
            return self._fallback_summary(query, results_data)

    @staticmethod
    def _extract_json(content):
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    @staticmethod
    def _fallback_summary(query, results_data):
        if not results_data:
            return {
                'headline': f"No procurement options available for {query.crop.name}",
                'points': [
                    {
                        'title': 'No supplier options',
                        'detail': 'No ranked supplier records were available for this query.',
                    }
                ],
            }

        best_cost = min(results_data, key=lambda x: x['total_cost'])
        fastest = min(results_data, key=lambda x: x['delivery_days'])
        lowest_carbon = min(results_data, key=lambda x: x['carbon_kg'])
        worst_cost = max(results_data, key=lambda x: x['total_cost'])
        savings = max(0.0, worst_cost['total_cost'] - best_cost['total_cost'])

        return {
            'headline': f"Procurement summary for {query.crop.name} in {query.source_state.name}",
            'points': [
                {
                    'title': 'Best cost option',
                    'detail': f"{best_cost['state']} ({best_cost['transport_mode']}) at INR {best_cost['total_cost']:.2f} total.",
                },
                {
                    'title': 'Fastest delivery',
                    'detail': f"{fastest['state']} can deliver in about {fastest['delivery_days']} days.",
                },
                {
                    'title': 'Lowest carbon option',
                    'detail': f"{lowest_carbon['state']} has the lowest footprint at {lowest_carbon['carbon_kg']:.2f} kg CO2e.",
                },
                {
                    'title': 'Estimated savings',
                    'detail': f"Choosing the best-cost option can save about INR {savings:.2f} vs highest-cost option.",
                },
            ],
        }

    def predict_demand(self, crop_name, state_name, historical_data):
        current_year = datetime.now().year
        target_years = [current_year + i for i in range(1, 6)]

        prompt = f"""You are forecasting agricultural demand for policy planning.
Current year: {current_year}
Crop: {crop_name}
State scope: {state_name}

Historical production data:
{json.dumps(historical_data, indent=2)}

Return ONLY valid JSON in this exact schema:
{{
  "trend": "<increasing|stable|decreasing>",
  "confidence": <number between 0 and 1>,
  "analysis": "<concise paragraph>",
  "forecast": [
    {{
      "year": <int>,
      "predicted_demand_tonnes": <number>,
      "confidence": <number between 0 and 1>,
      "suggestion": "<short action-oriented suggestion>"
    }}
  ]
}}
Rules:
- Forecast must have exactly 5 entries for years: {target_years}.
- Use one entry per year.
- No markdown.
- No extra keys."""

        response = self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an agricultural forecasting expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=700,
            temperature=0.3,
        )

        content = response.choices[0].message.content or ""
        return self._normalize_next5_prediction(
            content=content,
            historical_data=historical_data,
            current_year=current_year,
            target_years=target_years,
        )

    def _normalize_next5_prediction(self, content, historical_data, current_year, target_years):
        def normalize_trend(value):
            v = str(value).strip().lower()
            if v in {'increasing', 'stable', 'decreasing'}:
                return v
            return 'stable'

        def clamp_confidence(value, default=0.5):
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                parsed = default
            return round(max(0.0, min(1.0, parsed)), 2)

        try:
            parsed = self._extract_json(content)
            forecast = parsed.get('forecast')
            if not isinstance(forecast, list):
                raise ValueError("forecast must be a list")

            by_year = {}
            for item in forecast:
                if not isinstance(item, dict):
                    continue
                year = int(item.get('year'))
                if year not in target_years:
                    continue
                by_year[year] = {
                    'year': year,
                    'predicted_demand_tonnes': round(max(0.0, float(item.get('predicted_demand_tonnes'))), 2),
                    'confidence': clamp_confidence(item.get('confidence'), default=parsed.get('confidence', 0.5)),
                    'suggestion': str(item.get('suggestion', '')).strip()[:220] or "Monitor supply-demand gap and prepare procurement early.",
                }

            if len(by_year) != len(target_years):
                raise ValueError("forecast does not cover all target years")

            return {
                'current_year': current_year,
                'trend': normalize_trend(parsed.get('trend', 'stable')),
                'confidence': clamp_confidence(parsed.get('confidence', 0.5)),
                'analysis': str(parsed.get('analysis', '')).strip()[:1200] or 'AI-generated outlook based on historical production trends.',
                'forecast': [by_year[year] for year in target_years],
            }
        except Exception:
            logger.exception("Failed to parse AI 5-year demand prediction, using fallback.")
            return self._fallback_next5_prediction(
                historical_data=historical_data,
                current_year=current_year,
                target_years=target_years,
            )

    @staticmethod
    def _fallback_next5_prediction(historical_data, current_year, target_years):
        production_points = [
            float(item.get('production')) for item in historical_data
            if item.get('production') is not None
        ]
        latest_year = max((item.get('year', current_year) for item in historical_data), default=current_year)

        if not production_points:
            baseline = 0.0
            growth = 0.0
        elif len(production_points) == 1:
            baseline = production_points[-1]
            growth = 0.03
        else:
            baseline = production_points[-1]
            prev = production_points[-2]
            if prev <= 0:
                growth = 0.02
            else:
                growth = max(-0.15, min(0.15, (baseline - prev) / prev))

        if growth > 0.01:
            trend = 'increasing'
            suggestion = "Strengthen procurement planning and storage capacity."
        elif growth < -0.01:
            trend = 'decreasing'
            suggestion = "Plan early procurement and consider demand-side rationing buffers."
        else:
            trend = 'stable'
            suggestion = "Maintain current procurement strategy with periodic monitoring."

        forecast = []
        for year in target_years:
            years_from_baseline = max(1, year - latest_year)
            demand = baseline * ((1 + growth) ** years_from_baseline)
            forecast.append({
                'year': year,
                'predicted_demand_tonnes': round(max(0.0, demand), 2),
                'confidence': 0.35,
                'suggestion': suggestion,
            })

        return {
            'current_year': current_year,
            'trend': trend,
            'confidence': 0.35,
            'analysis': (
                "Fallback 5-year forecast generated from historical production trend "
                "because AI response was unavailable or invalid."
            ),
            'forecast': forecast,
        }

    def estimate_crop_price(self, crop_name, state_name):
        prompt = f"""What is the approximate current market price (in INR per tonne) for {crop_name}
in {state_name}, India? Consider MSP and typical mandi prices.
Return JSON: {{"price_per_tonne": <number>, "source": "estimated", "confidence": "<low/medium/high>"}}
Only return the JSON."""

        response = self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an Indian agricultural market expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.3,
        )

        return json.loads(response.choices[0].message.content)

    def generate_surplus_deficit_insight(self, crop_name, demand, supply_low, supply_high):
        prompt = f"""You are a policy analyst for Indian agriculture.

Crop: {crop_name}
Projected demand (million tonnes): {demand}
Projected supply range (million tonnes): {supply_low} to {supply_high}

Write one concise plain-text insight in this style:
"Is {crop_name} in surplus or deficit nationally? — ... better act fast."

Rules:
- 1 to 2 sentences only.
- Mention demand and supply numbers.
- Clearly state surplus/deficit/tight balance.
- No markdown."""

        response = self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You provide crisp, actionable policy insights."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=140,
            temperature=0.2,
        )
        return (response.choices[0].message.content or "").strip()
