import { useState } from "react";
import { useSession } from "../context/SessionContext";
import { DocumentType, DOCUMENT_TYPE_LABELS } from "../types/document";
import { uploadDocument } from "../api/documents";
import FileDropzone from "../components/upload/FileDropzone";
import DocumentTypeSelector from "../components/upload/DocumentTypeSelector";
import ExtractedFieldsView from "../components/documents/ExtractedFieldsView";
import { FileText, Loader2 } from "lucide-react";

interface Props {
  onComplete: () => void;
}

export default function UploadPage({ onComplete }: Props) {
  const { session, documents, refreshDocuments } = useSession();
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [docType, setDocType] = useState<DocumentType>(DocumentType.COMMERCIAL_INVOICE);
  const [lastUpload, setLastUpload] = useState<any>(null);

  const lcDoc = documents.find((d) => d.document_type === DocumentType.LC_ADVICE);
  const supportingDocs = documents.filter((d) => d.document_type !== DocumentType.LC_ADVICE);

  const handleUploadLC = async (file: File) => {
    if (!session) return;
    setUploading(true);
    setUploadError(null);
    try {
      const result = await uploadDocument(session.session_id, file, DocumentType.LC_ADVICE);
      setLastUpload(result);
      await refreshDocuments();
    } catch (e: any) {
      setUploadError(e.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleUploadDoc = async (file: File) => {
    if (!session) return;
    setUploading(true);
    setUploadError(null);
    try {
      const result = await uploadDocument(session.session_id, file, docType);
      setLastUpload(result);
      await refreshDocuments();
    } catch (e: any) {
      setUploadError(e.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Step 1: LC Advice */}
      <section>
        <h2 className="text-lg font-semibold text-slate-800 mb-3">
          Step 1: Upload LC Bank Advice
        </h2>
        {lcDoc ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-green-800">
                  {lcDoc.original_filename}
                </p>
                <p className="text-xs text-green-600">
                  {Object.values(lcDoc.fields).filter((f) => f.value).length} fields extracted
                  ({lcDoc.extraction_method})
                </p>
              </div>
            </div>
          </div>
        ) : (
          <FileDropzone
            onFileSelected={handleUploadLC}
            label="Upload LC Bank Advice (PDF or TXT)"
            disabled={uploading}
          />
        )}
      </section>

      {/* Step 2: Supporting Documents */}
      <section>
        <h2 className="text-lg font-semibold text-slate-800 mb-3">
          Step 2: Upload Supporting Documents
        </h2>

        <div className="space-y-3">
          <DocumentTypeSelector
            value={docType}
            onChange={setDocType}
            excludeLC
          />

          <FileDropzone
            onFileSelected={handleUploadDoc}
            label={`Upload ${DOCUMENT_TYPE_LABELS[docType]} (PDF or TXT)`}
            disabled={uploading || !lcDoc}
          />

          {!lcDoc && (
            <p className="text-xs text-slate-500">Upload the LC advice first</p>
          )}
        </div>

        {supportingDocs.length > 0 && (
          <div className="mt-4 space-y-2">
            <h3 className="text-sm font-medium text-slate-600">
              Uploaded Documents ({supportingDocs.length})
            </h3>
            {supportingDocs.map((doc) => (
              <div
                key={doc.doc_id}
                className="flex items-center justify-between bg-white border border-slate-200 rounded-lg px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-slate-400" />
                  <div>
                    <p className="text-sm font-medium text-slate-700">
                      {doc.original_filename}
                    </p>
                    <p className="text-xs text-slate-500">
                      {DOCUMENT_TYPE_LABELS[doc.document_type]} -{" "}
                      {Object.values(doc.fields).filter((f) => f.value).length} fields
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Upload status */}
      {uploading && (
        <div className="flex items-center gap-2 text-blue-600">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm">Uploading and extracting fields...</span>
        </div>
      )}

      {uploadError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {uploadError}
        </div>
      )}

      {/* Preview last upload */}
      {lastUpload && (
        <section>
          <ExtractedFieldsView
            fields={lastUpload.fields}
            title={`Extracted from: ${lastUpload.original_filename}`}
          />
        </section>
      )}

      {/* Continue */}
      {lcDoc && supportingDocs.length > 0 && (
        <div className="flex justify-end">
          <button
            onClick={onComplete}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Continue to Review
          </button>
        </div>
      )}
    </div>
  );
}
