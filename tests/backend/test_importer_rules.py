import unittest
from pathlib import Path

from backend.app.importer.catalog_importer import parse_workbook


class ImporterRulesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.levels, self.services, self.observations, self.omitted = parse_workbook(
            Path("data/CatalogoServicios.xlsx"), "Servicios Externos"
        )

    def test_import_controls(self) -> None:
        self.assertEqual(len(self.levels), 12)
        self.assertEqual(len(self.services), 46)

    def test_se12_has_one_canonical_level_and_preserves_codes(self) -> None:
        se12 = [service for service in self.services if service["code"].startswith("SE.12.")]
        self.assertEqual([service["code"] for service in se12], ["SE.12.1", "SE.12.2", "SE.12.3"])
        self.assertEqual(self.levels["SE.12"]["name"], "Suministrar Analitica")
        self.assertEqual(self.levels["SE.12"]["name_variants"], ["Suministrar Analitica", "Mantener Tableros de Control"])

    def test_incomplete_final_services_are_review(self) -> None:
        final_services = [service for service in self.services if service["code"].startswith("SE.12.")]
        self.assertTrue(all(service["review_status"] == "REVIEW" for service in final_services))
        self.assertTrue(all(service["active"] is None for service in final_services))

    def test_observations_cover_conflict_and_explicit_continuation_rule(self) -> None:
        reasons = {observation.reason for observation in self.observations}
        self.assertIn("LEVEL_1_NAME_CONFLICT", reasons)
        self.assertIn("LEVEL_1_BLOCK_CONTINUATION", reasons)
        self.assertIn("OPTION_LIST", reasons)
        self.assertGreater(self.omitted, 0)


if __name__ == "__main__":
    unittest.main()
