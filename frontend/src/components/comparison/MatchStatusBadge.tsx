import { CheckCircle, XCircle, AlertTriangle, Minus } from "lucide-react";
import { MatchStatus, Severity } from "../../types/comparison";
import { clsx } from "clsx";

interface Props {
  status: MatchStatus;
  severity?: Severity;
}

export default function MatchStatusBadge({ status, severity }: Props) {
  switch (status) {
    case MatchStatus.MATCH:
      return (
        <span className="inline-flex items-center gap-1 text-green-600">
          <CheckCircle className="w-4 h-4" />
          <span className="text-xs font-medium">Match</span>
        </span>
      );
    case MatchStatus.MISMATCH:
      return (
        <span
          className={clsx(
            "inline-flex items-center gap-1",
            severity === Severity.CRITICAL ? "text-red-600" : "text-orange-500"
          )}
        >
          <XCircle className="w-4 h-4" />
          <span className="text-xs font-medium">Mismatch</span>
        </span>
      );
    case MatchStatus.MISSING:
      return (
        <span className="inline-flex items-center gap-1 text-yellow-600">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-xs font-medium">Missing</span>
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 text-slate-400">
          <Minus className="w-4 h-4" />
          <span className="text-xs font-medium">N/A</span>
        </span>
      );
  }
}
