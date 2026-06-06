"use client"

import { AlertCircle, AlertTriangle, CheckCircle } from "lucide-react"
import FindingCard from "./FindingCard"
import type { Finding } from "@/types/api"

interface FindingsPanelProps {
  findings: Finding[]
  procurementType: string | null
  form: string | null
}

export default function FindingsPanel({ findings, procurementType, form }: FindingsPanelProps) {
  const violations = findings.filter((f) => f.severity === "ผิดระเบียบ")
  const improvements = findings.filter((f) => f.severity === "ควรปรับปรุง")

  // Group by topic_location
  const grouped = findings.reduce<Record<string, Finding[]>>((acc, f) => {
    const key = f.topic_location
    if (!acc[key]) acc[key] = []
    acc[key].push(f)
    return acc
  }, {})

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-white shrink-0">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">ผลการตรวจ</h2>
          {procurementType && (
            <span className="text-xs text-gray-400">
              {procurementType} · {form}
            </span>
          )}
        </div>

        {/* Summary badges */}
        <div className="flex items-center gap-2 mt-2">
          {findings.length === 0 ? (
            <div className="flex items-center gap-1.5 text-green-600 text-xs font-medium">
              <CheckCircle className="w-4 h-4" />
              ไม่พบข้อผิดพลาด
            </div>
          ) : (
            <>
              {violations.length > 0 && (
                <div className="flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 px-2 py-1 rounded-full">
                  <AlertCircle className="w-3.5 h-3.5" />
                  ผิดระเบียบ {violations.length} ข้อ
                </div>
              )}
              {improvements.length > 0 && (
                <div className="flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 px-2 py-1 rounded-full">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  ควรปรับปรุง {improvements.length} ข้อ
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Findings list */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {findings.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 gap-2">
            <CheckCircle className="w-10 h-10 text-green-300" />
            <p className="text-sm font-medium text-gray-500">TOR ผ่านการตรวจสอบ</p>
            <p className="text-xs">ไม่พบข้อผิดพลาดหรือข้อที่ควรปรับปรุง</p>
          </div>
        ) : (
          Object.entries(grouped).map(([topic, topicFindings]) => (
            <div key={topic}>
              <h3 className="text-xs font-semibold text-gray-700 mb-2">
                {topic}
              </h3>
              <div className="space-y-2">
                {topicFindings.map((f, i) => (
                  <FindingCard key={`${f.rule_id}-${i}`} finding={f} />
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
