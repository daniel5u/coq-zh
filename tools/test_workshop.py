import json
from pathlib import Path
import tempfile
import unittest

import workshop


class WorkshopChecks(unittest.TestCase):
    def info(self, **extra):
        return {"WorkshopId": 0, "Title": "T", "Description": 'line "one"\\two\n二', "ImagePath": "preview.png",
                "Visibility": "0", **extra}

    def test_new_item_maps_game_visibility_and_escapes_text(self):
        vdf = workshop.build_vdf(self.info(), Path("/c"), Path("/p.png"), "note")
        self.assertIn('"appid"\t"333640"', vdf)
        self.assertIn('"publishedfileid"\t"0"', vdf)
        self.assertIn('"visibility"\t"2"', vdf)  # game "0" (private) -> SteamCMD 2
        self.assertIn('"description"\t"line \\"one\\"\\\\two\n二"', vdf)

    def test_existing_item_keeps_steam_visibility(self):
        vdf = workshop.build_vdf(self.info(WorkshopId=123, Visibility="2"), Path("/c"), Path("/p.png"), "n")
        self.assertIn('"publishedfileid"\t"123"', vdf)
        self.assertNotIn("visibility", vdf)

    def test_created_id_and_write_back(self):
        self.assertEqual(workshop.created_id("Uploading content... Success.\nPublishFileID : 3456789012"), 3456789012)
        self.assertIsNone(workshop.created_id("ERROR! Not logged on."))
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            (source / "workshop.json").write_text(json.dumps(self.info(Title="卡德")), encoding="utf-8")
            workshop.save_workshop_id(source, 42)
            saved = json.loads((source / "workshop.json").read_text(encoding="utf-8"))
            self.assertEqual((saved["WorkshopId"], saved["Title"]), (42, "卡德"))

    def test_committed_listing_is_valid_and_stages_every_file(self):
        info = workshop.read_workshop()
        with tempfile.TemporaryDirectory() as temp:
            content = workshop.stage(workshop.MOD, Path(temp))
            staged = {p.relative_to(content).as_posix() for p in content.rglob("*") if p.is_file()}
        expected = {p.relative_to(workshop.MOD).as_posix() for p in workshop.mod_files(workshop.MOD)}
        self.assertEqual(staged, expected)
        self.assertIn(info["ImagePath"], staged)


if __name__ == "__main__":
    unittest.main()
