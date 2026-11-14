"""Regression checks for extraction boundaries; run after extract_catalogue.py."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from extract_catalogue import ROOT, parse_game_xml, parse_jsonc, xml_rows


class CatalogueChecks(unittest.TestCase):
    def test_game_xml_control_entities_and_tail(self):
        xml = '<root><part Name="ID" DisplayName="bird" AmmoChar="&amp;Y&#15;">before<b>middle</b>after</part></root>'
        root = parse_game_xml(xml)
        self.assertEqual(root[0].attrib["AmmoChar"], "&Y\x0f")
        rows = list(xml_rows(root, "fixture.xml", "/root[1]"))
        self.assertTrue(any(r["src"] == "bird" and r["classification"] == "display-candidate" for r in rows))
        self.assertTrue(any(r["src"] == "ID" and r["classification"] == "identifier-review" for r in rows))
        self.assertTrue(any(r["src"] == "after" and r["kind"] == "xml-tail" for r in rows))

    def test_jsonc_preserves_quoted_comments_and_trailing_comma(self):
        self.assertEqual(parse_jsonc('{// comment\n"url":"https://example.test/a/*b*/",/* multi\nline */"values":["x,}",],}'),
                         {"url": "https://example.test/a/*b*/", "values": ["x,}"]})

    def test_csharp_semantic_literals_and_dynamic_template(self):
        source = r'''
class Fixture {
 void Render() {
  // "Not a literal"
  Popup.Show("You receive " + item + "!");
  var options = new[] { "Save and Quit", "&KRestore Checkpoint" };
  var title = $"Hello {who}!";
  var quote = @"one ""quote""";
  var escaped = "line\nnext";
  Strings._S("internal-key", "Default phrase");
 }
}'''
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "Fixture.cs").write_text(source)
            target = directory / "rows.jsonl"
            result = subprocess.run(["dotnet", "run", "--no-build", "--no-restore", "--configuration", "Release", "--project",
                                     str(ROOT / "tools/text_catalogue/TextCatalogue.csproj"), "--", str(directory), str(target)],
                                    check=True, text=True, capture_output=True)
            self.assertEqual(json.loads(result.stdout)["parseErrors"], 0)
            rows = [json.loads(line) for line in target.read_text().splitlines()]
            texts = {r["src"] for r in rows}
            self.assertNotIn("Not a literal", texts)
            self.assertIn('one "quote"', texts)
            self.assertIn("line\nnext", texts)
            self.assertTrue(any(r["src"] == "You receive {0}!" and r["holes"] == ["item"] for r in rows))
            self.assertTrue(any(r["src"] == "Hello {0}!" and r["kind"] == "interpolation" for r in rows))
            self.assertTrue(any(r["src"] == "internal-key" and r["classification"] == "localization-key" for r in rows))


if __name__ == "__main__": unittest.main()
