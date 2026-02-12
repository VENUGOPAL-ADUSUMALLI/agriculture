from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

from petroleum.models import (
    CrudeOilProduction, RefineryProcessing,
    PetroleumProductProduction, PetroleumImportExportSnapshot,
    PetroleumTrade,
)
from petroleum.serializers import (
    CrudeOilProductionSerializer, RefineryProcessingSerializer,
    PetroleumProductProductionSerializer,
    PetroleumImportExportSnapshotSerializer,
    PetroleumTradeSerializer,
)
from petroleum.services.petroleum_analytics import PetroleumAnalyticsService

logger = logging.getLogger(__name__)


# ─── ReadOnly ViewSets ────────────────────────────────────────────

class CrudeOilProductionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CrudeOilProductionSerializer
    filterset_fields = ['year', 'company_name']
    search_fields = ['company_name']
    ordering_fields = ['year', 'quantity']

    def get_queryset(self):
        return CrudeOilProduction.objects.all()


class RefineryProcessingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RefineryProcessingSerializer
    filterset_fields = ['year', 'refinery_name']
    search_fields = ['refinery_name']
    ordering_fields = ['year', 'quantity']

    def get_queryset(self):
        return RefineryProcessing.objects.all()


class PetroleumProductProductionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PetroleumProductProductionSerializer
    filterset_fields = ['year', 'product']
    search_fields = ['product']
    ordering_fields = ['year', 'quantity']

    def get_queryset(self):
        return PetroleumProductProduction.objects.all()


class PetroleumImportExportSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PetroleumImportExportSnapshot.objects.all()
    serializer_class = PetroleumImportExportSnapshotSerializer
    filterset_fields = ['import_export', 'product']
    search_fields = ['product']


class PetroleumTradeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PetroleumTradeSerializer
    filterset_fields = ['year', 'product', 'trade_type']
    search_fields = ['product']
    ordering_fields = ['year', 'month', 'quantity', 'value_inr_crore']

    def get_queryset(self):
        return PetroleumTrade.objects.all()


# ─── Analytics Endpoints ─────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crude_production_forecast(request):
    """Problem 1: Crude Oil Production Forecasting."""
    company = request.query_params.get('company')
    service = PetroleumAnalyticsService()
    historical = service.get_crude_production_history(company_name=company)
    forecast = service.forecast_crude_production(company_name=company)
    return Response({
        'company': company or 'All',
        'historical_data': historical,
        'forecast': forecast,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def refinery_utilization(request):
    """Problem 2: Refinery Utilization Analysis."""
    refinery = request.query_params.get('refinery')
    year = request.query_params.get('year')
    if year:
        try:
            year = int(year)
        except ValueError:
            year = None

    service = PetroleumAnalyticsService()
    trends = service.get_refinery_trends(refinery_name=refinery, year=year)
    seasonal = service.get_refinery_seasonal_pattern(refinery_name=refinery)
    return Response({
        'refinery': refinery or 'All',
        'year_filter': year,
        'yearly_trends': trends,
        'seasonal_pattern': seasonal,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_demand_supply_gap(request):
    """Problem 3: Product-wise Demand-Supply Gap."""
    product = request.query_params.get('product')
    year = request.query_params.get('year')
    if year:
        try:
            year = int(year)
        except ValueError:
            year = None

    service = PetroleumAnalyticsService()
    gap_data = service.get_product_demand_supply_gap(product=product, year=year)
    return Response({
        'product_filter': product or 'All',
        'year_filter': year,
        **gap_data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import_cost_analysis(request):
    """Problem 4: Import Dependency & Cost Analysis."""
    year = request.query_params.get('year')
    if year:
        try:
            year = int(year)
        except ValueError:
            year = None

    service = PetroleumAnalyticsService()
    costs = service.get_import_cost_analysis(year=year)
    forecast = service.forecast_import_costs()
    return Response({
        'year_filter': year,
        'import_data': costs,
        'ai_forecast': forecast,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trade_balance_dashboard(request):
    """Problem 5: Trade Balance Dashboard."""
    year = request.query_params.get('year')
    if year:
        try:
            year = int(year)
        except ValueError:
            year = None

    service = PetroleumAnalyticsService()
    balance = service.get_trade_balance(year=year)
    return Response({
        'year_filter': year,
        'products': balance,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def market_intelligence(request):
    """Problem 6: AI-Powered Market Intelligence."""
    service = PetroleumAnalyticsService()
    intel = service.generate_market_intelligence()
    return Response(intel)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def filter_options(request):
    """Returns all available filter values for dropdowns."""
    return Response({
        'companies': list(
            CrudeOilProduction.objects.values_list('company_name', flat=True)
            .distinct().order_by('company_name')
        ),
        'refineries': list(
            RefineryProcessing.objects.values_list('refinery_name', flat=True)
            .distinct().order_by('refinery_name')
        ),
        'production_products': list(
            PetroleumProductProduction.objects.values_list('product', flat=True)
            .distinct().order_by('product')
        ),
        'trade_products': list(
            PetroleumTrade.objects.values_list('product', flat=True)
            .distinct().order_by('product')
        ),
        'years': {
            'crude_production': sorted(
                CrudeOilProduction.objects.values_list('year', flat=True).distinct()
            ),
            'refinery_processing': sorted(
                RefineryProcessing.objects.values_list('year', flat=True).distinct()
            ),
            'product_production': sorted(
                PetroleumProductProduction.objects.values_list('year', flat=True).distinct()
            ),
            'trade': sorted(
                PetroleumTrade.objects.values_list('year', flat=True).distinct()
            ),
        },
    })
