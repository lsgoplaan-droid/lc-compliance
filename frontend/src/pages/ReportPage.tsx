import { useEffect } from "react";
import { useSession } from "../context/SessionContext";
import { DOCUMENT_TYPE_LABELS } from "../types/document";

import FieldComparisonTable from "../components/comparison/FieldComparisonTable";
import ReportSummaryCard from "../components/report/ReportSummaryCard";
import MatchStatusBadge from "../components/comparison/MatchStatusBadge";
import { Loader2, AlertTriangle, XCircle } from "lucide-react";

interface Props {
  onBack: () => void;
}

export default function ReportPage({ onBack }: Props) {
  const { report, loading, loadReport } = useSession();

  useEffect(() => {
    if (!report && !loading) {
      loadReport();
    }
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        <p className="mt-3 text-sm text-slate-600">Generating compliance report...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-20">
        <p className="text-slate-500">No report available. Run comparison first.</p>
      </div>
    );
  }

  const totalMatch = report.document_comparisons.reduce(
    (s, c) => s + c.summary.match_count, 0
  );
  const totalMismatch = report.document_comparisons.reduce(
    (s, c) => s + c.summary.mismatch_count, 0
  );
  const totalMissing = report.document_comparisons.reduce(
    (s, c) => s + c.summary.missing_count, 0
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-800">Compliance Report</h2>
        <span className="text-xs text-slate-400">
          Generated: {new Date(report.generated_at).toLocaleString()}
        </span>
      </div>

      {/* Overall Summary */}
      <ReportSummaryCard
        matchCount={totalMatch}
        mismatchCount={totalMismatch}
        missingCount={totalMissing}
        complianceScore={report.overall_compliance_score}
      />

      {/* Critical Discrepancies */}
      {report.critical_discrepancies.length > 0 && (
        <section>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-red-700 mb-3">
            <XCircle className="w-4 h-4" />
            Critical Discrepancies ({report.critical_discrepancies.length})
          </h3>
          <div className="space-y-2">
            {report.critical_discrepancies.map((d, i) => (
              <div
                key={i}
                className="bg-red-50 border border-red-200 rounded-lg px-4 py-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-red-800">
                    {d.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                  </span>
                  <MatchStatusBadge status={d.match_status} severity={d.severity} />
                </div>
                <div className="mt-1 text-xs text-red-600 space-y-0.5">
                  <p>LC: {d.lc_value || "-"}</p>
                  <p>Doc: {d.doc_value || "-"}</p>
                  {d.note && <p className="italic">{d.note}</p>}
                  {d.ucp_rule && <p className="font-medium">{d.ucp_rule}</p>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Warnings */}
      {report.warnings.length > 0 && (
        <section>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-yellow-700 mb-3">
            <AlertTriangle className="w-4 h-4" />
            Warnings ({report.warnings.length})
          </h3>
          <div className="space-y-2">
            {report.warnings.map((w, i) => (
              <div
                key={i}
                className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-yellow-800">
                    {w.field_name.split("_").map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(" ")}
                  </span>
                  <MatchStatusBadge status={w.match_status} severity={w.severity} />
                </div>
                <div className="mt-1 text-xs text-yellow-700">
                  {w.note && <p className="italic">{w.note}</p>}
                  {w.ucp_rule && <p className="font-medium">{w.ucp_rule}</p>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Per-document breakdown */}
      {report.document_comparisons.map((comp) => (
        <section key={comp.doc_id}>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">
            {DOCUMENT_TYPE_LABELS[comp.document_type]} - {comp.original_filename}
            <span className="ml-2 text-xs font-normal text-slate-500">
              ({comp.summary.compliance_score}% compliance)
            </span>
          </h3>
          <FieldComparisonTable comparisons={comp.field_comparisons} showAll={false} />
        </section>
      ))}

      <div className="flex justify-start pt-4">
        <button
          onClick={onBack}
          className="text-slate-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-100 transition-colors"
        >
          Back to Comparison
        </button>
      </div>
    </div>
  );
}
