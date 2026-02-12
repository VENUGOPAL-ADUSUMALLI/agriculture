from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.models import User
from agri.models import (
    State, District, Crop, CropProduction, DemandSupply,
    CropPrice, UserProfile, ProcurementQuery, ProcurementResult,
)


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name', 'code', 'capital_city']


class DistrictSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)

    class Meta:
        model = District
        fields = ['id', 'name', 'state', 'state_name']


class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = ['id', 'name', 'group', 'typical_season']


class CropProductionSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    crop_name = serializers.CharField(source='crop.name', read_only=True)

    class Meta:
        model = CropProduction
        fields = [
            'id', 'state_name', 'district_name', 'crop_name',
            'crop_year', 'season', 'area', 'production',
        ]


class DemandSupplySerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandSupply
        fields = '__all__'


class CropPriceSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(source='crop.name', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)

    class Meta:
        model = CropPrice
        fields = [
            'id', 'crop', 'crop_name', 'state', 'state_name',
            'price_per_tonne', 'year', 'source',
        ]


class ProcurementResultSerializer(serializers.ModelSerializer):
    supplier_state_name = serializers.CharField(
        source='supplier_state.name', read_only=True)
    price_per_tonne = serializers.SerializerMethodField()
    base_price_per_tonne = serializers.SerializerMethodField()
    transport_cost_per_tonne = serializers.SerializerMethodField()

    @staticmethod
    def _format_money(val):
        return str(Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    @staticmethod
    def _fulfilled_quantity(obj):
        return max(0.0, min(
            float(obj.available_supply_tonnes),
            float(obj.query.required_quantity_tonnes),
        ))

    def get_base_price_per_tonne(self, obj):
        return self._format_money(obj.price_per_tonne)

    def get_transport_cost_per_tonne(self, obj):
        qty = self._fulfilled_quantity(obj)
        if qty <= 0:
            return None
        return self._format_money(Decimal(str(obj.transportation_cost)) / Decimal(str(qty)))

    def get_price_per_tonne(self, obj):
        """
        Return landed price per tonne (base + transport/tonne) so
        road and rail values are naturally mode-specific in API output.
        """
        qty = self._fulfilled_quantity(obj)
        if qty <= 0:
            return self._format_money(obj.price_per_tonne)
        landed = Decimal(str(obj.total_cost)) / Decimal(str(qty))
        return self._format_money(landed)

    class Meta:
        model = ProcurementResult
        fields = [
            'id', 'supplier_state_name', 'available_supply_tonnes',
            'base_price_per_tonne', 'transport_cost_per_tonne', 'price_per_tonne',
            'transportation_cost', 'total_cost',
            'distance_km', 'estimated_delivery_days', 'carbon_footprint_kg',
            'transport_mode', 'ranking_category', 'ranking_score',
        ]


class ProcurementQuerySerializer(serializers.ModelSerializer):
    results = ProcurementResultSerializer(many=True, read_only=True)
    crop_name = serializers.CharField(source='crop.name', read_only=True)
    state_name = serializers.CharField(source='source_state.name', read_only=True)
    district_name = serializers.CharField(source='source_district.name', read_only=True)
    query_uuid = serializers.UUIDField(source='public_id', read_only=True)

    class Meta:
        model = ProcurementQuery
        fields = [
            'id', 'query_uuid', 'crop_name', 'state_name', 'district_name',
            'required_quantity_tonnes', 'transport_mode', 'created_at', 'results',
        ]


class ProcurementRequestSerializer(serializers.Serializer):
    crop_id = serializers.IntegerField()
    state_id = serializers.IntegerField()
    district_id = serializers.IntegerField()
    quantity_tonnes = serializers.FloatField(min_value=1)
    transport_mode = serializers.ChoiceField(
        choices=['road', 'rail', 'both'], default='both', required=False)


class UserProfileSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['state', 'state_name', 'district', 'district_name',
                  'designation', 'phone']


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=150, required=False, default='')
    last_name = serializers.CharField(max_length=150, required=False, default='')
    state_id = serializers.IntegerField(required=False)
    district_id = serializers.IntegerField(required=False)
    designation = serializers.CharField(max_length=100, required=False, default='')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
