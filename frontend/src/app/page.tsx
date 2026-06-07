"use client"

import { useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Upload, FileText, Loader2, X, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

// MVP รองรับเฉพาะงานจ้างทั่วไป แบบเต็ม (ตรงกับขอบเขตใน backend/app/prompt.py)
// ตัวเลือกอื่นโชว์เป็น roadmap แต่ยังเลือกไม่ได้ กันส่งเอกสารนอก scope ที่ทำให้ผลตรวจเพี้ยน
const PROCUREMENT_TYPES = [
  { value: "จ้างทั่วไป", label: "งานจ้างทั่วไป", supported: true },
  { value: "ซื้อ", label: "งานซื้อ", supported: false },
  { value: "เช่า", label: "งานเช่า", supported: false },
  { value: "จ้างก่อสร้าง", label: "งานจ้างก่อสร้าง", supported: false },
  { value: "จ้างที่ปรึกษา", label: "งานจ้างที่ปรึกษา", supported: false },
]

const FORMS = [
  { value: "เต็ม", label: "แบบเต็ม", supported: true },
  { value: "ย่อ", label: "แบบย่อ", supported: false },
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
        `/api/v1/check`,
        { method: "POST", body: fd }
      )
      if (!res.ok) {
        const detail = await res.json().catch(() => null)
        throw new Error(detail?.detail ?? `ส่งไฟล์ไม่สำเร็จ (${res.status})`)
      }
      const data = await res.json()

      try {
        const dataUrl = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result as string)
          reader.onerror = reject
          reader.readAsDataURL(file)
        })
        sessionStorage.setItem(`pdf_${data.check_id}`, dataUrl)
      } catch {
        // sessionStorage quota exceeded — PDF viewer won't show after refresh
      }
      sessionStorage.setItem(`filename_${data.check_id}`, file.name)

      router.push(`/check/${data.check_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "เกิดข้อผิดพลาด กรุณาลองใหม่")
      setLoading(false)
    }
  }

  const canSubmit = !!file && !loading

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50">
      <div className="w-full max-w-lg">

        {/* Wordmark */}
        <div className="mb-5 text-center">
          <h1 className="text-xl font-semibold tracking-tight text-gray-900 text-balance">
            TORDIT
          </h1>
          <p className="mt-1 text-sm text-gray-500 leading-relaxed">
            ตรวจสอบเอกสาร TOR งานจัดซื้อจัดจ้างภาครัฐ
          </p>
        </div>

        {/* Card */}
        <div
          className="bg-white rounded-xl border border-gray-200 p-6"
          style={{ boxShadow: "var(--shadow-card)" }}
        >

          {/* Drop zone */}
          <div
            role="button"
            tabIndex={0}
            aria-label={
              file
                ? `ไฟล์ที่เลือก: ${file.name} — กดเพื่อเปลี่ยน`
                : "เลือกหรือลากไฟล์ PDF มาวาง"
            }
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                inputRef.current?.click()
              }
            }}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            className={cn(
              "relative flex flex-col items-center justify-center gap-3",
              "rounded-lg border-2 border-dashed py-10 px-8 cursor-pointer outline-none",
              "transition-[border-color,background-color] duration-150",
              dragging
                ? "border-[#C23680] bg-[rgba(194,54,128,0.04)]"
                : file
                  ? "border-green-300 bg-green-50"
                  : "border-gray-200 hover:border-gray-300 hover:bg-gray-50",
              !file && !dragging && "focus-visible:border-[#C23680] focus-visible:shadow-[0_0_0_3px_rgba(194,54,128,0.15)]"
            )}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="sr-only"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) acceptFile(f)
              }}
            />

            {file ? (
              <>
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-green-100">
                  <FileText className="w-6 h-6 text-green-600" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-800 break-all max-w-[300px]">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {(file.size / 1024 / 1024).toFixed(2)} MB &middot; คลิกเพื่อเปลี่ยนไฟล์
                  </p>
                </div>
                <button
                  type="button"
                  aria-label="นำไฟล์ออก"
                  onClick={(e) => { e.stopPropagation(); setFile(null) }}
                  className="absolute top-3 right-3 p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors duration-150"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <div
                  className={cn(
                    "flex items-center justify-center w-12 h-12 rounded-full transition-colors duration-150",
                    dragging ? "bg-[rgba(194,54,128,0.1)]" : "bg-gray-100"
                  )}
                >
                  <Upload
                    className={cn(
                      "w-5 h-5 transition-colors duration-150",
                      dragging ? "text-[#C23680]" : "text-gray-400"
                    )}
                  />
                </div>
                <div className="text-center space-y-0.5">
                  <p className="text-sm font-medium text-gray-700">
                    วางไฟล์ที่นี่ หรือ{" "}
                    <span className="text-[#C23680]">คลิกเพื่อเลือก</span>
                  </p>
                  <p className="text-xs text-gray-400">PDF เท่านั้น &middot; ไม่เกิน 5 MB</p>
                </div>
              </>
            )}
          </div>

          {/* Form controls */}
          <div className="mt-5 grid grid-cols-2 gap-3">
            <div>
              <label
                htmlFor="procurement-type"
                className="block text-xs font-medium text-gray-600 mb-1.5"
              >
                ประเภทงาน
              </label>
              <select
                id="procurement-type"
                value={procurementType}
                onChange={(e) => setProcurementType(e.target.value)}
                className={cn(
                  "w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800",
                  "focus:outline-none focus:border-[#C23680] focus:shadow-[0_0_0_3px_rgba(194,54,128,0.15)]",
                  "transition-[border-color,box-shadow] duration-150"
                )}
              >
                {PROCUREMENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value} disabled={!t.supported}>
                    {t.label}{t.supported ? "" : " (เร็วๆ นี้)"}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                รูปแบบ TOR
              </label>
              <div className="flex rounded-lg border border-gray-200 bg-gray-50 p-1 gap-1">
                {FORMS.map((f) => (
                  <button
                    key={f.value}
                    type="button"
                    disabled={!f.supported}
                    title={f.supported ? undefined : "รองรับเร็วๆ นี้"}
                    onClick={() => f.supported && setForm(f.value)}
                    className={cn(
                      "flex-1 rounded-md py-1.5 text-sm font-medium transition-colors duration-150",
                      form === f.value
                        ? "bg-white text-[#C23680] shadow-sm"
                        : f.supported
                          ? "text-gray-500 hover:text-gray-700"
                          : "text-gray-300 cursor-not-allowed"
                    )}
                  >
                    {f.label}{f.supported ? "" : " · เร็วๆ นี้"}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div
              role="alert"
              className="mt-4 flex items-start gap-2 rounded-lg bg-red-50 px-3 py-2.5"
            >
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-red-500" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            aria-disabled={!canSubmit}
            className={cn(
              "mt-4 w-full flex items-center justify-center gap-2",
              "rounded-lg px-4 py-2.5 text-sm font-medium",
              "transition-colors duration-150",
              canSubmit
                ? [
                    "bg-[#C23680] text-white",
                    "hover:bg-[#A22D6B]",
                    "focus-visible:outline-none focus-visible:shadow-[0_0_0_3px_rgba(194,54,128,0.35)]",
                  ]
                : "bg-gray-100 text-gray-400 cursor-not-allowed"
            )}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>กำลังส่งไฟล์…</span>
              </>
            ) : (
              <span>เริ่มตรวจสอบ</span>
            )}
          </button>
        </div>

        {/* Footer */}
        <p className="mt-4 text-center text-xs text-gray-400">
          MVP รองรับงานจ้างทั่วไป แบบเต็ม &middot; PDF ที่เป็นข้อความเท่านั้น
        </p>
      </div>
    </div>
  )
}
