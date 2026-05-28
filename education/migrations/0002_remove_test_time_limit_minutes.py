from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("education", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="test",
            name="time_limit_minutes",
        ),
    ]
