"""Rule registry — single source of truth ของกฎที่ระบบตรวจ.

MVP = งานจ้างทั่วไป แบบเต็ม ตรวจครบ 15 กฎตาม spec.md §11
เพิ่ม NUM-1 (ตรวจทศนิยมจำนวนเงิน) ตามคำขอเจ้าของงาน → รวมเป็น 16 กฎ
registry นี้ป้อนทั้ง checklist ใน system prompt (prompt.py) และตัวคัดกรองการอ้างอิง
(filter_findings) เพื่อให้รหัสกฎมีที่มาเดียว ไม่หลุดออกจากกัน.

ความน่าเชื่อถือ: แต่ละกฎผูก citation (การอ้างอิงทางการที่เจ้าหน้าที่เปิดหาได้จริง) และ
provision_keys (→ ตัวบทใน reference.py) ระบบ stamp ค่าพวกนี้ทับเอง (apply_references)
โมเดลจึง "แต่ง citation เองไม่ได้" — ตัด class ของการอ้างกฎมั่วทิ้งทั้งหมด.

check_type:
  "กฎตายตัว"   = ตัดสินได้ตรงไปตรงมา (เหมาะแปลงเป็นโค้ดตรวจตัวเลขทีหลังถ้าต้องการ)
  "วิจารณญาณ"  = ต้องใช้การตัดสินของโมเดลภาษา
"""

from dataclasses import dataclass

from app.reference import PROVISIONS
from app.schemas import Finding

FIXED = "กฎตายตัว"
JUDGMENT = "วิจารณญาณ"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    source: str                                  # ที่มาเชิงภายใน (ป้อน checklist ใน prompt)
    check_type: str
    citation: str = ""                           # การอ้างอิงทางการที่แสดงต่อเจ้าหน้าที่
    provision_keys: tuple[str, ...] = ()          # key → ตัวบทจริงใน reference.PROVISIONS


RULES: list[Rule] = [
    Rule("STRUCT-1", "ต้องมีหัวข้อบังคับครบข้อ 1 ถึง 9 ข้อ 10 เป็นทางเลือก", "ว 159", FIXED,
         "หนังสือเวียน ว 159 — สาระสำคัญที่ TOR แบบเต็มต้องมี (ข้อ 1–9)", ("ว159",)),
    Rule("STRUCT-2", "เลขข้อต้องต่อเนื่อง ไม่ข้าม ไม่ซ้ำ ลำดับย่อยอยู่ใต้หัวข้อที่ถูก", "ว 159 และ ข้อ R1", FIXED,
         "หนังสือเวียน ว 159 — ความครบถ้วนและลำดับเลขข้อของ TOR", ("ว159",)),
    Rule("STRUCT-3", "ความเหมาะสมของลำดับหัวข้อ", "ข้อ R1", JUDGMENT,
         "หนังสือเวียน ว 159 — ความเหมาะสมของลำดับหัวข้อ", ("ว159",)),
    Rule("QUAL-1", "คุณสมบัติผู้เสนอราคาต้องมีชุดมาตรฐานครบ", "ว 159 และตัวอย่างมาตรฐาน", FIXED,
         "หนังสือเวียน ว 159 — (3) คุณสมบัติของผู้ยื่นข้อเสนอ", ("ว159",)),
    Rule("QUAL-2", "คุณสมบัติที่ไม่เป็นสาระสำคัญให้จัดเป็นควรปรับปรุง ไม่ใช่ผิดระเบียบ", "ว 214 ข้อ 2", FIXED,
         "หนังสือเวียน ว 214 ข้อ 2 — คุณสมบัติที่ไม่เป็นสาระสำคัญ", ("ว214-2",)),
    Rule("PENALTY-1", "อัตราค่าปรับงานจ้างทั่วไปต้องอยู่ระหว่างร้อยละ 0.01 ถึง 0.20 ของราคาค่าจ้าง", "ระเบียบ 2560 และแม่แบบ", FIXED,
         "ระเบียบกระทรวงการคลังฯ พ.ศ. 2560 ข้อ 162 — อัตราค่าปรับรายวัน", ("ข้อ162",)),
    Rule("PENALTY-2", "ค่าปรับล่าช้า 'หลัก' ต้องเป็นรายวัน หากใช้รายชั่วโมงแทนถือว่าผิด (ข้อ 162) แต่ค่าปรับเสริมแบบ SLA งาน IT แบบรายชั่วโมงทำได้ (ข้อ 163) อย่า flag เพียงเพราะเป็นรายชั่วโมง", "ระเบียบ 2560 ข้อ 162/163", FIXED,
         "ระเบียบกระทรวงการคลังฯ พ.ศ. 2560 ข้อ 162 ประกอบ ข้อ 163", ("ข้อ162", "ข้อ163")),
    Rule("WORK-1", "ผลงานที่กำหนด ถ้ามี ต้องไม่เกินร้อยละ 50 ของวงเงิน", "ว 214 ข้อ 1.2.4", FIXED,
         "หนังสือเวียน ว 214 ข้อ 1 — การกำหนดผลงานไม่เกินร้อยละ 50", ("ว214-1",)),
    Rule("SPEC-1", "ห้ามระบุยี่ห้อเจาะจงหรือแหล่งผลิตเจาะจงในคุณลักษณะ", "ว 214 ข้อ 1.2", FIXED,
         "หนังสือเวียน ว 214 ข้อ 1 — ห้ามระบุยี่ห้อ/แหล่งผลิตเจาะจง", ("ว214-1",)),
    Rule("CRIT-1", "เกณฑ์พิจารณาต้องเป็นราคา หรือ ราคาประกอบเกณฑ์อื่น ตามมาตรา 65", "ว 159 และมาตรา 65", FIXED,
         "พ.ร.บ. การจัดซื้อจัดจ้างฯ พ.ศ. 2560 มาตรา 65 — หลักเกณฑ์การพิจารณาคัดเลือก", ("ม65",)),
    Rule("CRIT-2", "ความเหมาะสมของเกณฑ์เทียบกับความซับซ้อนของงาน", "ข้อ R3", JUDGMENT,
         "พ.ร.บ. การจัดซื้อจัดจ้างฯ พ.ศ. 2560 มาตรา 65 — ความเหมาะสมของเกณฑ์", ("ม65",)),
    Rule("DATE-1", "วันส่งมอบและวันครบงวดต้องอยู่ในช่วงระยะเวลาดำเนินการ", "ข้อ R7 และฉบับผิด 04A", FIXED,
         "หลักความสอดคล้องของกำหนดเวลา — วันส่งมอบ/ครบงวดต้องอยู่ในช่วงระยะเวลาดำเนินการ", ()),
    Rule("PAY-1", "งวดเงินรวมต้องเท่ากับร้อยละ 100", "ตัวอย่างมาตรฐาน", FIXED,
         "ตัวอย่างมาตรฐาน (กรมบัญชีกลาง) — งวดเงินรวมต้องเท่ากับร้อยละ 100", ()),
    Rule("PAY-2", "งวดเงินต้องสอดคล้องกับงานที่ส่งมอบจริงในแต่ละงวด", "ฉบับผิด 04A", JUDGMENT,
         "ตัวอย่างมาตรฐาน (กรมบัญชีกลาง) — งวดเงินต้องสอดคล้องกับงานที่ส่งมอบจริง", ()),
    Rule("COHERE-1", "ความเป็นมากับวัตถุประสงค์ต้องสัมพันธ์กัน และทั้งฉบับต้องสมเหตุสมผล", "ความต้องการของเจ้าของงาน", JUDGMENT,
         "ความสมเหตุสมผลของเนื้อหา TOR (ความต้องการของเจ้าของงาน)", ()),
    Rule("NUM-1", "จำนวนเงินทุกรายการต้องแสดงทศนิยมสองตำแหน่ง เช่น 1,000.00 บาท ยกเว้นจำนวนเต็มที่ลงท้าย 'บาทถ้วน'", "แม่แบบ/ตัวอย่างมาตรฐาน", FIXED,
         "ตัวอย่างมาตรฐาน (กรมบัญชีกลาง) — รูปแบบจำนวนเงินทศนิยม 2 ตำแหน่ง", ("เงินทศนิยม",)),
]

RULES_BY_ID: dict[str, Rule] = {r.rule_id: r for r in RULES}
RULE_IDS: frozenset[str] = frozenset(RULES_BY_ID)
RULE_ID_VALUES: tuple[str, ...] = tuple(r.rule_id for r in RULES)  # ลำดับคงที่ → ป้อน enum ใน schema


def filter_findings(findings: list[Finding]) -> list[Finding]:
    """คัดกรองการอ้างอิง (spec §9): hard filter ในโค้ด ไม่ใช่ prompt.

    - ทิ้งข้อค้นพบที่อ้าง rule_id ซึ่งไม่มีจริงใน registry (กันการอ้างกฎมั่ว
      ที่ทำลายความน่าเชื่อถือทั้งระบบ)
    - ตัดรายการซ้ำด้วยคู่ (topic_location, rule_id)
    - รักษาลำดับเดิมของข้อค้นพบที่ผ่าน
    """
    seen: set[tuple[str, str]] = set()
    kept: list[Finding] = []
    for f in findings:
        if f.rule_id not in RULE_IDS:
            continue
        key = (f.topic_location, f.rule_id)
        if key in seen:
            continue
        seen.add(key)
        kept.append(f)
    return kept


def _normalize(s: str) -> str:
    """ตัดช่องว่าง/ขึ้นบรรทัดทั้งหมด เพื่อเทียบ quote กับเอกสารแบบไม่สนการตัดบรรทัด."""
    return "".join(s.split())


def _provision_text(rule: Rule) -> str | None:
    """รวมตัวบทจริงของกฎจาก reference.PROVISIONS (None ถ้ากฎนั้นไม่มีตัวบทตรง)."""
    blocks = [PROVISIONS[k] for k in rule.provision_keys if k in PROVISIONS]
    return "\n\n".join(blocks) if blocks else None


def apply_references(findings: list[Finding], source_text: str) -> list[Finding]:
    """เติมการอ้างอิงที่เชื่อถือได้ + ตรวจหลักฐาน (เรียกหลัง filter_findings).

    - citation : เขียนทับด้วยค่าทางการจาก registry ตาม rule_id — โมเดลแต่ง citation เองไม่ได้
    - provision: แนบตัวบทจริงจาก reference.py ให้เจ้าหน้าที่กดดูได้ (None ถ้าไม่มีตัวบทตรง)
    - evidence : เก็บเฉพาะ quote ที่ปรากฏจริงในเอกสาร (เทียบแบบไม่สนช่องว่าง) ไม่งั้นตัดทิ้ง
                 → กัน "หลักฐานลอย" ที่โมเดลแต่งขึ้นมาเอง
    """
    norm_source = _normalize(source_text)
    out: list[Finding] = []
    for f in findings:
        rule = RULES_BY_ID.get(f.rule_id)
        if rule is None:  # ปกติผ่าน filter_findings มาแล้ว แต่กันไว้
            continue
        evidence = f.evidence
        if evidence and _normalize(evidence) not in norm_source:
            evidence = None
        out.append(
            f.model_copy(
                update={
                    "citation": rule.citation,
                    "provision": _provision_text(rule),
                    "evidence": evidence,
                }
            )
        )
    return out
