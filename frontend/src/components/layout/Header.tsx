import { FileCheck } from "lucide-react";

export default function Header() {
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4">
      <div className="flex items-center gap-3">
        <FileCheck className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-xl font-bold text-slate-900">LC Compliance Checker</h1>
          <p className="text-sm text-slate-500">
            Compare trade documents against Letter of Credit terms
          </p>
        </div>
      </div>
    </header>
  );
}
