from django.contrib import admin
from petroleum.models import (
    CrudeOilProduction, RefineryProcessing,
    PetroleumProductProduction, PetroleumImportExportSnapshot,
    PetroleumTrade,
)


@admin.register(CrudeOilProduction)
class CrudeOilProductionAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'month', 'year', 'quantity']
    list_filter = ['company_name', 'year']
    search_fields = ['company_name']


@admin.register(RefineryProcessing)
class RefineryProcessingAdmin(admin.ModelAdmin):
    list_display = ['refinery_name', 'month', 'year', 'quantity']
    list_filter = ['year']
    search_fields = ['refinery_name']


@admin.register(PetroleumProductProduction)
class PetroleumProductProductionAdmin(admin.ModelAdmin):
    list_display = ['product', 'month', 'year', 'quantity']
    list_filter = ['product', 'year']
    search_fields = ['product']


@admin.register(PetroleumImportExportSnapshot)
class PetroleumImportExportSnapshotAdmin(admin.ModelAdmin):
    list_display = ['import_export', 'product', 'total']
    list_filter = ['import_export']
    search_fields = ['product']


@admin.register(PetroleumTrade)
class PetroleumTradeAdmin(admin.ModelAdmin):
    list_display = ['product', 'trade_type', 'month', 'year', 'quantity',
                    'value_inr_crore', 'value_usd_million']
    list_filter = ['trade_type', 'year']
    search_fields = ['product']
