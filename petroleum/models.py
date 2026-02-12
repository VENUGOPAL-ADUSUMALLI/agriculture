from django.db import models


class CrudeOilProduction(models.Model):
    """API 1: Monthly Indigenous Crude Oil Production."""
    month = models.CharField(max_length=20, db_index=True)
    year = models.IntegerField(db_index=True)
    company_name = models.CharField(max_length=100, db_index=True)
    quantity = models.FloatField(
        null=True, blank=True,
        help_text="Production in 000 metric tonnes",
    )

    class Meta:
        ordering = ['-year', 'month']
        unique_together = ('month', 'year', 'company_name')
        indexes = [
            models.Index(fields=['company_name', 'year']),
        ]

    def __str__(self):
        return f"{self.company_name} - {self.month} {self.year}: {self.quantity}"


class RefineryProcessing(models.Model):
    """API 2: Monthly Crude Oil Processed by Refineries."""
    month = models.CharField(max_length=20, db_index=True)
    year = models.IntegerField(db_index=True)
    refinery_name = models.CharField(max_length=200, db_index=True)
    quantity = models.FloatField(
        null=True, blank=True,
        help_text="Crude oil processed in 000 metric tonnes",
    )

    class Meta:
        ordering = ['-year', 'month']
        unique_together = ('month', 'year', 'refinery_name')
        indexes = [
            models.Index(fields=['refinery_name', 'year']),
        ]

    def __str__(self):
        return f"{self.refinery_name} - {self.month} {self.year}: {self.quantity}"


class PetroleumProductProduction(models.Model):
    """API 3: Monthly Production of Petroleum Products by Refineries & Fractionators."""
    month = models.CharField(max_length=20, db_index=True)
    year = models.IntegerField(db_index=True)
    product = models.CharField(max_length=100, db_index=True)
    quantity = models.FloatField(
        null=True, blank=True,
        help_text="Production in 000 metric tonnes",
    )

    class Meta:
        ordering = ['-year', 'month']
        unique_together = ('month', 'year', 'product')
        indexes = [
            models.Index(fields=['product', 'year']),
        ]

    def __str__(self):
        return f"{self.product} - {self.month} {self.year}: {self.quantity}"


class PetroleumImportExportSnapshot(models.Model):
    """API 4: Import & Export of Petroleum Products - Volumes for Year 2022-23."""
    import_export = models.CharField(max_length=20)
    product = models.CharField(max_length=100)
    monthly_data = models.JSONField(
        default=dict,
        help_text="Monthly volumes: {april: x, may: y, ...}",
    )
    total = models.FloatField(
        null=True, blank=True,
        help_text="Annual total in 000 metric tonnes",
    )

    class Meta:
        ordering = ['import_export', 'product']
        unique_together = ('import_export', 'product')

    def __str__(self):
        return f"{self.import_export} - {self.product}: {self.total}"


class PetroleumTrade(models.Model):
    """API 5: Crude oil import and petroleum product import/export by Oil companies."""
    TRADE_CHOICES = [
        ('Import', 'Import'),
        ('Export', 'Export'),
    ]

    month = models.IntegerField(db_index=True, help_text="Month as number (1-12)")
    year = models.IntegerField(db_index=True)
    product = models.CharField(max_length=200, db_index=True)
    trade_type = models.CharField(max_length=10, choices=TRADE_CHOICES, db_index=True)
    quantity = models.FloatField(
        null=True, blank=True,
        help_text="Quantity in 000 metric tonnes",
    )
    value_inr_crore = models.FloatField(
        null=True, blank=True,
        help_text="Value in Rupees (Crore)",
    )
    value_usd_million = models.FloatField(
        null=True, blank=True,
        help_text="Value in US Dollars (Million)",
    )
    date_updated = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = ('month', 'year', 'product', 'trade_type')
        indexes = [
            models.Index(fields=['product', 'trade_type', 'year']),
            models.Index(fields=['trade_type', 'year']),
        ]

    def __str__(self):
        return f"{self.trade_type} {self.product} - {self.month}/{self.year}"
