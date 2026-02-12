import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agri', '0004_procurementquery_ai_summary_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='procurementquery',
            name='public_id',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
