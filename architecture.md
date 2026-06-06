# TORDIT — Architecture Diagram

## Pipeline หลัก (MVP — few-shot รอบเดียว)

```mermaid
flowchart TD
    U(["เจ้าหน้าที่พัสดุ"]) -->|นำเข้าเอกสาร| UP["อัปโหลดเอกสาร TOR<br/>(ไฟล์ PDF ที่เป็นข้อความ)"]
    UP --> SEL["ระบุประเภทและรูปแบบเอกสาร<br/>ผู้ใช้เลือกใน Dropdown<br/>เช่น งานจ้างทั่วไป แบบเต็ม"]
    SEL --> AI["ตรวจด้วย AI รอบเดียว<br/>ยิง prompt + เนื้อหา TOR → ได้ผลตรวจเลย"]

    PROMPT["System prompt + ตัวอย่าง (Few-shot)<br/>checklist กฎ + ตัวอย่างผิด/ถูก<br/>(คัดจากโฟลเดอร์ 03)"] -. ใส่ใน context .-> AI

    AI --> FILT["คัดกรองการอ้างอิงกฎ<br/>ทิ้งข้อที่อ้างกฎไม่มีอยู่จริง (เช็คในโค้ด)"]
    FILT --> REP["รายงานผลการตรวจ<br/>จัดกลุ่มตามหัวข้อ TOR<br/>ระดับความรุนแรง · การอ้างกฎ · วิธีแก้ที่แนะนำ"]
    REP --> U

    classDef ai fill:#fff3cd,stroke:#b8860b,color:#000
    classDef critical fill:#f8d7da,stroke:#c0392b,color:#000
    classDef io fill:#e7f0fd,stroke:#1f3864,color:#000
    class AI,PROMPT ai
    class FILT critical
    class UP,SEL,REP io
```

แนวทาง MVP: ตรวจด้วย AI รอบเดียวล้วน ใช้ few-shot สอนจากตัวอย่างผิด/ถูกจริง ไม่มี rule engine แยก เพื่อให้ทำเสร็จทันสาธิต · กล่อง**แดง** (คัดกรองการอ้างอิง) เป็นโค้ดสั้นๆ กันการอ้างกฎมั่วที่ทำลายความน่าเชื่อถือ · ถ้าภายหลังเช็คตัวเลขเป๊ะๆ ไม่นิ่ง ค่อยเติมการตรวจตัวเลขแบบกฎตายตัวเสริมได้

## ฝั่งข้อมูลและการวัดผล

```mermaid
flowchart LR
    C1["โฟลเดอร์ 01<br/>กฎเกณฑ์อ้างอิง"] --> CK["ชุดกฎ (checklist)<br/>ใส่ใน system prompt"]
    C3["โฟลเดอร์ 03<br/>คู่ผิด/ถูก ติดป้ายแล้ว"] --> SPLIT["แบ่งข้อมูล กันรั่ว<br/>(few-shot ห้ามซ้ำกับชุดทดสอบ)"]
    SPLIT --> FS["ตัวอย่าง few-shot<br/>ใส่ใน prompt"]
    SPLIT --> HELD[("ชุดทดสอบ held-out<br/>เฉลย ไม่เอาเข้า prompt")]
    C2["โฟลเดอร์ 02<br/>แม่แบบสะอาด"] --> INJ["ฉีดข้อผิดที่รู้คำตอบ<br/>เพิ่มเคสทดสอบ"]
    INJ --> HELD

    CK -.-> SYS["ผลการตรวจจริงจากระบบ"]
    FS -.-> SYS
    HELD --> EV["วัดผลของระบบ<br/>จับข้อผิดครบหรือไม่ และแจ้งเตือนเกินหรือไม่<br/>คุณภาพการพิจารณา (LLM-as-judge)"]
    SYS --> EV
    EV --> CI["ด่านกันคุณภาพถดถอยอัตโนมัติ"]

    classDef data fill:#e7f0fd,stroke:#1f3864,color:#000
    classDef gold fill:#fff3cd,stroke:#b8860b,color:#000
    class C1,C2,C3,CK,INJ,FS,SPLIT,SYS data
    class HELD,EV,CI gold
```

จุดสำคัญฝั่งข้อมูล: ตัวอย่างที่เอาไปใส่ few-shot **ห้ามซ้ำ** กับชุดที่ใช้วัดผล (held-out) ไม่งั้นคะแนนจะหลอกตา
