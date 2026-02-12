from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from agri.models import Crop, District, ProcurementQuery, ProcurementResult, State
from agri.services.openai_service import OpenAIService


class ResultsAISummaryCachingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='secret123')
        self.other_user = User.objects.create_user(username='user2', password='secret123')

        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.source_state = State.objects.create(name='Sikkim')
        self.supplier_state = State.objects.create(name='Karnataka')
        self.source_district = District.objects.create(name='Gangtok', state=self.source_state)

        self.crop = Crop.objects.create(name='Arecanut')

        self.query = ProcurementQuery.objects.create(
            user=self.user,
            crop=self.crop,
            source_state=self.source_state,
            source_district=self.source_district,
            required_quantity_tonnes=120,
            transport_mode='road',
        )
        ProcurementResult.objects.create(
            query=self.query,
            supplier_state=self.supplier_state,
            available_supply_tonnes=5000,
            price_per_tonne=60000,
            transportation_cost=120000,
            total_cost=7320000,
            distance_km=1400,
            estimated_delivery_days=4.5,
            carbon_footprint_kg=10416,
            transport_mode='road',
        )

    def test_results_cache_miss_generates_and_persists_summary(self):
        summary_payload = {
            'headline': 'Best option for current requirement',
            'points': [
                {'title': 'Best cost option', 'detail': 'Karnataka road shipment has lowest total cost.'},
                {'title': 'Fastest delivery', 'detail': 'Estimated delivery time is about 4.5 days.'},
                {'title': 'Lowest carbon', 'detail': 'Road mode has computed carbon for current options.'},
                {'title': 'Trade-off', 'detail': 'Lower cost comes with moderate delivery time.'},
            ],
        }

        with patch.object(OpenAIService, 'generate_procurement_summary', return_value=summary_payload) as mocked:
            response = self.client.get(reverse('api_results', args=[self.query.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['ai_summary_source'], 'generated')
        self.assertEqual(response.data['ai_summary']['headline'], summary_payload['headline'])
        self.assertEqual(len(response.data['ai_summary']['points']), 4)
        self.assertEqual(response.data['ai_summary']['model'], OpenAIService.MODEL_NAME)
        mocked.assert_called_once()

        self.query.refresh_from_db()
        self.assertEqual(self.query.ai_summary_json['headline'], summary_payload['headline'])
        self.assertIsNotNone(self.query.ai_summary_generated_at)
        self.assertEqual(self.query.ai_summary_model, OpenAIService.MODEL_NAME)
        self.assertEqual(self.query.ai_summary_error, '')

    def test_results_cache_hit_does_not_call_openai(self):
        self.query.ai_summary_json = {
            'headline': 'Cached summary',
            'points': [{'title': 'Cached', 'detail': 'From DB cache'}],
        }
        self.query.ai_summary_model = OpenAIService.MODEL_NAME
        self.query.save(update_fields=['ai_summary_json', 'ai_summary_model'])

        with patch.object(OpenAIService, 'generate_procurement_summary') as mocked:
            response = self.client.get(reverse('api_results', args=[self.query.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['ai_summary_source'], 'cache')
        self.assertEqual(response.data['ai_summary']['headline'], 'Cached summary')
        mocked.assert_not_called()

    def test_results_openai_failure_returns_unavailable(self):
        with patch.object(OpenAIService, 'generate_procurement_summary', side_effect=RuntimeError('OpenAI down')):
            response = self.client.get(reverse('api_results', args=[self.query.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['ai_summary_source'], 'unavailable')
        self.assertIsNone(response.data['ai_summary'])

        self.query.refresh_from_db()
        self.assertIn('OpenAI down', self.query.ai_summary_error)

    def test_user_cannot_access_other_users_query(self):
        other_query = ProcurementQuery.objects.create(
            user=self.other_user,
            crop=self.crop,
            source_state=self.source_state,
            source_district=self.source_district,
            required_quantity_tonnes=10,
            transport_mode='road',
        )

        get_response = self.client.get(reverse('api_results', args=[other_query.public_id]))

        self.assertEqual(get_response.status_code, 404)


class OpenAIServiceSummaryParserTests(APITestCase):
    def test_normalize_summary_accepts_valid_json(self):
        service = OpenAIService.__new__(OpenAIService)
        content = '{"headline": "Test", "points": [{"title": "A", "detail": "B"}, {"title": "C", "detail": "D"}]}'

        summary = service._normalize_summary(content, query=self._fake_query(), results_data=[])

        self.assertEqual(summary['headline'], 'Test')
        self.assertEqual(len(summary['points']), 2)

    def test_normalize_summary_fallback_on_invalid_json(self):
        service = OpenAIService.__new__(OpenAIService)

        summary = service._normalize_summary('not-json', query=self._fake_query(), results_data=[])

        self.assertIn('headline', summary)
        self.assertTrue(summary['points'])

    @staticmethod
    def _fake_query():
        class Query:
            class CropObj:
                name = 'Rice'

            class StateObj:
                name = 'Assam'

            crop = CropObj()
            source_state = StateObj()

        return Query()
