export type Severity = "ผิดระเบียบ" | "ควรปรับปรุง"
export type CheckStatus = "processing" | "completed" | "failed"

export interface Finding {
  error_class: number
  severity: Severity
  topic_location: string
  description: string
  rule_id: string
  citation: string
  suggested_fix: string
  evidence?: string | null   // ข้อความตรงคำจาก TOR ที่เป็นหลักฐาน (ระบบ verify แล้ว)
  provision?: string | null  // ตัวบทกฎหมายจริงของกฎข้อนี้
}

export interface CheckResult {
  check_id: string
  status: CheckStatus
  procurement_type: string | null
  form: string | null
  findings: Finding[]
  error: string | null
}
