from django.urls import path, include
from rest_framework.routers import SimpleRouter
from petroleum import views

router = SimpleRouter()
router.register(r'crude-production', views.CrudeOilProductionViewSet, basename='crude-production')
router.register(r'refinery-processing', views.RefineryProcessingViewSet, basename='refinery-processing')
router.register(r'product-production', views.PetroleumProductProductionViewSet,basename='product-production')
router.register(r'import-export-snapshot', views.PetroleumImportExportSnapshotViewSet,basename='import-export-snapshot')
router.register(r'trade', views.PetroleumTradeViewSet,basename='trade')

urlpatterns = [
    # Analytics endpoints
    path('forecast/crude/', views.crude_production_forecast,name='petroleum_crude_forecast'),
    path('analysis/refinery/', views.refinery_utilization,name='petroleum_refinery_utilization'),
    path('analysis/demand-supply-gap/', views.product_demand_supply_gap,name='petroleum_demand_supply_gap'),
    path('analysis/import-costs/', views.import_cost_analysis,name='petroleum_import_costs'),
    path('dashboard/trade-balance/', views.trade_balance_dashboard, name='petroleum_trade_balance'),
    path('intelligence/', views.market_intelligence,name='petroleum_market_intelligence'),
    path('filters/', views.filter_options, name='petroleum_filters'),
    path('', include(router.urls)),
]
