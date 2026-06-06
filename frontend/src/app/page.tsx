"use client"

import { useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Upload, FileText, Loader2, X } from "lucide-react"
import { cn } from "@/lib/utils"

const PROCUREMENT_TYPES = [
  { value: "จ้างทั่วไป", label: "งานจ้างทั่วไป" },
  { value: "ซื้อ", label: "งานซื้อ" },
  { value: "เช่า", label: "งานเช่า" },
  { value: "จ้างก่อสร้าง", label: "งานจ้างก่อสร้าง" },
  { value: "จ้างที่ปรึกษา", label: "งานจ้างที่ปรึกษา" },
]

const FORMS = [
  { value: "เต็ม", label: "แบบเต็ม" },
  { value: "ย่อ", label: "แบบย่อ" },
]

export default function UploadPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [procurementType, setProcurementType] = useState("จ้างทั่วไป")
  const [form, setForm] = useState("เต็ม")
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const acceptFile = useCallback((f: File) => {
    if (f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf")) {
      setFile(f)
      setError(null)
    } else {
      setError("รองรับเฉพาะไฟล์ PDF เท่านั้น")
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const f = e.dataTransfer.files[0]
      if (f) acceptFile(f)
    },
    [acceptFile]
  )

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append("file", file)
      fd.append("procurement_type", procurementType)
      fd.append("form", form)

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/check`,
        { method: "POST", body: fd }
      )
      if (!res.ok) {
        const detail = await res.json().catch(() => null)
        throw new Error(detail?.detail ?? `ส่งไฟล์ไม่สำเร็จ (${res.status})`)
      }
      const data = await res.json()

      // Keep blob URL in sessionStorage so the report page can show the PDF
      const blobUrl = URL.createObjectURL(file)
      sessionStorage.setItem(`pdf_${data.check_id}`, blobUrl)
      sessionStorage.setItem(`filename_${data.check_id}`, file.name)

      router.push(`/check/${data.check_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "เกิดข้อผิดพลาด กรุณาลองใหม่")
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">TORDIT</h1>
          <p className="mt-1 text-sm text-gray-500">ตรวจสอบเอกสาร TOR งานจัดซื้อจัดจ้างภาครัฐ</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-5">
          {/* Drop zone */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            className={cn(
              "relative flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-10 cursor-pointer transition-colors",
              dragging
                ? "border-blue-400 bg-blue-50"
                : file
                  ? "border-green-300 bg-green-50"
                  : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            )}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="sr-only"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) acceptFile(f) }}
            />
            {file ? (
              <>
                <FileText className="w-8 h-8 text-green-500" />
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-800">{file.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setFile(null) }}
                  className="absolute top-3 right-3 p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <Upload className="w-8 h-8 text-gray-300" />
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-700">วางไฟล์ที่นี่ หรือคลิกเพื่อเลือก</p>
                  <p className="text-xs text-gray-400 mt-0.5">PDF เท่านั้น ขนาดไม่เกิน 5 MB</p>
                </div>
              </>
            )}
          </div>

          {/* Procurement type + form */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                ประเภทงาน
              </label>
              <select
                value={procurementType}
                onChange={(e) => setProcurementType(e.target.value)}
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {PROCUREMENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                รูปแบบ TOR
              </label>
              <select
                value={form}
                onChange={(e) => setForm(e.target.value)}
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {FORMS.map((f) => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            onClick={handleSubmit}
            disabled={!file || loading}
            className={cn(
              "w-full flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors",
              file && !loading
                ? "bg-blue-600 text-white hover:bg-blue-700"
                : "bg-gray-100 text-gray-400 cursor-not-allowed"
            )}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                กำลังส่งไฟล์…
              </>
            ) : (
              "เริ่มตรวจสอบ"
            )}
          </button>
        </div>

        <p className="mt-4 text-center text-xs text-gray-400">
          MVP รองรับงานจ้างทั่วไป แบบเต็ม · PDF ที่เป็นข้อความเท่านั้น
        </p>
      </div>
    </div>
  )
}
