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

    def predict_demand(self, crop_name, state_name, historical_data, years=5):
        latest_year = max((item.get('year', 0) for item in historical_data), default=datetime.now().year)

        prompt = f"""Based on this historical production data for {crop_name} in {state_name}:

{json.dumps(historical_data, indent=2)}

Predict expected production for the next {years} years starting from year {latest_year + 1}.
Return ONLY valid JSON in this exact format:
{{
  "overall_confidence": "<low|medium|high>",
  "assumptions": ["string", "string"],
  "forecast": [
    {{
      "year": <int>,
      "predicted_production_tonnes": <number>,
      "confidence": "<low|medium|high>",
      "reasoning": "<short text>"
    }}
  ]
}}
Rules:
- forecast must contain exactly {years} items.
- No markdown.
- No extra keys outside this JSON."""

        response = self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an agricultural data scientist. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=700,
            temperature=0.3,
        )

        content = response.choices[0].message.content or ""
        return self._normalize_forecast(content, historical_data, years, latest_year)

    def _normalize_forecast(self, content, historical_data, years, latest_year):
        def valid_confidence(value):
            v = str(value).strip().lower()
            return v if v in ('low', 'medium', 'high') else 'medium'

        try:
            parsed = self._extract_json(content)
            forecast = parsed.get('forecast', [])
            if not isinstance(forecast, list):
                raise ValueError("forecast must be a list")

            cleaned = []
            for index, item in enumerate(forecast[:years]):
                if not isinstance(item, dict):
                    continue
                year = int(item.get('year', latest_year + index + 1))
                production = float(item.get('predicted_production_tonnes'))
                cleaned.append({
                    'year': year,
                    'predicted_production_tonnes': round(max(0.0, production), 2),
                    'confidence': valid_confidence(item.get('confidence', parsed.get('overall_confidence', 'medium'))),
                    'reasoning': str(item.get('reasoning', '')).strip()[:220],
                })

            if len(cleaned) != years:
                raise ValueError("insufficient forecast points")

            cleaned = sorted(cleaned, key=lambda x: x['year'])
            return {
                'years_requested': years,
                'overall_confidence': valid_confidence(parsed.get('overall_confidence', 'medium')),
                'assumptions': [str(a).strip()[:180] for a in parsed.get('assumptions', []) if str(a).strip()][:4],
                'forecast': cleaned,
            }
        except Exception:
            logger.exception("Failed to parse AI demand forecast, using fallback.")
            return self._fallback_forecast(historical_data, years, latest_year)

    @staticmethod
    def _fallback_forecast(historical_data, years, latest_year):
        production_points = [
            float(item.get('production')) for item in historical_data
            if item.get('production') is not None
        ]
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

        forecast = []
        current = baseline
        for offset in range(1, years + 1):
            current = current * (1 + growth)
            forecast.append({
                'year': latest_year + offset,
                'predicted_production_tonnes': round(max(0.0, current), 2),
                'confidence': 'low',
                'reasoning': 'Fallback trend estimate based on recent historical production.',
            })

        return {
            'years_requested': years,
            'overall_confidence': 'low',
            'assumptions': ['Fallback generated from historical trend due to AI response parsing failure.'],
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
