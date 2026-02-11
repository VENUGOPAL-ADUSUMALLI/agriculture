import json
import logging
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenAIService:

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
            })

        prompt = f"""You are an agricultural procurement advisor for the Indian government.

A state official from {query.source_state.name}, {query.source_district.name} needs
{query.required_quantity_tonnes} tonnes of {query.crop.name}.

Here are the available procurement options:
{json.dumps(results_data, indent=2)}

Provide a concise summary (3-4 paragraphs):
1. Best overall recommendation and why
2. Trade-offs between cost, delivery speed, and carbon footprint
3. Any seasonal or strategic considerations
4. Estimated savings compared to worst-case scenario

Return as plain text."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert agricultural advisor."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.7,
        )

        return response.choices[0].message.content

    def predict_demand(self, crop_name, state_name, historical_data):
        prompt = f"""Based on this historical production data for {crop_name} in {state_name}:

{json.dumps(historical_data, indent=2)}

Predict the expected demand/production for the next 2 years.
Return JSON with format: {{"prediction_year_1": <tonnes>, "prediction_year_2": <tonnes>, "confidence": "<low/medium/high>", "reasoning": "<brief explanation>"}}
Only return the JSON, no other text."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an agricultural data scientist. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.3,
        )

        return json.loads(response.choices[0].message.content)

    def estimate_crop_price(self, crop_name, state_name):
        prompt = f"""What is the approximate current market price (in INR per tonne) for {crop_name}
in {state_name}, India? Consider MSP and typical mandi prices.
Return JSON: {{"price_per_tonne": <number>, "source": "estimated", "confidence": "<low/medium/high>"}}
Only return the JSON."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an Indian agricultural market expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.3,
        )

        return json.loads(response.choices[0].message.content)
