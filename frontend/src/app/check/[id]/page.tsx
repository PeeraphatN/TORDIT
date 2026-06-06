"use client"

import { use, useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react"
import FindingsPanel from "@/components/FindingsPanel"
import type { CheckResult } from "@/types/api"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
const POLL_INTERVAL_MS = 2000

interface Props {
  params: Promise<{ id: string }>
}

export default function CheckPage({ params }: Props) {
  const { id } = use(params)
  const router = useRouter()

  const [result, setResult] = useState<CheckResult | null>(null)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [filename, setFilename] = useState<string>("เอกสาร TOR")

  // Retrieve stored PDF blob URL from sessionStorage (set by upload page)
  useEffect(() => {
    const stored = sessionStorage.getItem(`pdf_${id}`)
    const name = sessionStorage.getItem(`filename_${id}`)
    if (stored) setPdfUrl(stored)
    if (name) setFilename(name)
  }, [id])

  // Poll until completed or failed
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(() => {
    let cancelled = false

    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/check/${id}`)
        if (!res.ok) throw new Error(`ไม่พบรายการตรวจ (${res.status})`)
        const data: CheckResult = await res.json()
        if (!cancelled) {
          setResult(data)
          if (data.status === "processing") {
            timerRef.current = setTimeout(poll, POLL_INTERVAL_MS)
          }
        }
      } catch (err) {
        if (!cancelled)
          setFetchError(err instanceof Error ? err.message : "เกิดข้อผิดพลาด")
      }
    }

    poll()
    return () => {
      cancelled = true
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [id])

  const isProcessing = !result || result.status === "processing"

  return (
    <div className="h-screen flex flex-col bg-white overflow-hidden">
      {/* Top bar */}
      <header className="h-12 shrink-0 flex items-center gap-3 px-4 border-b border-gray-200 bg-white">
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="hidden sm:inline">กลับ</span>
        </button>

        <div className="flex-1 flex items-center gap-2 min-w-0">
          <span className="text-sm font-medium text-gray-800 truncate">{filename}</span>
          {isProcessing && (
            <div className="flex items-center gap-1 text-xs text-blue-500">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              กำลังตรวจสอบ…
            </div>
          )}
          {result?.status === "completed" && (
            <span className="text-xs text-green-600 font-medium">ตรวจสอบเสร็จแล้ว</span>
          )}
          {result?.status === "failed" && (
            <span className="text-xs text-red-500 font-medium">ตรวจสอบล้มเหลว</span>
          )}
        </div>
      </header>

      {/* Main split layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: PDF viewer */}
        <div className="flex-1 overflow-hidden bg-gray-100 border-r border-gray-200">
          {pdfUrl ? (
            <embed
              src={pdfUrl}
              type="application/pdf"
              className="w-full h-full"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
              ไม่พบไฟล์ PDF (อาจหมดอายุหลังรีเฟรชหน้า)
            </div>
          )}
        </div>

        {/* Right: Findings panel */}
        <div className="w-96 shrink-0 flex flex-col bg-white overflow-hidden">
          {fetchError ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 p-6 text-center">
              <AlertCircle className="w-8 h-8 text-red-400" />
              <p className="text-sm text-red-600 font-medium">{fetchError}</p>
              <button
                onClick={() => router.push("/")}
                className="text-xs text-blue-600 hover:underline"
              >
                กลับไปอัปโหลดใหม่
              </button>
            </div>
          ) : result?.status === "failed" ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 p-6 text-center">
              <AlertCircle className="w-8 h-8 text-red-400" />
              <p className="text-sm text-red-600 font-medium">
                {result.error ?? "การตรวจสอบล้มเหลว"}
              </p>
            </div>
          ) : isProcessing ? (
            <div className="flex flex-col items-center justify-center h-full gap-4 p-6 text-center">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
              <div>
                <p className="text-sm font-medium text-gray-700">กำลังตรวจสอบเอกสาร…</p>
                <p className="text-xs text-gray-400 mt-1">AI กำลังวิเคราะห์ TOR อาจใช้เวลา 30–60 วินาที</p>
              </div>
            </div>
          ) : (
            <FindingsPanel
              findings={result?.findings ?? []}
              procurementType={result?.procurement_type ?? null}
              form={result?.form ?? null}
            />
          )}
        </div>
      </div>
    </div>
  )
}
