import { FileCheck, Info, ClipboardCheck, Wand2 } from "lucide-react";
import { clsx } from "clsx";

export type AppMode = "checker" | "generator";

interface Props {
  mode?: AppMode;
  onModeChange?: (mode: AppMode) => void;
  onAboutClick?: () => void;
}

export default function Header({ mode = "checker", onModeChange, onAboutClick }: Props) {
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
        <div className="flex items-center gap-3">
          {onModeChange && (
            <div className="flex items-center bg-slate-100 rounded-lg p-0.5">
              <button
                onClick={() => onModeChange("checker")}
                className={clsx(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  mode === "checker"
                    ? "bg-white text-blue-700 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                <ClipboardCheck className="w-4 h-4" />
                Check
              </button>
              <button
                onClick={() => onModeChange("generator")}
                className={clsx(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  mode === "generator"
                    ? "bg-white text-amber-700 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                <Wand2 className="w-4 h-4" />
                Generate
              </button>
            </div>
          )}
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
      </div>
    </header>
  );
}
