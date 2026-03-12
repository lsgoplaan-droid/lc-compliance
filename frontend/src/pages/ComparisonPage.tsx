import { useState, useEffect } from "react";
import { useSession } from "../context/SessionContext";
import { DOCUMENT_TYPE_LABELS } from "../types/document";
import FieldComparisonTable from "../components/comparison/FieldComparisonTable";
import ReportSummaryCard from "../components/report/ReportSummaryCard";
import { Loader2 } from "lucide-react";
import { clsx } from "clsx";

interface Props {
  onComplete: () => void;
  onBack: () => void;
}

export default function ComparisonPage({ onComplete, onBack }: Props) {
  const { comparisons, loading, runComparison } = useSession();
  const [selectedIdx, setSelectedIdx] = useState(0);

  useEffect(() => {
    // Always run comparison on mount — handles new docs uploaded after previous run
    if (!loading) {
      runComparison();
    }
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        <p className="mt-3 text-sm text-slate-600">Running compliance comparison...</p>
      </div>
    );
  }

  if (comparisons.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-slate-500">No comparison results yet.</p>
        <button
          onClick={runComparison}
          className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Run Comparison
        </button>
      </div>
    );
  }

  const selected = comparisons[selectedIdx];

  // Aggregate summary across all docs
  const totalMatch = comparisons.reduce((s, c) => s + c.summary.match_count, 0);
  const totalMismatch = comparisons.reduce((s, c) => s + c.summary.mismatch_count, 0);
  const totalMissing = comparisons.reduce((s, c) => s + c.summary.missing_count, 0);
  const totalFields = totalMatch + totalMismatch + totalMissing;
  const overallScore = totalFields > 0 ? Math.round((totalMatch / totalFields) * 100) : 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h2 className="text-lg font-semibold text-slate-800">Comparison Results</h2>

      {/* Overall summary */}
      <ReportSummaryCard
        matchCount={totalMatch}
        mismatchCount={totalMismatch}
        missingCount={totalMissing}
        complianceScore={overallScore}
      />

      {/* Document tabs */}
      <div className="flex gap-2 border-b border-slate-200">
        {comparisons.map((comp, idx) => (
          <button
            key={comp.doc_id}
            onClick={() => setSelectedIdx(idx)}
            className={clsx(
              "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
              selectedIdx === idx
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            )}
          >
            {DOCUMENT_TYPE_LABELS[comp.document_type]}
            <span
              className={clsx(
                "ml-2 text-xs px-1.5 py-0.5 rounded-full",
                comp.summary.mismatch_count > 0
                  ? "bg-red-100 text-red-600"
                  : "bg-green-100 text-green-600"
              )}
            >
              {comp.summary.compliance_score}%
            </span>
          </button>
        ))}
      </div>

      {/* Selected doc comparison */}
      {selected && (
        <div>
          <p className="text-sm text-slate-500 mb-3">
            Comparing <strong>{selected.original_filename}</strong> against LC advice
          </p>
          <FieldComparisonTable comparisons={selected.field_comparisons} />
        </div>
      )}

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="text-slate-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-100 transition-colors"
        >
          Back to Review
        </button>
        <button
          onClick={onComplete}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          View Full Report
        </button>
      </div>
    </div>
  );
}
