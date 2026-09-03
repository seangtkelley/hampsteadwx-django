from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="snowseason",
            name="total",
            field=models.DecimalField(decimal_places=3, max_digits=8),
        ),
    ]
