"""Run without MySQL: python -m unittest LabDatabase.tests.test_assembly_annotations -v"""
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
if not settings.configured:
    settings.configure(SECRET_KEY='annotation-tests', USE_TZ=True,
        INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes', 'WebDatabase'],
        AUTH_USER_MODEL='WebDatabase.CustomUser',
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
    import django
    django.setup()

from django.db import connection
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import SeqFeature, SimpleLocation, CompoundLocation
from LabDatabase.feature_records import (normalized_record, feature_rows, record_from_rows,
    genbank_text, read_genbank, semantic_data, first, restore_assembly_part_styles, write_record)
from LabDatabase.assembly_inputs import attach_source, shift_processed_part, prepare_inputs
from WebDatabase.assembly_results import save_assembly_result
from WebDatabase.models import (Parttable, Backbonetable, Plasmidneed, Partfeaturetable,
    Backbonefeaturetable, Plasmidfeaturetable, Parentparttable, Parentbackbonetable,
    Parentplasmidtable, Plasmidscartable, Plasmid_Culture_Functions)


def record(sequence='A' * 100):
    result = SeqRecord(Seq(sequence), id='example', name='example', description='.')
    result.annotations.update(topology='circular', molecule_type='DNA')
    return result


class AnnotationTests(unittest.TestCase):
    def test_reverse_origin_spanning_roundtrip(self):
        source = record()
        source.features = [SeqFeature(CompoundLocation([SimpleLocation(0, 10, -1),
            SimpleLocation(90, 100, -1)]), type='CDS', qualifiers={'label': ['reverse CDS']})]
        source = normalized_record(source)
        rows = feature_rows(source)
        self.assertEqual([(r['feature_start'], r['feature_end'], r['strand']) for r in rows],
                         [(1, 10, -1), (91, 100, -1)])
        restored = record_from_rows(str(source.seq), rows)
        self.assertEqual(semantic_data(source), semantic_data(restored))
        self.assertEqual(semantic_data(source), semantic_data(read_genbank(io.StringIO(genbank_text(source)))))

    def test_plasmid_internal_features_keep_sources_without_new_container(self):
        source = record()
        source.features = [SeqFeature(SimpleLocation(0, 100, strand), type='misc_feature',
            qualifiers={'label': [str(strand)]}) for strand in (1, -1)]
        attach_source(source, 'plasmid', SimpleNamespace(pk=9, name='L2_module', level=2))
        normalized = normalized_record(source)
        self.assertEqual(len(normalized.features), 2)
        self.assertEqual({f.location.strand for f in normalized.features}, {1, -1})
        for feature in normalized.features:
            self.assertEqual(first(feature.qualifiers, 'source_type'), 'plasmid')
            self.assertEqual(first(feature.qualifiers, 'source_id'), '9')
            self.assertTrue(first(feature.qualifiers, 'source_revision'))
            self.assertNotEqual(first(feature.qualifiers, 'source_container'), 'true')

    def test_empty_plasmid_does_not_gain_features(self):
        source = record()
        attach_source(source, 'plasmid', SimpleNamespace(pk=9, name='L2_module', level=2))
        self.assertEqual(source.features, [])

    def test_existing_source_information_is_preserved(self):
        source = record()
        feature = SeqFeature(SimpleLocation(10, 30), type='CDS', qualifiers={
            'source_type': ['part'], 'source_id': ['17'], 'source_revision': ['original']})
        source.features = [feature]
        attach_source(source, 'plasmid', SimpleNamespace(pk=9, name='L2_module', level=2))
        self.assertEqual(feature.qualifiers['source_id'], ['17'])
        self.assertEqual(feature.qualifiers['source_type'], ['part'])
        self.assertEqual(feature.qualifiers['source_revision'], ['original'])

    def test_attach_backbone_removes_only_generated_containers(self):
        source = record()
        source.features = [SeqFeature(SimpleLocation(0, 100), type='rep_origin'),
            SeqFeature(SimpleLocation(0, 100), qualifiers={'source_container': ['true']}),
            SeqFeature(SimpleLocation(0, 100), qualifiers={'indicates_part': ['true']})]
        attach_source(source, 'backbone', SimpleNamespace(pk=1, name='vector'))
        self.assertEqual([f.type for f in source.features], ['rep_origin'])
        self.assertEqual(first(source.features[0].qualifiers, 'source_type'), 'backbone')

    def test_backbone_generated_indicator_removed_but_internal_feature_kept(self):
        backbone = record(); backbone.id = 'backbone-1'
        backbone.annotations['comment'] = 'polaris_source_type=backbone'
        result = record()
        result.features = [SeqFeature(SimpleLocation(0, 50), type='misc_feature',
            qualifiers={'indicates_part': True, 'source': backbone.id}),
            SeqFeature(SimpleLocation(0, 50), type='rep_origin', qualifiers={'label': ['ori']})]
        restore_assembly_part_styles(result, [backbone])
        self.assertEqual([f.type for f in result.features], ['rep_origin'])

    def test_part_coordinates_shift_by_actual_prefix(self):
        source = record('ATGCCCTAA')
        source.features = [SeqFeature(SimpleLocation(0, 9, -1), type='CDS')]
        shift_processed_part(source, 'GAAGACCTA' + str(source.seq) + 'AAGGTCTTC')
        self.assertEqual((int(source.features[0].location.start), int(source.features[0].location.end)), (9, 18))
        self.assertEqual(source.features[0].location.strand, -1)

    def test_real_assembly_retains_internal_features_without_plasmid_container(self):
        from LabDatabase.GGModule.SupportGG import SupportGG
        backbone = record('GGTCTCA' + 'GCTT' + 'ACGT' * 15 + 'AATG' + 'TGAGACC')
        plasmid = record('GGTCTCA' + 'AATG' + 'ATGC' * 15 + 'GCTT' + 'TGAGACC')
        for rec, kind, typ in [(backbone, 'backbone', 'rep_origin'), (plasmid, 'plasmid', 'CDS')]:
            rec.id = rec.name = kind + '-1'
            rec.features = [SeqFeature(SimpleLocation(15, 35, -1), type=typ, qualifiers={'label': [typ]})]
            attach_source(rec, kind, SimpleNamespace(pk=1, name='L1_module' if kind == 'plasmid' else 'vector', level=1))
            rec.annotations['comment'] = 'polaris_source_type=' + kind
        with tempfile.TemporaryDirectory() as folder:
            paths = [str(Path(folder) / (rec.id + '.gb')) for rec in (backbone, plasmid)]
            for path, rec in zip(paths, (backbone, plasmid)):
                write_record(path, normalized_record(rec))
            engine = SupportGG(paths, [backbone.id, plasmid.id])
            engine.assemblyPart('L2_result', 'BsaI')
            self.assertEqual(len(engine.simulation.construct_records), 1)
            engine.show(str(Path(folder) / 'result'))
            result = engine.simulation.construct_records[0]
            self.assertTrue(any(f.type == 'rep_origin' for f in result.features))
            self.assertTrue(any(f.type == 'CDS' for f in result.features))
            self.assertFalse(any(first(f.qualifiers, 'source_container') == 'true' for f in result.features))
            cds = next(f for f in result.features if f.type == 'CDS')
            self.assertEqual(first(cds.qualifiers, 'source_type'), 'plasmid')
            self.assertEqual(first(cds.qualifiers, 'source_id'), '1')
            self.assertFalse(any(first(f.qualifiers, 'source') == backbone.id and
                                 first(f.qualifiers, 'indicates_part').lower() == 'true' for f in result.features))
            saved = next((Path(folder) / 'result').rglob('L2_result.gb'))
            self.assertEqual(semantic_data(result), semantic_data(read_genbank(saved)))
            # The report library leaves cyclic figure/file objects for GC on Windows.
            import matplotlib.pyplot as plt
            import gc
            plt.close('all')
            gc.collect()


MODELS = [Parttable, Backbonetable, Plasmidneed, Partfeaturetable, Backbonefeaturetable,
    Plasmidfeaturetable, Parentparttable, Parentbackbonetable, Parentplasmidtable,
    Plasmidscartable, Plasmid_Culture_Functions]


class PersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with connection.schema_editor() as editor:
            for model in MODELS:
                editor.create_model(model)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as editor:
            for model in reversed(MODELS):
                editor.delete_model(model)

    def setUp(self):
        with connection.cursor() as cursor:
            for model in reversed(MODELS):
                cursor.execute('DELETE FROM ' + connection.ops.quote_name(model._meta.db_table))
        self.part = Parttable.objects.create(name='part', lengthinlevel0=100, level0sequence='A'*100, type=1)
        self.backbone = Backbonetable.objects.create(name='vector', sequence='A'*100, user='tester')
        self.parent = Plasmidneed.objects.create(name='L1_input', level='1', length=100,
                                                sequenceconfirm='A'*100, user='tester')
        source = record()
        source.features = [SeqFeature(SimpleLocation(10, 30, -1), type='CDS', qualifiers={'label': ['gene']})]
        self.payload = {'name': 'result', 'sequence': str(source.seq),
            'assembly_features': feature_rows(normalized_record(source)),
            'parts': [], 'backbones': [self.backbone.pk], 'plasmids': [self.parent.pk]}

    def test_save_features_and_parent_level_then_reuse(self):
        saved = save_assembly_result(self.payload, 'tester')
        self.assertEqual(saved['level'], '2')
        child = Plasmidneed.objects.get(pk=saved['plasmid_id'])
        self.assertEqual(Plasmidfeaturetable.objects.get(plasmidid=child).strand, -1)
        self.assertTrue(Parentplasmidtable.objects.filter(sonplasmidid=child, parentplasmidid=self.parent).exists())
        self.assertTrue(Parentbackbonetable.objects.filter(sonplasmidid=child, parentbackboneid=self.backbone).exists())
        self.payload.update(name='level3', plasmids=[child.pk])
        self.assertEqual(save_assembly_result(self.payload, 'tester')['level'], '3')

    def test_single_part_is_level_one(self):
        self.payload.update(parts=[self.part.pk], plasmids=[])
        self.assertEqual(save_assembly_result(self.payload, 'tester')['level'], '1')

    def test_repeated_save_does_not_duplicate_features_or_edges(self):
        save_assembly_result(self.payload, 'tester')
        save_assembly_result(self.payload, 'tester')
        self.assertEqual(Plasmidfeaturetable.objects.count(), 1)
        self.assertEqual(Parentplasmidtable.objects.count(), 1)

    def test_late_failure_rolls_back_sequence_features_and_parents(self):
        saved = save_assembly_result(self.payload, 'tester')
        self.payload.update(sequence='C'*100, plasmids=[], parts=[self.part.pk])
        with patch.object(Parentparttable.objects, 'bulk_create', side_effect=RuntimeError('write failed')):
            with self.assertRaises(RuntimeError):
                save_assembly_result(self.payload, 'tester')
        child = Plasmidneed.objects.get(pk=saved['plasmid_id'])
        self.assertEqual(child.sequenceconfirm, 'A'*100)
        self.assertEqual(child.level, '2')
        self.assertEqual(Plasmidfeaturetable.objects.filter(plasmidid=child).count(), 1)
        self.assertTrue(Parentplasmidtable.objects.filter(sonplasmidid=child, parentplasmidid=self.parent).exists())

    def test_invalid_feature_rejected_without_writes(self):
        self.payload['assembly_features'][0]['feature_end'] = 101
        with self.assertRaises(ValueError):
            save_assembly_result(self.payload, 'tester')
        self.assertFalse(Plasmidneed.objects.filter(name='result').exists())

    def test_inputs_are_refreshed_after_database_annotation_edit(self):
        Backbonefeaturetable.objects.create(backboneid=self.backbone, feature_start=2, feature_end=20,
            feature_type='rep_origin', feature_label='old', feature_color='', feature_apeinfo='')
        data = {'backbones': [self.backbone.pk], 'parts': [], 'plasmids': [self.parent.pk]}
        with tempfile.TemporaryDirectory() as folder:
            files, _, _ = prepare_inputs(data, folder, lambda _: 'BsaI', None, lambda name: name)
            self.assertEqual(first(read_genbank(files[0]).features[0].qualifiers, 'label'), 'old')
            Backbonefeaturetable.objects.update(feature_label='new')
            files, _, _ = prepare_inputs(data, folder, lambda _: 'BsaI', None, lambda name: name)
            self.assertEqual(first(read_genbank(files[0]).features[0].qualifiers, 'label'), 'new')

    def test_feature_migration_adopts_legacy_table_without_losing_rows(self):
        from importlib import import_module
        from django.apps import apps
        old = Backbonefeaturetable.objects.create(backboneid=self.backbone, feature_start=2,
            feature_end=20, feature_type='rep_origin', feature_label='legacy',
            feature_color='', feature_apeinfo='')
        with connection.cursor() as cursor:
            for column in ('strand', 'feature_group', 'segment_order', 'location_operator',
                           'coordinate_system', 'feature_metadata'):
                cursor.execute('ALTER TABLE "BackboneFeatureTable" DROP COLUMN "' + column + '"')
        migration = import_module('WebDatabase.migrations.0004_assembly_feature_metadata')
        with connection.schema_editor() as editor:
            migration.ensure_feature_tables(apps, editor)
        old.refresh_from_db()
        self.assertEqual(old.feature_label, 'legacy')
        self.assertEqual((old.feature_start, old.feature_end), (2, 20))
        self.assertIsNone(old.strand)

    def test_explicit_level_cannot_place_parent_above_child(self):
        self.payload['level'] = 1
        with self.assertRaises(ValueError):
            save_assembly_result(self.payload, 'tester')

    def test_replacing_ancestor_with_descendant_is_rejected(self):
        child = save_assembly_result(self.payload, 'tester')
        self.payload.update(name=self.parent.name, plasmids=[child['plasmid_id']])
        with self.assertRaisesRegex(ValueError, 'cycle'):
            save_assembly_result(self.payload, 'tester')


if __name__ == '__main__':
    unittest.main()
