# Generated by Django 3.0.1 on 2020-01-19 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetworkBayesianRankingConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number_of_iterations', models.IntegerField(default=10, help_text='updating log_gamma is iterative', verbose_name='number of iterations')),
            ],
            options={
                'verbose_name': 'Configuration: Parameters for updating the ranking',
            },
        ),
        migrations.DeleteModel(
            name='RankingGameGeneratorConfiguration',
        ),
        migrations.AlterField(
            model_name='network',
            name='log_gamma_lower_confidence',
            field=models.FloatField(db_index=True, default=0, verbose_name='minimal ranking'),
        ),
        migrations.AlterField(
            model_name='network',
            name='log_gamma_upper_confidence',
            field=models.FloatField(db_index=True, default=0, verbose_name='maximal ranking'),
        ),
    ]
