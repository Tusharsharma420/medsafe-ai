import pytest
from utils.medicine_db import MedicineDatabase

@pytest.fixture
def db():
    return MedicineDatabase()

def test_exact_match(db):
    """Test matching when name matches exactly."""
    match = db.fuzzy_match_medicine("Aspirin")
    assert match is not None
    assert match["name"] == "Aspirin"

def test_fuzzy_match_brand(db):
    """Test matching with brand spelling mistakes/variations."""
    # "Asprn" should match "Aspirin"
    match = db.fuzzy_match_medicine("Asprn")
    assert match is not None
    assert match["name"] == "Aspirin"

def test_fuzzy_match_salt(db):
    """Test matching by active salt with variations."""
    # "Acetaminophen" active salt for "Paracetamol"
    match = db.fuzzy_match_medicine("Acetaminopn")
    assert match is not None
    assert match["name"] == "Paracetamol"

def test_no_match(db):
    """Test behavior when no match is found below threshold."""
    match = db.fuzzy_match_medicine("UnknownMedThatDoesNotExist")
    assert match is None

def test_check_interactions_found(db):
    """Test interaction check works for dangerous combinations."""
    aspirin = db.fuzzy_match_medicine("Aspirin")
    warfarin = db.fuzzy_match_medicine("Warfarin")
    
    assert aspirin is not None
    assert warfarin is not None
    
    interactions = db.check_interactions([aspirin, warfarin])
    assert len(interactions) > 0
    assert any(
        (i["med1"] == "Aspirin" and i["med2"] == "Warfarin") or
        (i["med1"] == "Warfarin" and i["med2"] == "Aspirin")
        for i in interactions
    )

def test_check_interactions_none(db):
    """Test interaction check works for safe combinations."""
    amoxicillin = db.fuzzy_match_medicine("Amoxicillin")
    paracetamol = db.fuzzy_match_medicine("Paracetamol")
    
    assert amoxicillin is not None
    assert paracetamol is not None
    
    interactions = db.check_interactions([amoxicillin, paracetamol])
    assert len(interactions) == 0
