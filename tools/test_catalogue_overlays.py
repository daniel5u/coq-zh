import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import catalogue_overlays as overlays


class OverlayChecks(unittest.TestCase):
    def test_commands_preserve_ids_and_existing_chinese(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); base = root / "base"; out = root / "mod"
            for p in [base, out, root / "data", root / "work/catalogue_translation"]: p.mkdir(parents=True, exist_ok=True)
            (base / "Commands.xml").write_text('<commands><command ID="CmdA" DisplayText="Jump" Auto="true"><keyboard Key="Space" /></command><command ID="CmdB" DisplayText="Menu" /></commands>')
            (out / "Commands.xml").write_text('<commands Lang="zh"><command ID="CmdB" DisplayText="菜单" /></commands>')
            rows = []
            for i, (key, en, zh) in enumerate([("CmdA", "Jump", "跳跃"), ("CmdB", "Menu", "别的译法")], 1):
                rows.append({"id": key, "src": en, "zh": zh, "install_xml": True,
                             "context": [{"origin": "data", "file": "Commands.xml", "path": f"/commands[1]/command[{i}]/@DisplayText",
                                          "owner": [{"tag": "commands"}, {"tag": "command", "ID": key}]}]})
            (root / "data/catalogue_zh.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
            with patch.multiple(overlays, ROOT=root, OUT=out, DEFAULT_BASE=base):
                generated, report = overlays.build()
            tree = ET.parse(out / "Catalogue_commands.xml").getroot()
            self.assertEqual(tree.attrib, {"Lang": "zh", "LoadPriority": "-1100"})
            self.assertEqual(len(tree), 1)
            self.assertEqual(tree[0].attrib, {"ID": "CmdA", "DisplayText": "跳跃"})
            self.assertEqual(len(tree[0]), 0)  # No key binding or control flags copied.
            self.assertEqual({r["status"] for r in report}, {"generated", "already-localized"})

    def test_anatomy_variant_changes_description_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); base = root / "base"; out = root / "mod"
            for p in [base, out, root / "data", root / "work/catalogue_translation"]: p.mkdir(parents=True, exist_ok=True)
            (base / "Bodies.xml").write_text('<bodies><bodyparttypevariants><bodyparttypevariant Type="Equipment Rack" VariantOf="Back" Description="Rack" Category="Cybernetic" /></bodyparttypevariants></bodies>')
            record = {"id": "rack", "src": "Rack", "zh": "装备架", "install_xml": True,
                      "context": [{"origin": "data", "file": "Bodies.xml", "path": "/bodies[1]/bodyparttypevariants[1]/bodyparttypevariant[1]/@Description",
                                   "owner": [{"tag": "bodies"}, {"tag": "bodyparttypevariants"},
                                             {"tag": "bodyparttypevariant", "Type": "Equipment Rack", "VariantOf": "Back"}]}]}
            (root / "data/catalogue_zh.jsonl").write_text(json.dumps(record) + "\n")
            with patch.multiple(overlays, ROOT=root, OUT=out, DEFAULT_BASE=base):
                overlays.build()
            variant = ET.parse(out / "Catalogue_bodies.xml").getroot()[0][0]
            self.assertEqual(variant.attrib, {"Type": "Equipment Rack", "VariantOf": "Back", "Description": "装备架"})
            self.assertNotIn("Category", variant.attrib)

    def test_implicit_anatomy_description_and_changed_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); base = root / "base"; out = root / "mod"
            for p in [base, out, root / "data", root / "work/catalogue_translation"]: p.mkdir(parents=True, exist_ok=True)
            source = base / "Bodies.xml"
            source.write_text('<bodies><bodyparttypes><bodyparttype Type="Head" Category="Animal" /></bodyparttypes></bodies>')
            record = {"id": "head", "src": "Head", "zh": "头部", "install_xml": True,
                      "context": [{"origin": "data", "file": "Bodies.xml", "path": "/bodies[1]/bodyparttypes[1]/bodyparttype[1]/@Description",
                                   "fallback": {"source_attribute": "Type"},
                                   "owner": [{"tag": "bodies"}, {"tag": "bodyparttypes"}, {"tag": "bodyparttype", "Type": "Head"}]}]}
            (root / "data/catalogue_zh.jsonl").write_text(json.dumps(record) + "\n")
            with patch.multiple(overlays, ROOT=root, OUT=out, DEFAULT_BASE=base):
                overlays.build()
                label = ET.parse(out / "Catalogue_bodies.xml").getroot()[0][0]
                self.assertEqual(label.attrib, {"Type": "Head", "Description": "头部"})
                source.write_text('<bodies><bodyparttypes><bodyparttype Type="Head" Description="Changed label" /></bodyparttypes></bodies>')
                with self.assertRaisesRegex(ValueError, "Stale catalogue source"): overlays.build()

    def test_stale_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); base = root / "base"; out = root / "mod"
            for p in [base, out, root / "data", root / "work/catalogue_translation"]: p.mkdir(parents=True, exist_ok=True)
            (base / "Commands.xml").write_text('<commands><command ID="CmdA" DisplayText="New text" /></commands>')
            record = {"id": "a", "src": "Old text", "zh": "旧文字", "install_xml": True,
                      "context": [{"origin": "data", "file": "Commands.xml", "path": "/commands[1]/command[1]/@DisplayText",
                                   "owner": [{"tag": "commands"}, {"tag": "command", "ID": "CmdA"}]}]}
            (root / "data/catalogue_zh.jsonl").write_text(json.dumps(record) + "\n")
            with patch.multiple(overlays, ROOT=root, OUT=out, DEFAULT_BASE=base):
                with self.assertRaisesRegex(ValueError, "Stale catalogue source"): overlays.build()
            self.assertFalse((out / "Catalogue_commands.xml").exists())


if __name__ == "__main__": unittest.main()
