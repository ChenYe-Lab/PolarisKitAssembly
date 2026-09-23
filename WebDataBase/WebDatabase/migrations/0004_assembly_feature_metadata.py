"""Register legacy feature tables and add lossless annotation metadata.

Older deployments created these tables outside migrations. Adopt existing tables
without replacing their data; a fresh database receives the full tables.
"""
import django.db.models.deletion
from django.db import migrations, models
from django.db.migrations.state import ProjectState


def ensure_feature_tables(apps, schema_editor):
    tables = {name.casefold() for name in schema_editor.connection.introspection.table_names()}
    for name in ('Backbonefeaturetable', 'Partfeaturetable', 'Plasmidfeaturetable'):
        model = apps.get_model('WebDatabase', name)
        if model._meta.db_table.casefold() not in tables:
            schema_editor.create_model(model)
            continue
        with schema_editor.connection.cursor() as cursor:
            columns = {column.name for column in schema_editor.connection.introspection
                       .get_table_description(cursor, model._meta.db_table)}
        missing = [field for field in model._meta.local_fields if field.column not in columns]
        # SQLite remakes tables for some ADD COLUMN operations. Its model must
        # describe only the columns present at each step, not all future fields.
        state = ProjectState.from_apps(apps)
        model_name = model._meta.model_name
        for field in missing:
            state.remove_field('WebDatabase', model_name, field.name)
        for field in missing:
            state.add_field('WebDatabase', model_name, field.name, field.clone(), preserve_default=True)
            step_model = state.apps.get_model('WebDatabase', name)
            schema_editor.add_field(step_model, step_model._meta.get_field(field.name))


def feature_model(name, table, parent, pk):
    return migrations.CreateModel(name=name, fields=[
        (pk, models.AutoField(primary_key=True, serialize=False)),
        (parent + 'id', models.ForeignKey(to='WebDatabase.' + {'backbone': 'Backbonetable',
            'part': 'Parttable', 'plasmid': 'Plasmidneed'}[parent],
            on_delete=django.db.models.deletion.CASCADE, db_column=parent + 'id')),
        ('feature_start', models.IntegerField()), ('feature_end', models.IntegerField()),
        ('feature_type', models.CharField(max_length=50)),
        ('feature_label', models.CharField(max_length=50)),
        ('feature_color', models.CharField(max_length=50)),
        ('feature_apeinfo', models.CharField(max_length=50)),
        ('strand', models.SmallIntegerField(null=True, blank=True)),
        ('feature_group', models.CharField(max_length=64, blank=True, default='')),
        ('segment_order', models.PositiveIntegerField(default=0)),
        ('location_operator', models.CharField(max_length=20, blank=True, default='')),
        ('coordinate_system', models.CharField(max_length=30, default='one_based_closed')),
        ('feature_metadata', models.JSONField(default=dict, blank=True)),
    ], options={'db_table': table, 'managed': True})


class Migration(migrations.Migration):
    dependencies = [('WebDatabase', '0003_backbonetable_dbdtable_lbddimertable_lbdnrtable_and_more')]
    operations = [migrations.SeparateDatabaseAndState(
        state_operations=[feature_model('Backbonefeaturetable', 'BackboneFeatureTable', 'backbone', 'bfif'),
                          feature_model('Partfeaturetable', 'PartFeatureTable', 'part', 'pfid'),
                          feature_model('Plasmidfeaturetable', 'PlasmidFeatureTable', 'plasmid', 'pfid')]),
        migrations.RunPython(ensure_feature_tables)]
