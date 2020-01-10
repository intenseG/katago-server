# Generated by Django 3.0.1 on 2020-01-03 17:40

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import katago_server.contrib.validators
import katago_server.distributed_efforts.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('trainings', '__first__'),
        ('games', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicDistributedTaskConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('katago_config', models.TextField()),
            ],
            options={
                'verbose_name': 'Katago Configuration',
            },
        ),
        migrations.CreateModel(
            name='TrainingGameDistributedTask',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4)),
                ('status', models.CharField(choices=[('UNASSIGNED', 'Unassigned'), ('ONGOING', 'Ongoing'), ('DONE', 'Done'), ('CANCELED', 'Canceled')], default='UNASSIGNED', max_length=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_at', models.DateTimeField(auto_now=True)),
                ('expire_at', models.DateTimeField()),
                ('board_size_x', models.IntegerField(blank=True, default=19, null=True)),
                ('board_size_y', models.IntegerField(default=19)),
                ('handicap', models.IntegerField(blank=True, default=0, null=True)),
                ('komi', models.DecimalField(blank=True, decimal_places=1, default=7.0, max_digits=3, null=True)),
                ('rules_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('initial_position_sgf_file', models.FileField(blank=True, null=True, upload_to=katago_server.distributed_efforts.models.upload_initial_to, validators=[katago_server.contrib.validators.FileValidator(magic_types=('Smart Game Format (Go)',), max_size=10485760)])),
                ('initial_position_extra_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('game_extra_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='traininggamedistributedtask_games', to=settings.AUTH_USER_MODEL)),
                ('black_network', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='traininggamedistributedtask_predefined_jobs_as_black', to='trainings.Network')),
                ('result', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='games.TrainingGame')),
                ('white_network', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='traininggamedistributedtask_predefined_jobs_as_white', to='trainings.Network')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RankingEstimationGameDistributedTask',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4)),
                ('status', models.CharField(choices=[('UNASSIGNED', 'Unassigned'), ('ONGOING', 'Ongoing'), ('DONE', 'Done'), ('CANCELED', 'Canceled')], default='UNASSIGNED', max_length=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_at', models.DateTimeField(auto_now=True)),
                ('expire_at', models.DateTimeField()),
                ('board_size_x', models.IntegerField(blank=True, default=19, null=True)),
                ('board_size_y', models.IntegerField(default=19)),
                ('handicap', models.IntegerField(blank=True, default=0, null=True)),
                ('komi', models.DecimalField(blank=True, decimal_places=1, default=7.0, max_digits=3, null=True)),
                ('rules_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('initial_position_sgf_file', models.FileField(blank=True, null=True, upload_to=katago_server.distributed_efforts.models.upload_initial_to, validators=[katago_server.contrib.validators.FileValidator(magic_types=('Smart Game Format (Go)',), max_size=10485760)])),
                ('initial_position_extra_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('game_extra_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='rankingestimationgamedistributedtask_games', to=settings.AUTH_USER_MODEL)),
                ('black_network', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='rankingestimationgamedistributedtask_predefined_jobs_as_black', to='trainings.Network')),
                ('result', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='games.RankingEstimationGame')),
                ('white_network', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='rankingestimationgamedistributedtask_predefined_jobs_as_white', to='trainings.Network')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]