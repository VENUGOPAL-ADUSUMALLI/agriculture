from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Sum, Max, Count

from agri.models import (
    State, District, Crop, CropProduction, DemandSupply,
    CropPrice, UserProfile, ProcurementQuery, ProcurementResult,
)
from agri.serializers import (
    StateSerializer, DistrictSerializer, CropSerializer,
    CropProductionSerializer, DemandSupplySerializer, CropPriceSerializer,
    ProcurementQuerySerializer, ProcurementRequestSerializer,
    RegisterSerializer, UserProfileSerializer,
)
from agri.services.optimization_engine import OptimizationEngine
from agri.services.openai_service import OpenAIService


# ─── Auth Endpoints ───────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    user = User.objects.create_user(
        username=data['username'],
        password=data['password'],
        email=data.get('email', ''),
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
    )

    state = None
    district = None
    if data.get('state_id'):
        state = State.objects.filter(id=data['state_id']).first()
    if data.get('district_id'):
        district = District.objects.filter(id=data['district_id']).first()

    UserProfile.objects.create(
        user=user,
        state=state,
        district=district,
        designation=data.get('designation', ''),
    )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=user)

    profile_data = {}
    if hasattr(user, 'profile'):
        profile_data = UserProfileSerializer(user.profile).data

    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username,
        'profile': profile_data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'})


# ─── ReadOnly ViewSets ────────────────────────────────────────────

class StateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [AllowAny]
    search_fields = ['name']


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DistrictSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['state']
    search_fields = ['name']

    def get_queryset(self):
        queryset = District.objects.select_related('state')
        state_id = self.request.query_params.get('state')
        if state_id:
            queryset = queryset.filter(state_id=state_id)
        return queryset


class CropViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    search_fields = ['name', 'group']


class CropProductionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CropProductionSerializer
    filterset_fields = ['crop', 'state', 'crop_year', 'season']

    def get_queryset(self):
        return CropProduction.objects.select_related(
            'state', 'district', 'crop'
        ).all()


class DemandSupplyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DemandSupply.objects.all()
    serializer_class = DemandSupplySerializer


class CropPriceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CropPriceSerializer
    filterset_fields = ['crop', 'state', 'year']

    def get_queryset(self):
        return CropPrice.objects.select_related('crop', 'state').all()


# ─── Core Business Endpoints ─────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_procurement(request):
    serializer = ProcurementRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        crop = Crop.objects.get(id=data['crop_id'])
        state = State.objects.get(id=data['state_id'])
        district = District.objects.get(id=data['district_id'])
    except (Crop.DoesNotExist, State.DoesNotExist, District.DoesNotExist) as e:
        return Response(
            {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    engine = OptimizationEngine()
    query = engine.optimize_procurement(
        user=request.user,
        crop=crop,
        source_state=state,
        source_district=district,
        quantity_tonnes=data['quantity_tonnes'],
        transport_mode=data.get('transport_mode', 'both'),
    )

    result_serializer = ProcurementQuerySerializer(query)
    return Response(result_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def query_history(request):
    queries = ProcurementQuery.objects.filter(
        user=request.user
    ).select_related(
        'crop', 'source_state', 'source_district'
    ).prefetch_related('results__supplier_state')[:20]

    serializer = ProcurementQuerySerializer(queries, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def query_results(request, query_id):
    try:
        query = ProcurementQuery.objects.get(id=query_id, user=request.user)
    except ProcurementQuery.DoesNotExist:
        return Response(
            {'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProcurementQuerySerializer(query)

    # Generate AI summary
    ai_summary = None
    try:
        ai_service = OpenAIService()
        results = query.results.select_related('supplier_state').all()[:5]
        if results.exists():
            ai_summary = ai_service.generate_procurement_summary(query, results)
    except Exception:
        pass

    response_data = serializer.data
    response_data['ai_summary'] = ai_summary
    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crop_availability(request):
    crop_id = request.query_params.get('crop')
    if not crop_id:
        return Response(
            {'error': 'crop query parameter required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        crop = Crop.objects.get(id=crop_id)
    except Crop.DoesNotExist:
        return Response(
            {'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)

    latest_year = CropProduction.objects.filter(
        crop=crop
    ).aggregate(max_year=Max('crop_year'))['max_year']

    if not latest_year:
        return Response({
            'crop': CropSerializer(crop).data,
            'data_year': None,
            'states': [],
        })

    production_by_state = CropProduction.objects.filter(
        crop=crop,
        crop_year=latest_year,
    ).values(
        'state__id', 'state__name'
    ).annotate(
        total_production=Sum('production'),
        total_area=Sum('area'),
        district_count=Count('district', distinct=True),
    ).order_by('-total_production')

    return Response({
        'crop': CropSerializer(crop).data,
        'data_year': latest_year,
        'states': list(production_by_state),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def predict_demand(request, crop_id):
    try:
        crop = Crop.objects.get(id=crop_id)
    except Crop.DoesNotExist:
        return Response(
            {'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)

    state_id = request.query_params.get('state')

    # Build historical data
    production_qs = CropProduction.objects.filter(crop=crop)
    if state_id:
        production_qs = production_qs.filter(state_id=state_id)

    historical = production_qs.values('crop_year').annotate(
        total_production=Sum('production'),
        total_area=Sum('area'),
    ).order_by('crop_year')

    historical_data = [
        {
            'year': h['crop_year'],
            'production': h['total_production'],
            'area': h['total_area'],
        }
        for h in historical
    ]

    state_name = 'India'
    if state_id:
        state = State.objects.filter(id=state_id).first()
        if state:
            state_name = state.name

    try:
        ai_service = OpenAIService()
        prediction = ai_service.predict_demand(
            crop.name, state_name, historical_data)
    except Exception as e:
        prediction = {
            'error': f'Prediction unavailable: {str(e)}',
            'historical_data': historical_data,
        }

    return Response({
        'crop': CropSerializer(crop).data,
        'state': state_name,
        'historical_data': historical_data,
        'prediction': prediction,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def impact_dashboard(request):
    user_queries = ProcurementQuery.objects.filter(user=request.user)
    total_queries = user_queries.count()

    best_cost_results = ProcurementResult.objects.filter(
        query__user=request.user,
        ranking_category='best_cost',
    )

    total_optimized_cost = sum(float(r.total_cost) for r in best_cost_results)

    all_results = ProcurementResult.objects.filter(query__user=request.user)
    total_carbon = sum(r.carbon_footprint_kg for r in all_results)

    lowest_carbon_results = ProcurementResult.objects.filter(
        query__user=request.user,
        ranking_category='lowest_carbon',
    )
    carbon_saved = sum(r.carbon_footprint_kg for r in lowest_carbon_results)

    recent = ProcurementQuerySerializer(
        user_queries[:10], many=True
    ).data

    return Response({
        'total_queries': total_queries,
        'total_optimized_cost': total_optimized_cost,
        'total_carbon_footprint_kg': total_carbon,
        'carbon_saved_kg': carbon_saved,
        'recent_queries': recent,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    demand_supply = DemandSupply.objects.all()
    gap_data = []
    for ds in demand_supply:
        demand = ds.projected_demand_2020_21 or ds.projected_demand_2016_17
        supply_high = ds.projected_supply_2016_17_high
        supply_low = ds.projected_supply_2016_17_low

        if demand and supply_high:
            gap = round(demand - supply_high, 2)
            gap_status = 'surplus' if gap <= 0 else 'deficit'
        else:
            gap = None
            gap_status = 'unknown'

        gap_data.append({
            'crop_group': ds.crop_group,
            'projected_demand': demand,
            'projected_supply_low': supply_low,
            'projected_supply_high': supply_high,
            'actual_production_2011_12': ds.actual_production_2011_12,
            'gap_million_tonnes': gap,
            'status': gap_status,
        })

    return Response({
        'demand_supply_gaps': gap_data,
    })
