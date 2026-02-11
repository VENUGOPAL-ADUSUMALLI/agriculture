import logging
from django.db.models import Sum, Max, Avg
from agri.models import (
    State, District, Crop, CropProduction, CropPrice,
    ProcurementQuery, ProcurementResult,
)
from agri.services.google_maps import GoogleMapsService
from agri.services.cost_calculator import CostCalculator

logger = logging.getLogger(__name__)


class OptimizationEngine:

    # Ranking weights (configurable)
    WEIGHT_COST = 0.50
    WEIGHT_DELIVERY = 0.25
    WEIGHT_CARBON = 0.25

    def __init__(self):
        self.maps_service = GoogleMapsService()
        self.cost_calc = CostCalculator()

    def find_suppliers(self, crop, exclude_state=None):
        latest_year = CropProduction.objects.filter(
            crop=crop
        ).aggregate(max_year=Max('crop_year'))['max_year']

        if not latest_year:
            return [], latest_year

        suppliers = CropProduction.objects.filter(
            crop=crop,
            crop_year=latest_year,
        ).values(
            'state__id', 'state__name'
        ).annotate(
            total_production=Sum('production'),
            total_area=Sum('area'),
        ).filter(
            total_production__gt=0
        ).order_by('-total_production')

        if exclude_state:
            suppliers = suppliers.exclude(state__id=exclude_state.id)

        return list(suppliers), latest_year

    def get_price(self, crop, state):
        price = CropPrice.objects.filter(
            crop=crop,
            state=state,
        ).order_by('-year').first()

        if price:
            return price.price_per_tonne

        avg = CropPrice.objects.filter(
            crop=crop
        ).aggregate(avg_price=Avg('price_per_tonne'))['avg_price']

        return avg or 20000

    def optimize_procurement(self, user, crop, source_state, source_district,
                             quantity_tonnes):
        query = ProcurementQuery.objects.create(
            user=user,
            crop=crop,
            source_state=source_state,
            source_district=source_district,
            required_quantity_tonnes=quantity_tonnes,
        )

        suppliers, latest_year = self.find_suppliers(crop, exclude_state=source_state)

        results = []

        for supplier in suppliers:
            supplier_state = State.objects.get(id=supplier['state__id'])
            available_supply = supplier['total_production']

            if available_supply < quantity_tonnes * 0.1:
                continue

            fulfillable = min(available_supply, quantity_tonnes)

            price_per_tonne = self.get_price(crop, supplier_state)

            distance_data = self.maps_service.get_distance(
                supplier_state, None,
                source_state, source_district,
            )
            distance_km = distance_data['distance_km']

            transport_cost = self.cost_calc.calculate_transportation_cost(
                distance_km, fulfillable)
            total_cost = self.cost_calc.calculate_total_cost(
                price_per_tonne, fulfillable, transport_cost)
            delivery_days = self.cost_calc.calculate_delivery_time_days(distance_km)
            carbon_kg = self.cost_calc.calculate_carbon_footprint(
                distance_km, fulfillable)

            result = ProcurementResult.objects.create(
                query=query,
                supplier_state=supplier_state,
                available_supply_tonnes=available_supply,
                price_per_tonne=price_per_tonne,
                transportation_cost=transport_cost,
                total_cost=total_cost,
                distance_km=distance_km,
                estimated_delivery_days=delivery_days,
                carbon_footprint_kg=carbon_kg,
            )
            results.append(result)

        self._rank_results(results)

        return query

    def _rank_results(self, results):
        if not results:
            return

        costs = [float(r.total_cost) for r in results]
        deliveries = [r.estimated_delivery_days for r in results]
        carbons = [r.carbon_footprint_kg for r in results]

        min_cost, max_cost = min(costs), max(costs)
        min_del, max_del = min(deliveries), max(deliveries)
        min_carb, max_carb = min(carbons), max(carbons)

        def normalize(val, mn, mx):
            if mx == mn:
                return 0.0
            return (val - mn) / (mx - mn)

        for r in results:
            norm_cost = normalize(float(r.total_cost), min_cost, max_cost)
            norm_delivery = normalize(r.estimated_delivery_days, min_del, max_del)
            norm_carbon = normalize(r.carbon_footprint_kg, min_carb, max_carb)

            r.ranking_score = (
                self.WEIGHT_COST * norm_cost
                + self.WEIGHT_DELIVERY * norm_delivery
                + self.WEIGHT_CARBON * norm_carbon
            )

        # Assign category labels
        by_cost = sorted(results, key=lambda r: float(r.total_cost))
        by_cost[0].ranking_category = 'best_cost'

        by_delivery = sorted(results, key=lambda r: r.estimated_delivery_days)
        by_delivery[0].ranking_category = 'fastest'

        by_carbon = sorted(results, key=lambda r: r.carbon_footprint_kg)
        by_carbon[0].ranking_category = 'lowest_carbon'

        for r in results:
            r.save()
