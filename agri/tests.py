import json
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


class OpenAIServicePredictionParserTests(APITestCase):
    def test_normalize_next5_prediction_accepts_valid_json(self):
        service = OpenAIService.__new__(OpenAIService)
        current_year = 2026
        target_years = [2027, 2028, 2029, 2030, 2031]
        content = json.dumps({
            'trend': 'increasing',
            'confidence': 0.76,
            'analysis': 'Rising steadily.',
            'forecast': [
                {'year': y, 'predicted_demand_tonnes': 1000 + i * 100, 'confidence': 0.7, 'suggestion': 'Plan procurement'}
                for i, y in enumerate(target_years)
            ],
        })

        result = service._normalize_next5_prediction(
            content=content,
            historical_data=[{'year': 2020, 'production': 900}],
            current_year=current_year,
            target_years=target_years,
        )

        self.assertEqual(result['current_year'], 2026)
        self.assertEqual(result['trend'], 'increasing')
        self.assertEqual(result['confidence'], 0.76)
        self.assertEqual(len(result['forecast']), 5)
        self.assertEqual(result['forecast'][0]['year'], 2027)

    def test_normalize_next5_prediction_fallback_on_invalid(self):
        service = OpenAIService.__new__(OpenAIService)
        current_year = 2026
        target_years = [2027, 2028, 2029, 2030, 2031]

        result = service._normalize_next5_prediction(
            content='not-json',
            historical_data=[{'year': 2020, 'production': 900}],
            current_year=current_year,
            target_years=target_years,
        )

        self.assertEqual(result['current_year'], 2026)
        self.assertIn(result['trend'], ['increasing', 'stable', 'decreasing'])
        self.assertLessEqual(result['confidence'], 1.0)
        self.assertEqual(len(result['forecast']), 5)


class PredictDemandApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='predict_user', password='secret123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.state = State.objects.create(name='Rajasthan')
        self.district = District.objects.create(name='Jaipur', state=self.state)
        self.crop = Crop.objects.create(name='Rice', group='Cereals', typical_season='Kharif')

    @patch.object(OpenAIService, 'predict_demand')
    def test_predict_endpoint_returns_legacy_shape(self, mocked_predict):
        mocked_predict.return_value = {
            'current_year': 2026,
            'trend': 'increasing',
            'confidence': 0.72,
            'analysis': 'Demand is increasing based on historical trend.',
            'forecast': [
                {'year': 2027, 'predicted_demand_tonnes': 100000.0, 'confidence': 0.71, 'suggestion': 'Increase buffer stock.'},
                {'year': 2028, 'predicted_demand_tonnes': 103000.0, 'confidence': 0.7, 'suggestion': 'Increase buffer stock.'},
                {'year': 2029, 'predicted_demand_tonnes': 106000.0, 'confidence': 0.69, 'suggestion': 'Increase buffer stock.'},
                {'year': 2030, 'predicted_demand_tonnes': 109000.0, 'confidence': 0.68, 'suggestion': 'Increase buffer stock.'},
                {'year': 2031, 'predicted_demand_tonnes': 112000.0, 'confidence': 0.67, 'suggestion': 'Increase buffer stock.'},
            ],
        }

        response = self.client.get(reverse('api_predict', args=[self.crop.id]), {'state': self.state.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data.keys()), {'crop', 'state', 'historical_data', 'prediction'})
        self.assertIn('trend', response.data['prediction'])
        self.assertIn('confidence', response.data['prediction'])
        self.assertIn('analysis', response.data['prediction'])
        self.assertIn('current_year', response.data['prediction'])
        self.assertIn('forecast', response.data['prediction'])
        self.assertEqual(len(response.data['prediction']['forecast']), 5)


class DemandSupplyInsightsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='insights_user', password='secret123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.state = State.objects.create(name='West Bengal')
        self.district = District.objects.create(name='Nadia', state=self.state)
        self.crop = Crop.objects.create(name='Rice', group='Cereals', typical_season='Kharif')

        CropProduction.objects.create(
            state=self.state,
            district=self.district,
            crop=self.crop,
            crop_year=2014,
            season='Kharif',
            area=1000,
            production=2500,
        )
        DemandSupply.objects.create(
            crop_group='Cereals',
            projected_demand_2020_21=108.0,
            projected_supply_2016_17_low=98.0,
            projected_supply_2016_17_high=106.0,
        )
        CropPrice.objects.create(
            crop=self.crop,
            state=self.state,
            year=2024,
            price_per_tonne=18500,
            source='MSP',
        )

    @patch.object(OpenAIService, 'generate_surplus_deficit_insight')
    def test_demand_supply_insights_endpoint(self, mocked_insight):
        mocked_insight.return_value = (
            'Is Rice in surplus or deficit nationally? — '
            'Projected demand is 108M tonnes vs supply 98-106M tonnes, '
            'so Rice might be slightly short nationally; better act fast.'
        )
        response = self.client.get('/api/v1/demand-supply/insights/?crop=Rice')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['crop']['name'], 'Rice')
        self.assertEqual(response.data['production_insight']['data_year'], 2014)
        self.assertTrue(response.data['production_insight']['top_states'])
        self.assertEqual(response.data['demand_supply_insight']['balance_status'], 'deficit')
        self.assertIn('Is Rice in surplus or deficit nationally?', response.data['ai_prediction'])
        self.assertEqual(response.data['price_insight']['price_year'], 2024)

    def test_demand_supply_insights_requires_crop_param(self):
        response = self.client.get('/api/v1/demand-supply/insights/')
        self.assertEqual(response.status_code, 400)

    @patch.object(OpenAIService, 'predict_demand', side_effect=RuntimeError('OpenAI unavailable'))
    def test_predict_endpoint_failure_still_returns_legacy_shape(self, mocked_predict):
        response = self.client.get(reverse('api_predict', args=[self.crop.id]), {'state': self.state.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data.keys()), {'crop', 'state', 'historical_data', 'prediction'})
        self.assertIn('trend', response.data['prediction'])
        self.assertIn('confidence', response.data['prediction'])
        self.assertIn('analysis', response.data['prediction'])
        self.assertIn('current_year', response.data['prediction'])
        self.assertIn('forecast', response.data['prediction'])
        self.assertEqual(len(response.data['prediction']['forecast']), 5)
