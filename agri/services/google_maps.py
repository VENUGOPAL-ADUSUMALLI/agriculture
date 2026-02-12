import math
import googlemaps
from django.conf import settings
from agri.models import DistanceCache


class GoogleMapsService:
    TRANSPORT_MODE_CONFIG = {
        'road': {
            'mode': 'driving',
            'transit_mode': None,
        },
        'rail': {
            'mode': 'transit',
            'transit_mode': 'rail',
        },
    }

    def __init__(self):
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    def get_distance(self, origin_state, origin_district, dest_state, dest_district, transport_mode='road'):
        if transport_mode not in self.TRANSPORT_MODE_CONFIG:
            transport_mode = 'road'

        cached = DistanceCache.objects.filter(
            origin_state=origin_state,
            origin_district=origin_district,
            destination_state=dest_state,
            destination_district=dest_district,
            transport_mode=transport_mode,
        ).first()

        if cached:
            return {
                'distance_km': cached.distance_km,
                'duration_hours': cached.duration_hours,
                'transport_mode': cached.transport_mode,
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
            config = self.TRANSPORT_MODE_CONFIG[transport_mode]
            params = {
                'origins': [origin_str],
                'destinations': [dest_str],
                'mode': config['mode'],
                'units': 'metric',
            }
            if config['transit_mode']:
                params['transit_mode'] = config['transit_mode']
                params['departure_time'] = 'now'

            result = self.client.distance_matrix(
                **params,
            )

            element = result['rows'][0]['elements'][0]

            if element['status'] != 'OK':
                if transport_mode == 'rail':
                    road_fallback = self._fallback_from_road_matrix(origin_str, dest_str)
                    if road_fallback:
                        return road_fallback
                return self._fallback_estimate(origin_state, dest_state, transport_mode)

            distance_km = element['distance']['value'] / 1000
            duration_hours = element['duration']['value'] / 3600

        except Exception:
            if transport_mode == 'rail':
                road_fallback = self._fallback_from_road_matrix(origin_str, dest_str)
                if road_fallback:
                    return road_fallback
            return self._fallback_estimate(origin_state, dest_state, transport_mode)

        DistanceCache.objects.update_or_create(
            origin_state=origin_state,
            origin_district=origin_district,
            destination_state=dest_state,
            destination_district=dest_district,
            transport_mode=transport_mode,
            defaults={
                'distance_km': distance_km,
                'duration_hours': duration_hours,
            },
        )

        return {
            'distance_km': distance_km,
            'duration_hours': duration_hours,
            'transport_mode': transport_mode,
        }

    def _fallback_from_road_matrix(self, origin_str, dest_str):
        """
        If rail transit route is unavailable, derive a route-specific rail estimate
        from driving distance so different routes do not collapse to one constant.
        """
        try:
            road_result = self.client.distance_matrix(
                origins=[origin_str],
                destinations=[dest_str],
                mode='driving',
                units='metric',
            )
            road_element = road_result['rows'][0]['elements'][0]
            if road_element['status'] != 'OK':
                return None
            road_km = road_element['distance']['value'] / 1000
            rail_km = round(road_km * 0.92, 3)
            rail_hours = round(rail_km / 35, 2)
            return {
                'distance_km': rail_km,
                'duration_hours': rail_hours,
                'transport_mode': 'rail',
            }
        except Exception:
            return None

    def _fallback_estimate(self, origin_state, dest_state, transport_mode):
        if not all([
            origin_state.latitude, origin_state.longitude,
            dest_state.latitude, dest_state.longitude,
        ]):
            if transport_mode == 'rail':
                return {'distance_km': 900, 'duration_hours': 30, 'transport_mode': 'rail'}
            return {'distance_km': 1000, 'duration_hours': 20, 'transport_mode': 'road'}

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
        if transport_mode == 'rail':
            rail_distance = straight_distance * 1.2
            return {
                'distance_km': round(rail_distance, 1),
                'duration_hours': round(rail_distance / 35, 1),
                'transport_mode': 'rail',
            }

        return {
            'distance_km': round(straight_distance * 1.4, 1),
            'duration_hours': round((straight_distance * 1.4) / 50, 1),
            'transport_mode': 'road',
        }
