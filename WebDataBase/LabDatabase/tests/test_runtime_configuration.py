import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import engines
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from LabDatabase import design_engine
from WebDataWorld.runtime import ServiceSession, output_file, service_url, set_task_status, page_size
from WebDatabase.part_types import PartType


class RuntimeTests(SimpleTestCase):
    @override_settings(WEBDATABASE_API_BASE_URL='https://example.test/prefix/WebDatabase', SERVICE_HTTP_TIMEOUT=7)
    def test_service_override_and_timeout(self):
        url = service_url('WEBDATABASE_API_BASE_URL', '/Part')
        self.assertEqual(url, 'https://example.test/prefix/WebDatabase/Part')
        with patch('requests.Session.request') as request:
            with ServiceSession() as client:
                client.get(url)
            self.assertEqual(request.call_args.kwargs['timeout'], 7)

    @override_settings(EXPERIMENT_BASE_URL='')
    def test_missing_optional_service_is_explicit(self):
        with self.assertRaises(ImproperlyConfigured):
            service_url('EXPERIMENT_BASE_URL', 'part/1')

    @override_settings(TASK_STATUS_TTL_SECONDS=4321)
    def test_progress_writes_keep_same_ttl(self):
        with patch('WebDataWorld.runtime.cache.set') as write:
            for state in ('queued', 'processing', 'done'):
                set_task_status('task-1', state)
            self.assertEqual([c.kwargs['timeout'] for c in write.call_args_list], [4321] * 3)

    def test_output_path_creates_directory_and_joins_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'generated'
            target = Path(output_file(folder, 'user-123.xlsx'))
            self.assertEqual(target.parent, folder)
            target.write_bytes(b'example')
            self.assertTrue(target.is_file())
            with self.assertRaises(ValueError):
                output_file(folder, '../outside.xlsx')

    def test_assembly_helpers_follow_directory_override(self):
        from LabDatabase import views
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with override_settings(ASSEMBLY_INPUT_DIR=root / 'inputs', ASSEMBLY_OUTPUT_DIR=root / 'results'):
                self.assertEqual(Path(views._assembly_file_path('example')).parent, root / 'inputs')
                self.assertEqual(Path(views._ensure_task_output_dir('task')), root / 'results' / 'task')

    @override_settings(API_PAGE_SIZE=12, API_MAX_PAGE_SIZE=50, UPLOAD_PAGE_SIZE=25, UPLOAD_MAX_PAGE_SIZE=100)
    def test_pagination_limits(self):
        self.assertEqual(page_size(), 12)
        self.assertEqual(page_size(999), 50)
        self.assertEqual(page_size(-1), 1)
        self.assertEqual(page_size(upload=True), 25)
        self.assertEqual(page_size(999, upload=True), 100)

    def test_feature_file_is_bundled(self):
        from LabDatabase.CaculateModule.FeatureIdentify import featureIdentify
        featureIdentify()  # Must work with no developer Desktop directory.

    def test_namespaced_routes_keep_existing_names(self):
        self.assertEqual(reverse('lab:index'), reverse('index'))
        self.assertEqual(reverse('lab:login'), '/LabDatabase/login')
        self.assertEqual(reverse('api:login'), '/WebDatabase/login')
        self.assertEqual(reverse('lab:downloadtemplate', args=['part']), '/LabDatabase/download/part')

    def test_all_application_templates_compile(self):
        for app in ('LabDatabase', 'WebDatabase'):
            for path in (settings.BASE_DIR / app / 'templates').glob('*.html'):
                with self.subTest(path=path.name):
                    engines['django'].from_string(path.read_text(encoding='utf-8'))

    def test_home_template_links_render(self):
        from django.template.loader import render_to_string
        html = render_to_string('index.html', {'user': SimpleNamespace(is_authenticated=True, username='tester')})
        self.assertIn('/LabDatabase/user/tester', html)
        self.assertIn('/LabDatabase/download/part', html)
        self.assertNotIn('{% url', html)


class DesignConfigurationTests(SimpleTestCase):
    @override_settings(DESIGN_CONFIG={'backbones': {'ecoli': 'bb-ecoli', 'yeast': 'bb-yeast', 'bacillus': 'bb-bacillus', 'mammalian': 'bb-mammalian'}})
    def test_chassis_mapping_never_falls_through(self):
        with patch.object(design_engine.Backbonetable, 'objects') as manager:
            query = manager.exclude.return_value.exclude.return_value
            query.filter.return_value.first.return_value = None
            for chassis in ('ecoli', 'yeast', 'bacillus', 'mammalian'):
                design_engine._fetch_backbone_candidates(chassis)
                query.filter.assert_called_with(name__iexact='bb-' + chassis)
            with self.assertRaisesRegex(ValueError, '不支持'):
                design_engine._fetch_backbone_candidates('unknown')

    @override_settings(DESIGN_CONFIG={'backbones': {'ecoli': 'bb-ecoli'}})
    def test_unconfigured_chassis_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '尚未配置'):
            design_engine._fetch_backbone_candidates('bacillus')

    @override_settings(DESIGN_CONFIG={'part_strengths': {'7': {'value': 10, 'source': 'measured'}, '42': {'value': 30, 'source': 'demo'}}}, DESIGN_CANDIDATE_LIMIT=20)
    def test_strength_is_bound_to_id_not_name_order(self):
        first = SimpleNamespace(partid=7, name='Z', alias='')
        second = SimpleNamespace(partid=42, name='A', alias='')
        with patch.object(design_engine.Parttable, 'objects') as manager:
            query = manager.filter.return_value.exclude.return_value.exclude.return_value
            query.order_by.return_value = [first, second]
            before = design_engine._fetch_part_candidates(PartType.PROMOTER, 1, 100)
            first.name, second.name = 'A', 'Z'
            query.order_by.return_value = [second, first]
            after = design_engine._fetch_part_candidates(PartType.PROMOTER, 1, 100)
        self.assertEqual({p['id']: p['strength'] for p in before}, {p['id']: p['strength'] for p in after})
        self.assertEqual(before[0]['strength_source'], 'measured')

    @override_settings(DESIGN_CONFIG={'part_strengths': {}})
    def test_missing_strengths_are_not_invented(self):
        with self.assertRaisesRegex(ValueError, '尚未配置'):
            design_engine._fetch_part_candidates(PartType.PROMOTER, 1, 100)

    def test_nonfinite_strength_rejected(self):
        for value in ('nan', 'inf', '-inf', 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                design_engine._parse_numeric(value)

    @override_settings(DESIGN_REPOSITORY_TTL_HOURS=48)
    def test_design_expiry_uses_its_own_policy(self):
        from django.utils import timezone
        now = timezone.now()
        result = {'repository_name': 'example', 'selected_parts': [],
                  'selected_backbone': {'id': 3, 'name': 'bb'}, 'inputs': {}, 'strengths': {}}
        with patch.object(design_engine.CustomUser, 'objects'), patch.object(design_engine.Temporaryrepository, 'objects') as repos, patch.object(design_engine.timezone, 'now', return_value=now):
            design_engine.create_design_repository(SimpleNamespace(session={'info': {'uid': 1}}), result)
        self.assertEqual(repos.create.call_args.kwargs['repositoryexpire_time'], now + timezone.timedelta(hours=48))


class SettingsTests(SimpleTestCase):
    def test_production_settings_require_secret_and_use_secure_defaults(self):
        import os
        import runpy
        # Avoid any real .env and log directory; execute a temporary settings copy.
        source = (settings.BASE_DIR / 'WebDataWorld' / 'settings.py').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'project' / 'settings.py'
            path.parent.mkdir()
            path.write_text(source, encoding='utf-8')
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ImproperlyConfigured):
                    runpy.run_path(str(path))
            with patch.dict(os.environ, {'DJANGO_SECRET_KEY': 'test-only-unique-key'}, clear=True):
                config = runpy.run_path(str(path))
            self.assertFalse(config['DEBUG'])
            self.assertTrue(config['SESSION_COOKIE_SECURE'])
            self.assertTrue(config['CSRF_COOKIE_SECURE'])
            self.assertEqual(config['CSRF_TRUSTED_ORIGINS'], [])
            self.assertNotIn('*', config['ALLOWED_HOSTS'])

    def test_invalid_policy_value_fails_configuration(self):
        from WebDataWorld.settings import positive_env
        import os
        for value in ('0', '-1', 'nan', 'invalid'):
            with self.subTest(value=value), patch.dict(os.environ, {'TEST_POLICY': value}):
                with self.assertRaises(ImproperlyConfigured):
                    positive_env('TEST_POLICY', 5, float)
