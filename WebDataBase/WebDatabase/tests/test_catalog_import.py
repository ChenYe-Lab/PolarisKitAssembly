from pathlib import Path
from django.test import TransactionTestCase, SimpleTestCase
from django.core.management.base import CommandError
from django.db import IntegrityError
from WebDatabase.catalog_import import import_catalog, read_rows
from WebDatabase.models import Parttable, Backbonetable, Plasmidneed, Backbonefeaturetable


class LiteralParserTests(SimpleTestCase):
    def test_quotes_escapes_null_and_statement_text_are_data(self):
        text = "INSERT INTO `parttable` (`name`,`note`) VALUES ('it\\'s','a; DROP TABLE x;\\nnext'),('two',NULL);"
        rows = list(read_rows(text))
        self.assertEqual(rows[0][1], {'name': "it's", 'note': 'a; DROP TABLE x;\nnext'})
        self.assertIsNone(rows[1][1]['note'])

    def test_sql_expressions_are_rejected(self):
        with self.assertRaises(CommandError):
            list(read_rows('INSERT INTO `parttable` (`name`) VALUES (CONCAT(1,2));'))


class CatalogImportTests(TransactionTestCase):
    def setUp(self):
        self.dump = (Path(__file__).resolve().parents[3] / 'KitAssembly_Labdnadata_20260923_072954.sql').read_text(encoding='utf-8')

    def test_dry_run_then_import_preserves_counts_and_rejects_repeat(self):
        counts, skipped = import_catalog(self.dump, dry_run=True)
        self.assertEqual(sum(counts.values()), 2507)
        self.assertEqual(sum(skipped.values()), 8)
        self.assertFalse(Parttable.objects.exists())
        import_catalog(self.dump)
        self.assertEqual(Parttable.objects.count(), 84)
        self.assertEqual(Backbonetable.objects.count(), 76)
        self.assertEqual(Plasmidneed.objects.count(), 109)
        self.assertFalse(Backbonefeaturetable.objects.filter(feature_group__isnull=True).exists())
        with self.assertRaises(CommandError): import_catalog(self.dump)
        self.assertEqual(Parttable.objects.count(), 84)

    def test_invalid_data_does_not_partially_import(self):
        text = self.dump + '\nINSERT INTO `parttable` (`PartID`,`Name`) VALUES (999999,NULL);'
        with self.assertRaises((CommandError, IntegrityError)): import_catalog(text)
        self.assertFalse(Backbonetable.objects.exists())
