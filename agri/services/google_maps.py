import math
import googlemaps
from django.conf import settings
from agri.models import DistanceCache


class GoogleMapsService:

    def __init__(self):
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    def get_distance(self, origin_state, origin_district, dest_state, dest_district):
        cached = DistanceCache.objects.filter(
            origin_state=origin_state,
            origin_district=origin_district,
            destination_state=dest_state,
            destination_district=dest_district,
        ).first()

        if cached:
            return {
                'distance_km': cached.distance_km,
                'duration_hours': cached.duration_hours,
            }

        origin_parts = []
        if origin_district:
            origin_parts.append(origin_district.name)
        origin_parts.append(origin_state.name)
        origin_parts.append('India')
        origin_str = ', '.join(origin_parts)

        dest_parts = []
        if dest_district:
            dest_parts.append(dest_district.name)
        dest_parts.append(dest_state.name)
        dest_parts.append('India')
        dest_str = ', '.join(dest_parts)

        try:
            result = self.client.distance_matrix(
                origins=[origin_str],
                destinations=[dest_str],
                mode='driving',
                units='metric',
            )

            element = result['rows'][0]['elements'][0]

            if element['status'] != 'OK':
                return self._fallback_estimate(origin_state, dest_state)

            distance_km = element['distance']['value'] / 1000
            duration_hours = element['duration']['value'] / 3600

        except Exception:
            return self._fallback_estimate(origin_state, dest_state)

        DistanceCache.objects.update_or_create(
            origin_state=origin_state,
            origin_district=origin_district,
            destination_state=dest_state,
            destination_district=dest_district,
            defaults={
                'distance_km': distance_km,
                'duration_hours': duration_hours,
            },
        )

        return {
            'distance_km': distance_km,
            'duration_hours': duration_hours,
        }

    def _fallback_estimate(self, origin_state, dest_state):
        if not all([
            origin_state.latitude, origin_state.longitude,
            dest_state.latitude, dest_state.longitude,
        ]):
            return {'distance_km': 1000, 'duration_hours': 20}

        R = 6371
        lat1 = math.radians(origin_state.latitude)
        lon1 = math.radians(origin_state.longitude)
        lat2 = math.radians(dest_state.latitude)
        lon2 = math.radians(dest_state.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        straight_distance = R * c
        road_distance = straight_distance * 1.4

        return {
            'distance_km': round(road_distance, 1),
            'duration_hours': round(road_distance / 50, 1),
        }
