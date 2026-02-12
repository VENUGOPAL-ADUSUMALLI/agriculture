from django.contrib import admin
from agri.models import (
    State, District, Crop, CropProduction, DemandSupply,
    CropPrice, UserProfile, ProcurementQuery, ProcurementResult,
    DistanceCache, RailwayFreightRate
)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'capital_city']
    search_fields = ['name']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'state']
    list_filter = ['state']
    search_fields = ['name']


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'typical_season']
    search_fields = ['name']
    list_filter = ['group']


@admin.register(CropProduction)
class CropProductionAdmin(admin.ModelAdmin):
    list_display = ['crop', 'state', 'district', 'crop_year', 'season', 'production']
    list_filter = ['crop_year', 'season', 'state']
    search_fields = ['crop__name', 'state__name']


@admin.register(DemandSupply)
class DemandSupplyAdmin(admin.ModelAdmin):
    list_display = ['crop_group', 'projected_demand_2016_17', 'projected_demand_2020_21',
                    'actual_production_2006_07', 'actual_production_2011_12']


@admin.register(CropPrice)
class CropPriceAdmin(admin.ModelAdmin):
    list_display = ['crop', 'state', 'price_per_tonne', 'year', 'source']
    list_filter = ['year', 'source', 'state']
    search_fields = ['crop__name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'state', 'district', 'designation']
    list_filter = ['state']


@admin.register(ProcurementQuery)
class ProcurementQueryAdmin(admin.ModelAdmin):
    list_display = ['user', 'crop', 'source_state', 'required_quantity_tonnes', 'transport_mode', 'created_at']
    list_filter = ['created_at', 'crop', 'transport_mode']


@admin.register(ProcurementResult)
class ProcurementResultAdmin(admin.ModelAdmin):
    list_display = ['query', 'supplier_state', 'transport_mode', 'total_cost', 'estimated_delivery_days',
                    'carbon_footprint_kg', 'ranking_category']
    list_filter = ['ranking_category', 'transport_mode']


@admin.register(DistanceCache)
class DistanceCacheAdmin(admin.ModelAdmin):
    list_display = ['origin_state', 'destination_state', 'distance_km', 'duration_hours']


@admin.register(RailwayFreightRate)
class RailwayFreightRateAdmin(admin.ModelAdmin):
    list_display = ['rate_class', 'min_distance_km', 'max_distance_km', 'rate_per_tonne']
    list_filter = ['rate_class']
