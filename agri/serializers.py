from rest_framework import serializers
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

    class Meta:
        model = ProcurementResult
        fields = [
            'id', 'supplier_state_name', 'available_supply_tonnes',
            'price_per_tonne', 'transportation_cost', 'total_cost',
            'distance_km', 'estimated_delivery_days', 'carbon_footprint_kg',
            'ranking_category', 'ranking_score',
        ]


class ProcurementQuerySerializer(serializers.ModelSerializer):
    results = ProcurementResultSerializer(many=True, read_only=True)
    crop_name = serializers.CharField(source='crop.name', read_only=True)
    state_name = serializers.CharField(source='source_state.name', read_only=True)
    district_name = serializers.CharField(source='source_district.name', read_only=True)

    class Meta:
        model = ProcurementQuery
        fields = [
            'id', 'crop_name', 'state_name', 'district_name',
            'required_quantity_tonnes', 'created_at', 'results',
        ]


class ProcurementRequestSerializer(serializers.Serializer):
    crop_id = serializers.IntegerField()
    state_id = serializers.IntegerField()
    district_id = serializers.IntegerField()
    quantity_tonnes = serializers.FloatField(min_value=1)


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
