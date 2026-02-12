from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agri', '0003_distancecache_transport_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='procurementquery',
            name='ai_summary_error',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='procurementquery',
            name='ai_summary_generated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='procurementquery',
            name='ai_summary_json',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='procurementquery',
            name='ai_summary_model',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
