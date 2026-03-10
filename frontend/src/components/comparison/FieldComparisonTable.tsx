import { MatchStatus } from "../../types/comparison";
import type { FieldComparison } from "../../types/comparison";
import MatchStatusBadge from "./MatchStatusBadge";
import { clsx } from "clsx";

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

export default function FieldComparisonTable({ comparisons, showAll = true }: Props) {
  const filtered = showAll
    ? comparisons
    : comparisons.filter((c) => c.match_status !== MatchStatus.NOT_APPLICABLE);

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
      </table>
    </div>
  );
}
