"""เทสต์ apply_references — stamp citation/ตัวบทจาก registry + ground evidence (rules.py)."""

from app.reference import PROVISIONS
from app.rules import RULES, RULES_BY_ID, apply_references
from app.schemas import Finding


def mk(rule_id, *, evidence=None, citation="BOGUS-CITATION", topic="หัวข้อ"):
    return Finding(
        error_class=1,
        severity="ผิดระเบียบ",
        topic_location=topic,
        description="d",
        rule_id=rule_id,
        citation=citation,
        suggested_fix="s",
        evidence=evidence,
    )


# --- registry integrity ---

def test_every_rule_has_citation():
    for r in RULES:
        assert r.citation, f"{r.rule_id} ไม่มี citation"


def test_provision_keys_all_exist_in_reference():
    for r in RULES:
        for key in r.provision_keys:
            assert key in PROVISIONS, f"{r.rule_id} อ้าง provision key '{key}' ที่ไม่มีจริง"


# --- citation stamping ---

def test_citation_overwritten_from_registry():
    # โมเดลแต่ง citation มั่ว → ต้องถูกเขียนทับด้วยค่าทางการจาก registry
    out = apply_references([mk("PENALTY-2", citation="ระเบียบ 2560 / ข้อ R2")], "")
    assert out[0].citation == RULES_BY_ID["PENALTY-2"].citation
    assert "R2" not in out[0].citation


# --- provision text ---

def test_provision_attached_for_rule_with_keys():
    out = apply_references([mk("PENALTY-2")], "")
    assert out[0].provision is not None
    assert "162" in out[0].provision and "163" in out[0].provision  # join ข้อ162 + ข้อ163


def test_provision_none_for_rule_without_keys():
    out = apply_references([mk("DATE-1")], "")  # DATE-1 ไม่มี provision_keys
    assert out[0].provision is None


# --- evidence grounding ---

_SOURCE = "หัวข้อหนึ่ง\nPenalty rate: 1,000 baht per hour\nบรรทัดสุดท้าย"


def test_evidence_kept_when_present_in_source():
    out = apply_references([mk("PENALTY-2", evidence="Penalty rate: 1,000 baht per hour")], _SOURCE)
    assert out[0].evidence == "Penalty rate: 1,000 baht per hour"


def test_evidence_dropped_when_not_in_source():
    out = apply_references([mk("PENALTY-2", evidence="ข้อความที่ไม่มีอยู่จริง")], _SOURCE)
    assert out[0].evidence is None


def test_evidence_match_is_whitespace_insensitive():
    # โมเดลยก quote ที่ตัดบรรทัด/เว้นวรรคต่างจากต้นฉบับ ต้องยัง match ได้
    out = apply_references([mk("PENALTY-2", evidence="Penalty rate:\n1,000 baht  per hour")], _SOURCE)
    assert out[0].evidence is not None


def test_unknown_rule_id_is_skipped():
    out = apply_references([mk("NOPE-99")], _SOURCE)
    assert out == []
