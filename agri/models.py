from django.db import models
from django.contrib.auth.models import User
import uuid


class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True, blank=True, null=True)
    capital_city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='districts')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'state')

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class Crop(models.Model):
    SEASON_CHOICES = [
        ('Kharif', 'Kharif'),
        ('Rabi', 'Rabi'),
        ('Whole Year', 'Whole Year'),
        ('Summer', 'Summer'),
        ('Winter', 'Winter'),
        ('Autumn', 'Autumn'),
    ]

    name = models.CharField(max_length=100, unique=True)
    group = models.CharField(max_length=100, blank=True)
    typical_season = models.CharField(max_length=20, choices=SEASON_CHOICES, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CropProduction(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='productions')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='productions')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='productions')
    crop_year = models.IntegerField(db_index=True)
    season = models.CharField(max_length=30)
    area = models.FloatField(null=True, blank=True, help_text="Area in hectares")
    production = models.FloatField(null=True, blank=True, help_text="Production in tonnes")

    class Meta:
        indexes = [
            models.Index(fields=['crop', 'crop_year']),
            models.Index(fields=['state', 'crop']),
            models.Index(fields=['state', 'crop', 'crop_year']),
        ]
        unique_together = ('state', 'district', 'crop', 'crop_year', 'season')

    def __str__(self):
        return f"{self.crop.name} - {self.district.name} ({self.crop_year})"


class DemandSupply(models.Model):
    crop_group = models.CharField(max_length=100, unique=True)
    projected_demand_2016_17 = models.FloatField(null=True, blank=True, help_text="Million tonnes")
    projected_demand_2020_21 = models.FloatField(null=True, blank=True, help_text="Million tonnes")
    projected_supply_2016_17_low = models.FloatField(null=True, blank=True, help_text="Million tonnes (low)")
    projected_supply_2016_17_high = models.FloatField(null=True, blank=True, help_text="Million tonnes (high)")
    actual_production_2006_07 = models.FloatField(null=True, blank=True, help_text="Million tonnes")
    actual_production_2011_12 = models.FloatField(null=True, blank=True, help_text="Million tonnes")

    class Meta:
        verbose_name_plural = "Demand & Supply"

    def __str__(self):
        return self.crop_group


class CropPrice(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='prices')
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='crop_prices')
    price_per_tonne = models.DecimalField(max_digits=12, decimal_places=2, help_text="INR per tonne")
    year = models.IntegerField()
    source = models.CharField(max_length=50, default='MSP', help_text="MSP, Market, Estimated")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('crop', 'state', 'year')
        indexes = [
            models.Index(fields=['crop', 'state']),
        ]

    def __str__(self):
        return f"{self.crop.name} in {self.state.name}: INR {self.price_per_tonne}/tonne"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.state}"


class ProcurementQuery(models.Model):
    TRANSPORT_PREF_CHOICES = [
        ('road', 'Road Only'),
        ('rail', 'Rail Only'),
        ('both', 'Both Road & Rail'),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='queries')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    source_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='procurement_queries')
    source_district = models.ForeignKey(District, on_delete=models.CASCADE)
    required_quantity_tonnes = models.FloatField()
    transport_mode = models.CharField(max_length=10, choices=TRANSPORT_PREF_CHOICES, default='both')
    ai_summary_json = models.JSONField(null=True, blank=True)
    ai_summary_generated_at = models.DateTimeField(null=True, blank=True)
    ai_summary_model = models.CharField(max_length=100, blank=True, default='')
    ai_summary_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Procurement Queries"

    def __str__(self):
        return f"{self.crop.name} - {self.required_quantity_tonnes}T ({self.created_at.date()})"


class ProcurementResult(models.Model):
    RANKING_CHOICES = [
        ('best_cost', 'Best Cost'),
        ('fastest', 'Fastest Delivery'),
        ('lowest_carbon', 'Lowest Carbon'),
    ]
    TRANSPORT_MODE_CHOICES = [
        ('road', 'Road'),
        ('rail', 'Rail'),
    ]

    query = models.ForeignKey(ProcurementQuery, on_delete=models.CASCADE, related_name='results')
    supplier_state = models.ForeignKey(State, on_delete=models.CASCADE)
    supplier_district = models.ForeignKey(District, on_delete=models.CASCADE, null=True, blank=True)
    available_supply_tonnes = models.FloatField()
    price_per_tonne = models.DecimalField(max_digits=12, decimal_places=2)
    transportation_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)
    distance_km = models.FloatField()
    estimated_delivery_days = models.FloatField()
    carbon_footprint_kg = models.FloatField(help_text="CO2 equivalent in kg")
    transport_mode = models.CharField(max_length=10, choices=TRANSPORT_MODE_CHOICES, default='road')
    ranking_category = models.CharField(max_length=20, choices=RANKING_CHOICES, blank=True)
    ranking_score = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['total_cost']

    def __str__(self):
        return f"{self.supplier_state.name} ({self.transport_mode}) -> {self.query.source_state.name}: INR {self.total_cost}"


class RailwayFreightRate(models.Model):
    RATE_CLASS_CHOICES = [
        ('130A', 'Train Load - Food Grains (130A)'),
        ('130B', 'Wagon Load - Food Grains (130B)'),
        ('LR3', 'Train Load - Spices/Sugar (LR3)'),
        ('LR3W', 'Wagon Load - Spices/Sugar (LR3W)'),
    ]

    rate_class = models.CharField(max_length=10, choices=RATE_CLASS_CHOICES)
    min_distance_km = models.IntegerField()
    max_distance_km = models.IntegerField()
    rate_per_tonne = models.DecimalField(max_digits=10, decimal_places=2, help_text="INR per tonne")

    class Meta:
        unique_together = ('rate_class', 'min_distance_km', 'max_distance_km')
        ordering = ['rate_class', 'min_distance_km']
        verbose_name_plural = "Railway Freight Rates"

    def __str__(self):
        return f"{self.rate_class}: {self.min_distance_km}-{self.max_distance_km}km = INR {self.rate_per_tonne}/T"


class DistanceCache(models.Model):
    TRANSPORT_MODE_CHOICES = [
        ('road', 'Road'),
        ('rail', 'Rail'),
    ]

    origin_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='distances_from')
    origin_district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='distances_from', null=True, blank=True)
    destination_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='distances_to')
    destination_district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='distances_to', null=True, blank=True)
    transport_mode = models.CharField(max_length=10, choices=TRANSPORT_MODE_CHOICES, default='road')
    distance_km = models.FloatField()
    duration_hours = models.FloatField()
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            'origin_state', 'origin_district',
            'destination_state', 'destination_district',
            'transport_mode',
        )

    def __str__(self):
        return f"{self.origin_state} -> {self.destination_state} ({self.transport_mode}): {self.distance_km}km"
