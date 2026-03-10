import { clsx } from "clsx";
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react";

interface Props {
  matchCount: number;
  mismatchCount: number;
  missingCount: number;
  complianceScore: number;
}

export default function ReportSummaryCard({
  matchCount,
  mismatchCount,
  missingCount,
  complianceScore,
}: Props) {
  return (
    <div className="grid grid-cols-4 gap-4">
      <div
        className={clsx(
          "rounded-lg p-4 text-center",
          complianceScore >= 80 ? "bg-green-50" : complianceScore >= 50 ? "bg-yellow-50" : "bg-red-50"
        )}
      >
        <div
          className={clsx(
            "text-3xl font-bold",
            complianceScore >= 80 ? "text-green-600" : complianceScore >= 50 ? "text-yellow-600" : "text-red-600"
          )}
        >
          {complianceScore}%
        </div>
        <div className="text-xs text-slate-600 mt-1">Compliance Score</div>
      </div>

      <div className="rounded-lg bg-green-50 p-4 text-center">
        <div className="flex items-center justify-center gap-1">
          <CheckCircle className="w-5 h-5 text-green-500" />
          <span className="text-2xl font-bold text-green-600">{matchCount}</span>
        </div>
        <div className="text-xs text-slate-600 mt-1">Matches</div>
      </div>

      <div className="rounded-lg bg-red-50 p-4 text-center">
        <div className="flex items-center justify-center gap-1">
          <XCircle className="w-5 h-5 text-red-500" />
          <span className="text-2xl font-bold text-red-600">{mismatchCount}</span>
        </div>
        <div className="text-xs text-slate-600 mt-1">Mismatches</div>
      </div>

      <div className="rounded-lg bg-yellow-50 p-4 text-center">
        <div className="flex items-center justify-center gap-1">
          <AlertTriangle className="w-5 h-5 text-yellow-500" />
          <span className="text-2xl font-bold text-yellow-600">{missingCount}</span>
        </div>
        <div className="text-xs text-slate-600 mt-1">Missing</div>
      </div>
    </div>
  );
}
