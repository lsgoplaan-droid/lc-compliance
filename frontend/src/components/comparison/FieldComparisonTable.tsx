import { useState } from "react";
import { MatchStatus } from "../../types/comparison";
import type { FieldComparison } from "../../types/comparison";
import MatchStatusBadge from "./MatchStatusBadge";
import { clsx } from "clsx";
import { CheckCircle, XCircle, AlertTriangle, Filter } from "lucide-react";

type StatusFilter = "all" | "match" | "mismatch" | "missing";

interface Props {
  comparisons: FieldComparison[];
  showAll?: boolean;
}

function formatFieldName(name: string): string {
  return name
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function categoryLabel(cat: string): string {
  return cat.charAt(0).toUpperCase() + cat.slice(1);
}

function countByStatus(comparisons: FieldComparison[], excludeNA: boolean) {
  const items = excludeNA
    ? comparisons.filter((c) => c.match_status !== MatchStatus.NOT_APPLICABLE)
    : comparisons;
  return {
    all: items.length,
    match: items.filter((c) => c.match_status === MatchStatus.MATCH).length,
    mismatch: items.filter((c) => c.match_status === MatchStatus.MISMATCH).length,
    missing: items.filter((c) => c.match_status === MatchStatus.MISSING).length,
  };
}

const FILTER_CONFIG: Record<StatusFilter, { label: string; icon: typeof Filter; activeClass: string; countClass: string }> = {
  all: { label: "All", icon: Filter, activeClass: "bg-slate-600 text-white", countClass: "bg-slate-100 text-slate-600" },
  match: { label: "Match", icon: CheckCircle, activeClass: "bg-green-600 text-white", countClass: "bg-green-100 text-green-700" },
  mismatch: { label: "Mismatch", icon: XCircle, activeClass: "bg-red-600 text-white", countClass: "bg-red-100 text-red-700" },
  missing: { label: "Missing", icon: AlertTriangle, activeClass: "bg-yellow-500 text-white", countClass: "bg-yellow-100 text-yellow-700" },
};

export default function FieldComparisonTable({ comparisons, showAll = true }: Props) {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  // First filter out N/A if not showAll
  const baseFiltered = showAll
    ? comparisons
    : comparisons.filter((c) => c.match_status !== MatchStatus.NOT_APPLICABLE);

  const counts = countByStatus(comparisons, !showAll);

  // Then apply status filter
  const filtered = statusFilter === "all"
    ? baseFiltered
    : baseFiltered.filter((c) => {
        if (statusFilter === "match") return c.match_status === MatchStatus.MATCH;
        if (statusFilter === "mismatch") return c.match_status === MatchStatus.MISMATCH;
        if (statusFilter === "missing") return c.match_status === MatchStatus.MISSING;
        return true;
      });

  // Group by category
  const grouped = filtered.reduce(
    (acc, c) => {
      const cat = c.field_category;
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(c);
      return acc;
    },
    {} as Record<string, FieldComparison[]>
  );

  const categoryOrder = ["core", "goods", "shipping"];

  return (
    <div className="space-y-3">
      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        {(Object.keys(FILTER_CONFIG) as StatusFilter[]).map((key) => {
          const config = FILTER_CONFIG[key];
          const Icon = config.icon;
          const count = counts[key];
          const isActive = statusFilter === key;
          if (key !== "all" && count === 0) return null;
          return (
            <button
              key={key}
              onClick={() => setStatusFilter(key)}
              className={clsx(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
                isActive ? config.activeClass : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {config.label}
              <span
                className={clsx(
                  "ml-0.5 px-1.5 py-0.5 rounded-full text-xs",
                  isActive ? "bg-white/20 text-inherit" : config.countClass
                )}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div className="border border-slate-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="text-left px-3 py-2 text-slate-600 font-medium w-36">Field</th>
              <th className="text-left px-3 py-2 text-slate-600 font-medium">LC Value</th>
              <th className="text-left px-3 py-2 text-slate-600 font-medium">Doc Value</th>
              <th className="text-center px-3 py-2 text-slate-600 font-medium w-28">Status</th>
              <th className="text-center px-3 py-2 text-slate-600 font-medium w-20">Score</th>
              <th className="text-left px-3 py-2 text-slate-600 font-medium">Notes</th>
            </tr>
          </thead>
          {categoryOrder.map((cat) => {
              const items = grouped[cat];
              if (!items) return null;
              return (
                <tbody key={cat}>
                  <tr className="bg-slate-100">
                    <td colSpan={6} className="px-3 py-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      {categoryLabel(cat)}
                    </td>
                  </tr>
                  {items.map((comp) => (
                    <tr
                      key={comp.field_name}
                      className={clsx(
                        "border-t border-slate-100",
                        comp.match_status === MatchStatus.MISMATCH && "bg-red-50/50",
                        comp.match_status === MatchStatus.MISSING && "bg-yellow-50/50"
                      )}
                    >
                      <td className="px-3 py-2 text-slate-700 font-medium whitespace-nowrap">
                        {formatFieldName(comp.field_name)}
                      </td>
                      <td className="px-3 py-2 text-slate-600 max-w-[200px] truncate" title={comp.lc_value || ""}>
                        {comp.lc_value || <span className="text-slate-400 italic">-</span>}
                      </td>
                      <td className="px-3 py-2 text-slate-600 max-w-[200px] truncate" title={comp.doc_value || ""}>
                        {comp.doc_value || <span className="text-slate-400 italic">-</span>}
                      </td>
                      <td className="px-3 py-2 text-center">
                        <MatchStatusBadge status={comp.match_status} severity={comp.severity} />
                      </td>
                      <td className="px-3 py-2 text-center text-xs text-slate-500">
                        {comp.similarity_score !== null
                          ? `${Math.round(comp.similarity_score * 100)}%`
                          : "-"}
                      </td>
                      <td className="px-3 py-2 text-xs text-slate-500 max-w-[200px] truncate" title={comp.note || ""}>
                        {comp.note || (comp.ucp_rule ? comp.ucp_rule : "-")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              );
            })}
          {filtered.length === 0 && (
            <tbody>
              <tr>
                <td colSpan={6} className="px-3 py-8 text-center text-sm text-slate-400">
                  No fields match the selected filter.
                </td>
              </tr>
            </tbody>
          )}
        </table>
      </div>
    </div>
  );
}
