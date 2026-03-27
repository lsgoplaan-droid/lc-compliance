import { useState, useEffect, useRef } from "react";
import { useSession } from "../context/SessionContext";
import { DocumentType } from "../types/document";
import { uploadDocument } from "../api/documents";
import FileDropzone from "../components/upload/FileDropzone";
import ExtractedFieldsView from "../components/documents/ExtractedFieldsView";
import api from "../api/client";
import {
  FileText,
  Loader2,
  Wand2,
  Download,
  CheckCircle,
  FileDown,
} from "lucide-react";

const DOC_OPTIONS = [
  { key: "commercial_invoice", label: "Commercial Invoice" },
  { key: "bill_of_lading", label: "Bill of Lading" },
  { key: "certificate_of_origin", label: "Certificate of Origin" },
  { key: "packing_list", label: "Packing List" },
] as const;

export default function GeneratePage() {
  const { session, documents, refreshDocuments, createSession } = useSession();
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(
    new Set(DOC_OPTIONS.map((d) => d.key))
  );
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (uploading) {
      setElapsed(0);
      timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [uploading]);

  const lcDoc = documents.find(
    (d) => d.document_type === DocumentType.LC_ADVICE
  );
  const generatedDocs = documents.filter(
    (d) => d.document_type !== DocumentType.LC_ADVICE
  );

  const toggleDoc = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === DOC_OPTIONS.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(DOC_OPTIONS.map((d) => d.key)));
    }
  };

  const handleUploadLC = async (file: File) => {
    if (!session) return;
    setUploading(true);
    setUploadError(null);
    try {
      await uploadDocument(session.session_id, file, DocumentType.LC_ADVICE);
      await refreshDocuments();
    } catch (e: any) {
      setUploadError(e.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleGenerate = async () => {
    if (!session || selected.size === 0) return;
    setGenerating(true);
    setUploadError(null);
    try {
      const docTypes = Array.from(selected);
      await api.post(`/sessions/${session.session_id}/generate`, {
        doc_types: docTypes,
      });
      await refreshDocuments();
    } catch (e: any) {
      setUploadError(e.response?.data?.detail || "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (docId: string, filename: string) => {
    if (!session) return;
    try {
      const response = await api.get(
        `/sessions/${session.session_id}/download/${docId}`,
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      setUploadError("Download failed");
    }
  };

  const handleDownloadAll = async () => {
    for (const doc of generatedDocs) {
      await handleDownload(doc.doc_id, doc.original_filename);
    }
  };

  const [viewDocId, setViewDocId] = useState<string | null>(null);
  const viewDoc = documents.find((d) => d.doc_id === viewDocId);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-lg p-5">
        <h2 className="text-lg font-semibold text-amber-900">
          Document Generator
        </h2>
        <p className="text-sm text-amber-700 mt-1">
          Upload an LC Bank Advice and generate matching supporting documents
          (Invoice, B/L, Certificate of Origin, Packing List) as PDFs.
        </p>
      </div>

      {/* Step 1: Upload LC */}
      <section>
        <h3 className="text-lg font-semibold text-slate-800 mb-3">
          Step 1: Upload LC Bank Advice
        </h3>
        {lcDoc ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-green-800">
                  {lcDoc.original_filename}
                </p>
                <p className="text-xs text-green-600">
                  {Object.values(lcDoc.fields).filter((f) => f.value).length}{" "}
                  fields extracted ({lcDoc.extraction_method})
                </p>
              </div>
            </div>
            <button
              onClick={() => createSession()}
              className="text-xs text-slate-500 hover:text-slate-700 hover:underline"
            >
              Upload different LC
            </button>
          </div>
        ) : (
          <FileDropzone
            onFileSelected={handleUploadLC}
            label="Upload LC Bank Advice (PDF or TXT)"
            disabled={uploading}
          />
        )}
      </section>

      {/* Upload status */}
      {uploading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
          <div className="flex items-center gap-2 text-blue-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm font-medium">
              Uploading and extracting fields...
            </span>
          </div>
          <p className="text-xs text-blue-500">
            Elapsed: {Math.floor(elapsed / 60)}:
            {String(elapsed % 60).padStart(2, "0")}
          </p>
        </div>
      )}

      {/* Step 2: Select & Generate */}
      {lcDoc && (
        <section>
          <h3 className="text-lg font-semibold text-slate-800 mb-3">
            Step 2: Select Documents to Generate
          </h3>
          <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selected.size === DOC_OPTIONS.length}
                onChange={toggleAll}
                className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
              />
              <span className="text-sm font-medium text-slate-700">
                Select All
              </span>
            </label>
            <div className="border-t border-slate-100" />
            <div className="grid grid-cols-2 gap-2">
              {DOC_OPTIONS.map(({ key, label }) => (
                <label
                  key={key}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selected.has(key)}
                    onChange={() => toggleDoc(key)}
                    className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
                  />
                  <span className="text-sm text-slate-700">{label}</span>
                </label>
              ))}
            </div>
            <div className="pt-2">
              <button
                onClick={handleGenerate}
                disabled={generating || selected.size === 0}
                className="flex items-center gap-2 bg-amber-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-amber-700 transition-colors disabled:opacity-50"
              >
                {generating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Wand2 className="w-4 h-4" />
                )}
                Generate {selected.size === DOC_OPTIONS.length ? "All" : selected.size} Document
                {selected.size !== 1 ? "s" : ""}
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Generated Documents */}
      {generatedDocs.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-slate-800">
              Generated Documents ({generatedDocs.length})
            </h3>
            <button
              onClick={handleDownloadAll}
              className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              <FileDown className="w-4 h-4" />
              Download All
            </button>
          </div>
          <div className="space-y-2">
            {generatedDocs.map((doc) => (
              <div
                key={doc.doc_id}
                className="flex items-center justify-between bg-white border border-slate-200 rounded-lg px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-700">
                      {doc.original_filename}
                    </p>
                    <p className="text-xs text-slate-500">
                      {Object.values(doc.fields).filter((f) => f.value).length}{" "}
                      fields extracted
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() =>
                      setViewDocId(
                        viewDocId === doc.doc_id ? null : doc.doc_id
                      )
                    }
                    className="text-xs text-slate-500 hover:text-blue-600 px-2 py-1 rounded hover:bg-slate-50"
                  >
                    {viewDocId === doc.doc_id ? "Hide" : "Preview"}
                  </button>
                  <button
                    onClick={() =>
                      handleDownload(doc.doc_id, doc.original_filename)
                    }
                    className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
                  >
                    <Download className="w-3.5 h-3.5" />
                    PDF
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Preview panel */}
          {viewDoc && (
            <div className="mt-4">
              <ExtractedFieldsView
                fields={viewDoc.fields}
                title={`Fields: ${viewDoc.original_filename}`}
              />
            </div>
          )}
        </section>
      )}

      {uploadError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {uploadError}
        </div>
      )}
    </div>
  );
}
