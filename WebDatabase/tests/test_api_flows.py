from __future__ import annotations

import json

from django.test import TestCase
from django.urls import resolve

from WebDatabase.models import (
    Backbone_Culture_Functions,
    Backbonetable,
    Backbonescartable,
    CustomUser,
    Partscartable,
    Parttable,
    Plasmid_Culture_Functions,
    Plasmidneed,
    Plasmidscartable,
)
from WebDatabase.tests.test_urls import URL_CASES


class WebDatabaseApiFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create(
            uname="tester",
            username="tester",
            email="tester@example.com",
            role=CustomUser.UserRole.USER,
            is_active=True,
        )

        cls.part = Parttable.objects.create(
            name="part_seed",
            alias="p_seed",
            lengthinlevel0=4,
            level0sequence="ATGC",
            confirmedsequence="ATGC",
            insertsequence="AT",
            sourceorganism="E.coli",
            reference="seed-ref",
            note="seed",
            type=1,
            user=cls.user.uname,
            tag="normal",
        )
        Partscartable.objects.create(
            part_id=cls.part,
            bsmbi="AB",
            bsai="AB",
            bbsi="AB",
            aari="AB",
            sapi="AB"
        )

        cls.backbone = Backbonetable.objects.create(
            name="bb_seed",
            sequence="ATGCATGC",
            species="E.coli",
            copynumber="high",
            user=cls.user.uname,
            tag="normal",
        )
        Backbone_Culture_Functions.objects.create(
            backbone_id=cls.backbone,
            function_type="ori",
            function_content="pMB1",
        )
        Backbone_Culture_Functions.objects.create(
            backbone_id=cls.backbone,
            function_type="marker",
            function_content="Amp",
        )
        Backbonescartable.objects.create(
            backboneid=cls.backbone,
            bsmbi="AB",
            bsai="AB",
            bbsi="AB",
            aari="AB",
            sapi="AB",
        )

        cls.plasmid = Plasmidneed.objects.create(
            name="plasmid_seed",
            level="1",
            length=8,
            sequenceconfirm="ATGCATGC",
            plate="P1",
            state=1,
            user=cls.user.uname,
            alias="pl_seed",
            tag="normal",
        )
        Plasmid_Culture_Functions.objects.create(
            plasmid_id=cls.plasmid,
            function_type="ori",
            function_content="p15A",
        )
        Plasmid_Culture_Functions.objects.create(
            plasmid_id=cls.plasmid,
            function_type="marker",
            function_content="Kan",
        )
        Plasmidscartable.objects.create(
            plasmidid=cls.plasmid,
            bsmbi="CGTCTC",
            bsai="GGTCTC",
            bbsi="GAAGAC",
            aari="CACCTGC",
            sapi="GCTCTTC",
        )

    def setUp(self):
        session = self.client.session
        session["info"] = {"uid": self.user.uid, "uname": self.user.uname}
        session.save()

    def test_part_api_flow(self):
        add_payload = {
            "name": "part_api_1",
            "alias": "alias_api_1",
            "Level0Sequence": "TTGACA",
            "ConfirmedSequence": "TTGACA",
            "InsertSequence": "TTGA",
            "source": "E.coli",
            "reference": "paper-x",
            "note": "note-x",
            "type": "promoter",
        }
        resp = self.client.post(
            "/WebDatabase/AddPartData",
            data=json.dumps(add_payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), "Added part data")

        resp = self.client.get("/WebDatabase/PartName", {"name": "part_api_1"})
        self.assertEqual(resp.status_code, 200)
        part_data = resp.json()["data"]
        self.assertEqual(part_data["name"], "part_api_1")
        self.assertEqual(part_data["type"], 1)

        resp = self.client.get("/WebDatabase/PartSeq", {"seq": "TGAC"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(item["name"] == "part_api_1" for item in resp.json()))

        resp = self.client.post(
            "/WebDatabase/UpdatePartSequence",
            data=json.dumps({"name": "part_api_1", "sequence": "AACCGG"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        part_id = Parttable.objects.get(name="part_api_1").partid
        resp = self.client.get("/WebDatabase/GetPartSeqByID", {"partid": part_id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["level0sequence"], "AACCGG")

    def test_backbone_api_flow(self):
        add_payload = {
            "name": "bb_api_1",
            "sequence": "AATTCCGG",
            "species": "B.subtilis",
            "copynumber": "low",
            "note": "bb-note",
            "alias": "bb-alias",
            "tag": "normal",
        }
        resp = self.client.post(
            "/WebDatabase/AddBackbone",
            data=json.dumps(add_payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), "Added backbone data")

        backbone = Backbonetable.objects.get(name="bb_api_1")

        resp = self.client.get("/WebDatabase/BackboneName", {"name": "bb_api_1"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(resp.json()["data"]["name"], "bb_api_1")

        resp = self.client.post(
            "/WebDatabase/UpdateBackboneSequence",
            data=json.dumps({"name": "bb_api_1", "sequence": "GGGGCCCC"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.get(
            "/WebDatabase/GetBackboneSeqByID",
            {"backboneid": backbone.id},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["sequence"], "GGGGCCCC")

    def test_plasmid_api_flow(self):
        add_payload = {
            "name": "plasmid_api_1",
            "level": "2",
            "sequence": "CCGGTTAA",
            "plate": "P2",
            "state": 1,
            "note": "plasmid-note",
            "alias": "plasmid-alias",
            "ParentInfo": "parent-info",
            "tag": "normal",
        }
        resp = self.client.post(
            "/WebDatabase/AddPlasmidData",
            data=json.dumps(add_payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), "Plasmid Data Added")

        plasmid = Plasmidneed.objects.get(name="plasmid_api_1")

        resp = self.client.get("/WebDatabase/PlasmidName", {"name": "plasmid_api_1"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(resp.json()["data"]["name"], "plasmid_api_1")

        resp = self.client.post(
            "/WebDatabase/UpdatePlasmidSequence",
            data=json.dumps({"name": "plasmid_api_1", "sequence": "TTTTAAAA"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.get(
            "/WebDatabase/PlasmidSeqByID",
            {"plasmidid": plasmid.plasmidid},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["sequenceconfirm"], "TTTTAAAA")

    def test_scar_api_flow(self):
        resp = self.client.post(
            "/WebDatabase/setPartScar",
            data=json.dumps(
                {
                    "name": self.part.name,
                    "bsmbi": "AAAAAA",
                    "bsai": "BBBBBB",
                    "bbsi": "CCCCCC",
                    "aari": "DDDDDD",
                    "sapi": "EEEEEE",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.get("/WebDatabase/getPartScar", {"id": self.part.partid})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(resp.json()["scar_info"][0]["bsmbi"], "AAAAAA")

        resp = self.client.post(
            "/WebDatabase/setBackboneScar",
            data=json.dumps(
                {
                    "backboneid": self.backbone.id,
                    "bsmbi": "111111",
                    "bsai": "222222",
                    "bbsi": "333333",
                    "aari": "444444",
                    "sapi": "555555",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.get("/WebDatabase/getBackboneScar", {"id": self.backbone.id})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(resp.json()["scar_info"][0]["bsmbi"], "111111")

        resp = self.client.post(
            "/WebDatabase/setPlasmidScar",
            data=json.dumps(
                {
                    "plasmidid": self.plasmid.plasmidid,
                    "bsmbi": "AAAA11",
                    "bsai": "BBBB22",
                    "bbsi": "CCCC33",
                    "aari": "DDDD44",
                    "sapi": "EEEE55",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.get(
            "/WebDatabase/getPlasmidScar",
            {"plasmidid": self.plasmid.plasmidid},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(resp.json()["scar_info"][0]["bsmbi"], "AAAA11")

    def test_repository_api_flow(self):
        resp = self.client.post(
            "/WebDatabase/createRepo",
            data=json.dumps({"Name": "repo_api", "Note": "unit-test"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.get("/WebDatabase/getrepos")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertTrue(any(repo["name"] == "repo_api" for repo in resp.json()["repo"]))

        resp = self.client.post(
            "/WebDatabase/getrepo",
            data=json.dumps({"Name": "repo_api"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.post(
            "/WebDatabase/addparts",
            data=json.dumps(
                {
                    "RepoName": "repo_api",
                    "part_ids": [self.part.partid],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(resp.json()["total_parts"], 1)

        resp = self.client.post(
            "/WebDatabase/addbackbones",
            data=json.dumps(
                {
                    "RepoName": "repo_api",
                    "backbone_ids": [self.backbone.id],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.post(
            "/WebDatabase/addplasmids",
            data=json.dumps(
                {
                    "RepoName": "repo_api",
                    "plasmid_ids": [self.plasmid.plasmidid],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.get("/WebDatabase/getparts")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertIn(self.part.partid, resp.json()["parts"])

    def test_user_stat_api_flow(self):
        resp = self.client.get("/WebDatabase/getuserlist")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertTrue(any(user["uname"] == self.user.uname for user in resp.json()["data"]))

        resp = self.client.get("/WebDatabase/getalluseruploadlist")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        resp = self.client.get(f"/WebDatabase/getuserpartcount/{self.user.uname}")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertGreaterEqual(resp.json()["count"], 1)

        resp = self.client.get(f"/WebDatabase/getuserbackbonecount/{self.user.uname}")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertGreaterEqual(resp.json()["count"], 1)

        resp = self.client.get(f"/WebDatabase/getuserplasmidcount/{self.user.uname}")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertGreaterEqual(resp.json()["count"], 1)


class WebDatabaseAllApiRouteTests(TestCase):
    def test_all_webdatabase_api_paths_are_callable(self):
        for path, view_func in URL_CASES:
            with self.subTest(path=path):
                match = resolve(path)
                self.assertIs(match.func, view_func)
