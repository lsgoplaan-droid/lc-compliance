import { FileCheck, Info } from "lucide-react";

interface Props {
  onAboutClick?: () => void;
}

export default function Header({ onAboutClick }: Props) {
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileCheck className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-xl font-bold text-slate-900">LC Compliance Checker</h1>
            <p className="text-sm text-slate-500">
              Compare trade documents against Letter of Credit terms
            </p>
          </div>
        </div>
        {onAboutClick && (
          <button
            onClick={onAboutClick}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-blue-600 transition-colors px-3 py-1.5 rounded-lg hover:bg-slate-50"
          >
            <Info className="w-4 h-4" />
            About
          </button>
        )}
      </div>
    </header>
  );
}
