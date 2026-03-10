import type { ExtractedField } from "../../types/document";
import { clsx } from "clsx";

interface Props {
  fields: Record<string, ExtractedField>;
  title?: string;
}

function formatFieldName(name: string): string {
  return name
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function confidenceColor(c: number): string {
  if (c >= 0.8) return "text-green-600 bg-green-50";
  if (c >= 0.5) return "text-yellow-600 bg-yellow-50";
  return "text-red-600 bg-red-50";
}

export default function ExtractedFieldsView({ fields, title }: Props) {
  const entries = Object.entries(fields).filter(([, f]) => f.value);

  if (entries.length === 0) {
    return (
      <div className="text-sm text-slate-500 italic py-4">No fields extracted</div>
    );
  }

  return (
    <div>
      {title && (
        <h3 className="text-sm font-semibold text-slate-700 mb-2">{title}</h3>
      )}
      <div className="border border-slate-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="text-left px-3 py-2 text-slate-600 font-medium">Field</th>
              <th className="text-left px-3 py-2 text-slate-600 font-medium">Value</th>
              <th className="text-center px-3 py-2 text-slate-600 font-medium w-20">Conf.</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([name, field]) => (
              <tr key={name} className="border-t border-slate-100">
                <td className="px-3 py-2 text-slate-600 whitespace-nowrap">
                  {formatFieldName(name)}
                </td>
                <td className="px-3 py-2 text-slate-900 max-w-xs truncate" title={field.value || ""}>
                  {field.value}
                </td>
                <td className="px-3 py-2 text-center">
                  <span
                    className={clsx(
                      "inline-block px-2 py-0.5 rounded text-xs font-medium",
                      confidenceColor(field.confidence)
                    )}
                  >
                    {Math.round(field.confidence * 100)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
