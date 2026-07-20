from django.test import TestCase

from WebDatabase.models import Backbonetable, Backbonescartable


class GetBackboneScarViewTests(TestCase):
    def setUp(self):
        self.url = "/WebDatabase/getBackboneScar"
        self.backbone = Backbonetable.objects.create(
            name="BB_TEST_001",
            sequence="ATGCATGC",
            user="tester",
        )
        Backbonescartable.objects.create(
            backboneid=self.backbone,
            bsmbi="CGTCTC",
            bsai="GGTCTC",
            bbsi="GAAGAC",
            aari="CACCTGC",
            sapi="GCTCTTC",
        )

    def test_get_backbone_scar_success(self):
        response = self.client.get(self.url, {"id": self.backbone.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(len(payload["scar_info"]), 1)
        self.assertEqual(
            payload["scar_info"][0],
            {
                "bsmbi": "CGTCTC",
                "bsai": "GGTCTC",
                "bbsi": "GAAGAC",
                "aari": "CACCTGC",
                "sapi": "GCTCTTC",
            },
        )

    def test_get_backbone_scar_not_found(self):
        backbone_without_scar = Backbonetable.objects.create(
            name="BB_TEST_002",
            sequence="TTTTCCCC",
            user="tester",
        )

        response = self.client.get(self.url, {"id": backbone_without_scar.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "No such scar information")

    def test_get_backbone_scar_missing_id(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "id cannot be empty")

    def test_get_backbone_scar_empty_id(self):
        response = self.client.get(self.url, {"id": ""})

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "id cannot be empty")

    def test_get_backbone_scar_wrong_method(self):
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "Just GET method")
