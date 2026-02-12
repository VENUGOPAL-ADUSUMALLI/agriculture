from decimal import Decimal

# Road transport constants
TRANSPORT_RATE_PER_KM_PER_TONNE = Decimal('2.50')
AVG_TRUCK_SPEED_KMH = 40.0
LOADING_TIME_HOURS = 24.0
CO2_EMISSION_FACTOR = 0.062

# Railway transport constants
AVG_RAIL_SPEED_KMH = 25.0
RAIL_LOADING_TIME_HOURS = 48.0
RAIL_CO2_EMISSION_FACTOR = 0.022
TRAIN_LOAD_THRESHOLD_TONNES = 2400


class CostCalculator:

    # ─── Road Methods ─────────────────────────────────────────────

    @staticmethod
    def calculate_transportation_cost(distance_km, quantity_tonnes):
        return (
            Decimal(str(distance_km))
            * TRANSPORT_RATE_PER_KM_PER_TONNE
            * Decimal(str(quantity_tonnes))
        )

    @staticmethod
    def calculate_total_cost(price_per_tonne, quantity_tonnes, transportation_cost):
        crop_cost = Decimal(str(price_per_tonne)) * Decimal(str(quantity_tonnes))
        return crop_cost + Decimal(str(transportation_cost))

    @staticmethod
    def calculate_delivery_time_days(distance_km):
        travel_hours = distance_km / AVG_TRUCK_SPEED_KMH
        total_hours = travel_hours + LOADING_TIME_HOURS
        return round(total_hours / 24, 1)

    @staticmethod
    def calculate_carbon_footprint(distance_km, quantity_tonnes, mode='road'):
        factor = CO2_EMISSION_FACTOR if mode == 'road' else RAIL_CO2_EMISSION_FACTOR
        return round(distance_km * quantity_tonnes * factor, 2)

    # ─── Railway Methods ──────────────────────────────────────────

    @staticmethod
    def get_railway_rate_class(crop, quantity_tonnes):
        is_turmeric = crop.name.lower() == 'turmeric'
        is_train_load = quantity_tonnes >= TRAIN_LOAD_THRESHOLD_TONNES

        if is_turmeric:
            return 'LR3' if is_train_load else 'LR3W'
        else:
            return '130A' if is_train_load else '130B'

    @staticmethod
    def calculate_railway_cost(distance_km, quantity_tonnes, rate_per_tonne):
        return Decimal(str(rate_per_tonne)) * Decimal(str(quantity_tonnes))

    @staticmethod
    def calculate_railway_delivery_days(distance_km):
        travel_hours = distance_km / AVG_RAIL_SPEED_KMH
        total_hours = travel_hours + RAIL_LOADING_TIME_HOURS
        return round(total_hours / 24, 1)

    # ─── Shared ───────────────────────────────────────────────────

    @staticmethod
    def calculate_savings(baseline_total_cost, optimized_total_cost):
        return Decimal(str(baseline_total_cost)) - Decimal(str(optimized_total_cost))
