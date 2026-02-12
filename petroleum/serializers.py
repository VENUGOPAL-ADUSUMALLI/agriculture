from rest_framework import serializers
from petroleum.models import (
    CrudeOilProduction, RefineryProcessing,
    PetroleumProductProduction, PetroleumImportExportSnapshot,
    PetroleumTrade,
)


class CrudeOilProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrudeOilProduction
        fields = ['id', 'month', 'year', 'company_name', 'quantity']


class RefineryProcessingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefineryProcessing
        fields = ['id', 'month', 'year', 'refinery_name', 'quantity']


class PetroleumProductProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetroleumProductProduction
        fields = ['id', 'month', 'year', 'product', 'quantity']


class PetroleumImportExportSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetroleumImportExportSnapshot
        fields = ['id', 'import_export', 'product', 'monthly_data', 'total']


class PetroleumTradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetroleumTrade
        fields = [
            'id', 'month', 'year', 'product', 'trade_type',
            'quantity', 'value_inr_crore', 'value_usd_million',
            'date_updated',
        ]
