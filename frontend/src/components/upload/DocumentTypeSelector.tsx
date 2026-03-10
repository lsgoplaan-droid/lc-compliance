import { DocumentType, DOCUMENT_TYPE_LABELS } from "../../types/document";

interface Props {
  value: DocumentType;
  onChange: (type: DocumentType) => void;
  excludeLC?: boolean;
}

export default function DocumentTypeSelector({ value, onChange, excludeLC }: Props) {
  const types = Object.values(DocumentType).filter(
    (t) => !excludeLC || t !== DocumentType.LC_ADVICE
  );

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as DocumentType)}
      className="block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
    >
      {types.map((t) => (
        <option key={t} value={t}>
          {DOCUMENT_TYPE_LABELS[t]}
        </option>
      ))}
    </select>
  );
}
