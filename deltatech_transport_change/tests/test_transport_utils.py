# © 2025 Deltatech / Terrabit
# Tests for transport_utils standalone functions

import os
import tempfile

from odoo.tests.common import TransactionCase

from odoo.addons.deltatech_transport_change.models.transport_utils import (
    _bump_manifest_version_inplace,
    map_xmlid,
)


class TestMapXmlid(TransactionCase):
    def test_false_returns_empty_string(self):
        self.assertEqual(map_xmlid(False), "")

    def test_none_returns_empty_string(self):
        self.assertEqual(map_xmlid(None), "")

    def test_empty_string_returns_empty(self):
        self.assertEqual(map_xmlid(""), "")

    def test_plain_string(self):
        self.assertEqual(map_xmlid("hello"), "hello")

    def test_integer(self):
        self.assertEqual(map_xmlid(42), "42")

    def test_list_of_strings(self):
        self.assertEqual(map_xmlid(["a", "b"]), "a,b")

    def test_tuple_of_values(self):
        self.assertEqual(map_xmlid(("x", False, "y")), "x,,y")

    def test_single_record_no_xmlid(self):
        # res.partner.category created without external id → fallback model,id
        cat = self.env["res.partner.category"].create({"name": "Util Cat"})
        result = map_xmlid(cat)
        self.assertEqual(result, f"res.partner.category,{cat.id}")

    def test_single_record_with_xmlid(self):
        # Use a record that has an xmlid (base data)
        lang = self.env.ref("base.lang_en", raise_if_not_found=False)
        if lang is None:
            self.skipTest("base.lang_en not available")
        result = map_xmlid(lang)
        self.assertIn("base.lang_en", result)

    def test_multiple_records_no_xmlid(self):
        cat1 = self.env["res.partner.category"].create({"name": "Cat 1"})
        cat2 = self.env["res.partner.category"].create({"name": "Cat 2"})
        combined = cat1 | cat2
        result = map_xmlid(combined)
        self.assertIn(",", result)
        self.assertIn(f"res.partner.category,{cat1.id}", result)
        self.assertIn(f"res.partner.category,{cat2.id}", result)


class TestBumpManifestVersion(TransactionCase):
    def _write_manifest(self, path, content):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_bump_simple_version(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
            f.write('{"name": "Test", "version": "19.0.0.0.1", "data": []}\n')
            path = f.name
        try:
            changed, new_ver = _bump_manifest_version_inplace(path)
            self.assertTrue(changed)
            self.assertEqual(new_ver, "19.0.0.0.2")
        finally:
            os.unlink(path)

    def test_bump_idempotent_on_non_numeric_last_segment(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
            f.write('{"name": "Test", "version": "19.0.0.0.abc", "data": []}\n')
            path = f.name
        try:
            changed, new_ver = _bump_manifest_version_inplace(path)
            self.assertFalse(changed)
            self.assertIsNone(new_ver)
        finally:
            os.unlink(path)

    def test_bump_missing_version_key(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
            f.write('{"name": "Test", "data": []}\n')
            path = f.name
        try:
            changed, new_ver = _bump_manifest_version_inplace(path)
            self.assertFalse(changed)
        finally:
            os.unlink(path)

    def test_bump_nonexistent_file(self):
        changed, new_ver = _bump_manifest_version_inplace("/tmp/does_not_exist_manifest.py")
        self.assertFalse(changed)
        self.assertIsNone(new_ver)

    def test_bump_invalid_python(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
            f.write("this is not valid python !!!")
            path = f.name
        try:
            changed, new_ver = _bump_manifest_version_inplace(path)
            self.assertFalse(changed)
        finally:
            os.unlink(path)
