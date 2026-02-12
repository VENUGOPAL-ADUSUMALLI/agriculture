from django.urls import path, include
from rest_framework.routers import DefaultRouter
from agri import views

router = DefaultRouter()
router.register(r'states', views.StateViewSet)
router.register(r'districts', views.DistrictViewSet, basename='district')
router.register(r'crops', views.CropViewSet)
router.register(r'production', views.CropProductionViewSet, basename='production')
router.register(r'demand-supply', views.DemandSupplyViewSet)
router.register(r'prices', views.CropPriceViewSet, basename='price')

urlpatterns = [
    # Auth
    path('auth/register/', views.register_view, name='api_register'),
    path('auth/login/', views.login_view, name='api_login'),
    path('auth/logout/', views.logout_view, name='api_logout'),

    # Core business
    path('optimize/', views.optimize_procurement, name='api_optimize'),
    path('history/', views.query_history, name='api_history'),
    path('results/<uuid:query_uuid>/', views.query_results, name='api_results'),
    path('crop-availability/', views.crop_availability, name='api_crop_availability'),
    path('predict/<int:crop_id>/', views.predict_demand, name='api_predict'),
    path('impact/', views.impact_dashboard, name='api_impact'),
    path('dashboard/', views.dashboard_view, name='api_dashboard'),

    # ViewSet routes
    path('', include(router.urls)),
]
