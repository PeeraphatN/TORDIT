"use client"

import { useState } from "react"
import {
  ChevronDown,
  ChevronRight,
  AlertCircle,
  AlertTriangle,
  Quote,
  BookOpen,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { Finding } from "@/types/api"

const ERROR_CLASS_LABEL: Record<number, string> = {
  1: "โครงสร้าง/ความครบถ้วน",
  2: "ค่าขัดระเบียบ",
  3: "ความสอดคล้องภายใน",
  4: "ความสมเหตุสมผล",
}

interface FindingCardProps {
  finding: Finding
}

export default function FindingCard({ finding }: FindingCardProps) {
  const [open, setOpen] = useState(false)
  const [showLaw, setShowLaw] = useState(false)
  const isViolation = finding.severity === "ผิดระเบียบ"

  return (
    <div
      className={cn(
        "rounded-lg border text-sm overflow-hidden",
        isViolation
          ? "border-red-200 bg-red-50"
          : "border-amber-200 bg-amber-50"
      )}
    >
      {/* Header row */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-start gap-2 p-3 text-left hover:opacity-80 transition-opacity"
      >
        <span className="mt-0.5 shrink-0">
          {isViolation ? (
            <AlertCircle className="w-4 h-4 text-red-500" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          )}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={cn(
                "text-xs font-semibold px-1.5 py-0.5 rounded",
                isViolation
                  ? "bg-red-100 text-red-700"
                  : "bg-amber-100 text-amber-700"
              )}
            >
              {finding.severity}
            </span>
            <span className="text-xs text-gray-500 font-mono">{finding.rule_id}</span>
          </div>
          <p className="mt-1 text-gray-800 font-medium leading-snug line-clamp-2">
            {finding.description}
          </p>
        </div>
        <span className="shrink-0 mt-0.5 text-gray-400">
          {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </span>
      </button>

      {/* Expanded detail */}
      {open && (
        <div className="px-3 pb-3 space-y-2.5 border-t border-black/5 pt-2">
          {/* Evidence — ข้อความตรงคำจากเอกสาร ที่ระบบ verify แล้วว่ามีอยู่จริง */}
          {finding.evidence && (
            <div>
              <span className="flex items-center gap-1 text-xs font-medium text-gray-500">
                <Quote className="w-3 h-3" />
                หลักฐานในเอกสาร
                <span className="text-[10px] text-green-600 font-normal">· พบในเอกสาร ✓</span>
              </span>
              <blockquote className="mt-1 bg-white/60 border border-gray-100 rounded-md px-2 py-1.5 text-xs text-gray-700 italic leading-relaxed">
                “{finding.evidence}”
              </blockquote>
            </div>
          )}
          <div>
            <span className="text-xs font-medium text-gray-500">อ้างอิง</span>
            <p className="text-xs text-gray-700 mt-0.5">{finding.citation}</p>
            {/* ตัวบทกฎหมายจริง — กดดูได้ เพิ่มความน่าเชื่อถือ */}
            {finding.provision && (
              <>
                <button
                  onClick={() => setShowLaw((v) => !v)}
                  className="mt-1 flex items-center gap-1 text-xs text-[#C23680] hover:text-[#A22D6B] transition-colors"
                >
                  <BookOpen className="w-3 h-3" />
                  {showLaw ? "ซ่อนตัวบทกฎหมาย" : "ดูตัวบทกฎหมาย"}
                </button>
                {showLaw && (
                  <pre className="mt-1 whitespace-pre-wrap break-words rounded bg-gray-50 border border-gray-200 p-2 text-[11px] text-gray-600 leading-relaxed font-sans">
                    {finding.provision}
                  </pre>
                )}
              </>
            )}
          </div>
          <div>
            <span className="text-xs font-medium text-gray-500">คำแนะนำ</span>
            <p className="text-xs text-gray-700 mt-0.5 leading-relaxed">{finding.suggested_fix}</p>
          </div>
          <div>
            <span className="text-xs font-medium text-gray-500">ประเภทข้อผิด</span>
            <p className="text-xs text-gray-600 mt-0.5">
              {finding.error_class} — {ERROR_CLASS_LABEL[finding.error_class] ?? "ไม่ระบุ"}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
