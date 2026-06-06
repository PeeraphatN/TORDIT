from app.rules import RULES, RULE_IDS, RULES_BY_ID, Rule

# กฎ 15 ข้อ MVP ตาม spec.md §11 + NUM-1 (ตรวจทศนิยมจำนวนเงิน ตามคำขอเจ้าของงาน) = 16
EXPECTED_IDS = {
    "STRUCT-1", "STRUCT-2", "STRUCT-3",
    "QUAL-1", "QUAL-2",
    "PENALTY-1", "PENALTY-2",
    "WORK-1", "SPEC-1",
    "CRIT-1", "CRIT-2",
    "DATE-1",
    "PAY-1", "PAY-2",
    "COHERE-1",
    "NUM-1",
}


def test_registry_has_exactly_the_mvp_rules():
    assert len(RULES) == 16
    assert set(RULE_IDS) == EXPECTED_IDS


def test_every_rule_has_required_fields():
    for r in RULES:
        assert isinstance(r, Rule)
        assert r.rule_id and r.description and r.source
        assert r.check_type in {"กฎตายตัว", "วิจารณญาณ"}


def test_no_duplicate_rule_ids():
    ids = [r.rule_id for r in RULES]
    assert len(ids) == len(set(ids))


def test_lookup_by_id_matches_spec_check_type():
    # spec §11: PENALTY-2 เป็นกฎตายตัว, COHERE-1 ใช้วิจารณญาณ
    assert RULES_BY_ID["PENALTY-2"].check_type == "กฎตายตัว"
    assert RULES_BY_ID["COHERE-1"].check_type == "วิจารณญาณ"
    assert "DOES-NOT-EXIST" not in RULES_BY_ID
