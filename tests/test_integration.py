"""Integration tests for MedSafe AI — end-to-end pipeline."""
import pytest
from utils.medicine_db import MedicineDatabase


@pytest.fixture(scope="module")
def db():
    return MedicineDatabase()


class TestDatabaseCoverage:
    """Verify the expanded database has correct content."""

    def test_database_has_minimum_medicines(self, db):
        assert len(db.medicines) >= 20, f"Expected 20+ medicines, got {len(db.medicines)}"

    def test_all_medicines_have_required_fields(self, db):
        for med in db.medicines:
            assert "name" in med, f"Missing 'name' in {med}"
            assert "active_salt" in med, f"Missing 'active_salt' in {med}"
            assert "uses" in med, f"Missing 'uses' in {med}"
            assert "interactions" in med, f"Missing 'interactions' in {med}"

    def test_all_interactions_have_required_fields(self, db):
        for med in db.medicines:
            for interaction in med.get("interactions", []):
                assert "interacting_drug_salt" in interaction
                assert "severity" in interaction
                assert "description" in interaction

    def test_severity_values_are_valid(self, db):
        valid_severities = {"High", "Moderate", "Low"}
        for med in db.medicines:
            for interaction in med.get("interactions", []):
                assert interaction["severity"] in valid_severities, (
                    f"Invalid severity '{interaction['severity']}' in {med['name']}"
                )

    def test_database_contains_key_drugs(self, db):
        drug_names = [m["name"].lower() for m in db.medicines]
        for required in ["aspirin", "warfarin", "paracetamol", "metformin"]:
            assert required in drug_names, f"'{required}' missing from database"


class TestFuzzyMatchEdgeCases:
    """Edge case coverage for the fuzzy matcher."""

    def test_case_insensitive_match(self, db):
        assert db.fuzzy_match_medicine("ASPIRIN") is not None
        assert db.fuzzy_match_medicine("aspirin") is not None
        assert db.fuzzy_match_medicine("Aspirin") is not None

    def test_dosage_string_matches_at_lower_threshold(self, db):
        # "Aspirin 100mg" scores below 80 due to extra tokens — use threshold=60
        # This reflects real-world input; the OCR view pre-cleans before matching
        result = db.fuzzy_match_medicine("Aspirin 100mg", threshold=60)
        assert result is not None
        assert result["name"] == "Aspirin"

    def test_plain_name_matches_at_default_threshold(self, db):
        result = db.fuzzy_match_medicine("Aspirin")
        assert result is not None
        assert result["name"] == "Aspirin"

    def test_empty_string_returns_none(self, db):
        assert db.fuzzy_match_medicine("") is None

    def test_none_returns_none(self, db):
        assert db.fuzzy_match_medicine(None) is None

    def test_very_low_threshold_matches_more(self, db):
        # "Asprn" at threshold=50 should match Aspirin
        result = db.fuzzy_match_medicine("Asprn", threshold=50)
        assert result is not None

    def test_new_drugs_are_findable(self, db):
        """Verify drugs added in the expanded DB are reachable."""
        assert db.fuzzy_match_medicine("Zoloft") is not None
        assert db.fuzzy_match_medicine("Cipro") is not None
        assert db.fuzzy_match_medicine("Norvasc") is not None
        assert db.fuzzy_match_medicine("Plavix") is not None


class TestInteractionDetection:
    """Full pipeline: input → fuzzy match → interaction detection."""

    def test_aspirin_warfarin_high_severity(self, db):
        aspirin = db.fuzzy_match_medicine("Aspirin")
        warfarin = db.fuzzy_match_medicine("Warfarin")
        interactions = db.check_interactions([aspirin, warfarin])
        assert len(interactions) >= 1
        high = [i for i in interactions if i["severity"] == "High"]
        assert len(high) >= 1

    def test_tramadol_sertraline_high_severity(self, db):
        """Serotonin syndrome — critical interaction."""
        tramadol = db.fuzzy_match_medicine("Ultram")
        sertraline = db.fuzzy_match_medicine("Zoloft")
        interactions = db.check_interactions([tramadol, sertraline])
        assert len(interactions) >= 1
        assert any(i["severity"] == "High" for i in interactions)

    def test_ibuprofen_prednisone_high_gi_risk(self, db):
        ibuprofen = db.fuzzy_match_medicine("Advil")
        prednisone = db.fuzzy_match_medicine("Deltasone")
        interactions = db.check_interactions([ibuprofen, prednisone])
        assert len(interactions) >= 1

    def test_three_drug_interaction_check(self, db):
        """Verify pairwise checking works for 3 drugs."""
        aspirin = db.fuzzy_match_medicine("Aspirin")
        warfarin = db.fuzzy_match_medicine("Warfarin")
        ibuprofen = db.fuzzy_match_medicine("Advil")
        interactions = db.check_interactions([aspirin, warfarin, ibuprofen])
        # Should find at least: Aspirin+Warfarin and Aspirin+Advil
        assert len(interactions) >= 2

    def test_no_duplicate_interactions(self, db):
        """Check that (A,B) and (B,A) are not both returned."""
        aspirin = db.fuzzy_match_medicine("Aspirin")
        warfarin = db.fuzzy_match_medicine("Warfarin")
        interactions = db.check_interactions([aspirin, warfarin])
        pairs = [(i["med1"], i["med2"]) for i in interactions]
        reverse_pairs = [(i["med2"], i["med1"]) for i in interactions]
        for pair in pairs:
            assert pair not in reverse_pairs, f"Duplicate interaction pair found: {pair}"

    def test_amoxicillin_lisinopril_no_interaction(self, db):
        amoxicillin = db.fuzzy_match_medicine("Amoxicillin")
        lisinopril = db.fuzzy_match_medicine("Lisinopril")
        interactions = db.check_interactions([amoxicillin, lisinopril])
        assert len(interactions) == 0

    def test_none_medicine_in_list_handled_gracefully(self, db):
        """None values in medicine list should not crash."""
        aspirin = db.fuzzy_match_medicine("Aspirin")
        interactions = db.check_interactions([aspirin, None])
        # Should not raise; None entries are skipped
        assert isinstance(interactions, list)
