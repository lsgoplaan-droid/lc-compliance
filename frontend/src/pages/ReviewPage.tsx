import { useState } from "react";
import { useSession } from "../context/SessionContext";
import { DOCUMENT_TYPE_LABELS } from "../types/document";
import ExtractedFieldsView from "../components/documents/ExtractedFieldsView";
import { clsx } from "clsx";

interface Props {
  onComplete: () => void;
  onBack: () => void;
}

export default function ReviewPage({ onComplete, onBack }: Props) {
  const { documents } = useSession();
  const [selectedDocId, setSelectedDocId] = useState<string | null>(
    documents[0]?.doc_id || null
  );

  const selectedDoc = documents.find((d) => d.doc_id === selectedDocId);

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex gap-6">
        {/* Document list sidebar */}
        <div className="w-64 flex-shrink-0">
          <h3 className="text-sm font-semibold text-slate-600 mb-2">Documents</h3>
          <div className="space-y-1">
            {documents.map((doc) => (
              <button
                key={doc.doc_id}
                onClick={() => setSelectedDocId(doc.doc_id)}
                className={clsx(
                  "w-full text-left px-3 py-2 rounded-lg text-sm transition-colors",
                  selectedDocId === doc.doc_id
                    ? "bg-blue-100 text-blue-800"
                    : "hover:bg-slate-100 text-slate-700"
                )}
              >
                <p className="font-medium truncate">{doc.original_filename}</p>
                <p className="text-xs text-slate-500">
                  {DOCUMENT_TYPE_LABELS[doc.document_type]}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Extracted fields view */}
        <div className="flex-1 min-w-0">
          {selectedDoc ? (
            <div>
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-slate-800">
                  {selectedDoc.original_filename}
                </h2>
                <p className="text-sm text-slate-500">
                  {DOCUMENT_TYPE_LABELS[selectedDoc.document_type]} - Extracted via{" "}
                  {selectedDoc.extraction_method}
                </p>
              </div>
              <ExtractedFieldsView fields={selectedDoc.fields} />
            </div>
          ) : (
            <div className="text-sm text-slate-500">Select a document to review</div>
          )}
        </div>
      </div>

      <div className="flex justify-between mt-8">
        <button
          onClick={onBack}
          className="text-slate-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-100 transition-colors"
        >
          Back to Upload
        </button>
        <button
          onClick={onComplete}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Run Comparison
        </button>
      </div>
    </div>
  );
}
