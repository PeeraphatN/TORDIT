from app.rules import filter_findings
from app.schemas import Finding


def mk(rule_id, topic="หัวข้อ"):
    return Finding(
        error_class=1,
        severity="ผิดระเบียบ",
        topic_location=topic,
        description="d",
        rule_id=rule_id,
        citation="c",
        suggested_fix="s",
    )


def test_drops_findings_with_unknown_rule_id():
    # spec §9: rule_id ที่ไม่มีจริงใน checklist ต้องถูกทิ้ง
    out = filter_findings([mk("PENALTY-2"), mk("BOGUS-99"), mk("STRUCT-1")])
    assert [f.rule_id for f in out] == ["PENALTY-2", "STRUCT-1"]


def test_dedups_by_topic_and_rule_id():
    out = filter_findings([mk("STRUCT-1", "โครงสร้าง"), mk("STRUCT-1", "โครงสร้าง")])
    assert len(out) == 1


def test_same_rule_different_topic_is_kept():
    out = filter_findings([mk("STRUCT-1", "A"), mk("STRUCT-1", "B")])
    assert len(out) == 2


def test_preserves_input_order():
    out = filter_findings([mk("CRIT-1"), mk("PENALTY-2"), mk("STRUCT-1")])
    assert [f.rule_id for f in out] == ["CRIT-1", "PENALTY-2", "STRUCT-1"]


def test_empty_list_returns_empty():
    assert filter_findings([]) == []
