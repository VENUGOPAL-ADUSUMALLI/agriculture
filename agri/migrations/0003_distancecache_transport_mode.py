from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agri', '0002_procurementquery_transport_mode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='distancecache',
            name='transport_mode',
            field=models.CharField(
                choices=[('road', 'Road'), ('rail', 'Rail')],
                default='road',
                max_length=10,
            ),
        ),
        migrations.AlterUniqueTogether(
            name='distancecache',
            unique_together={
                (
                    'origin_state',
                    'origin_district',
                    'destination_state',
                    'destination_district',
                    'transport_mode',
                )
            },
        ),
    ]
