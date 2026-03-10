import { clsx } from "clsx";
import { Upload, Eye, GitCompare, FileText } from "lucide-react";

const steps = [
  { key: "upload", label: "Upload", icon: Upload },
  { key: "review", label: "Review", icon: Eye },
  { key: "compare", label: "Compare", icon: GitCompare },
  { key: "report", label: "Report", icon: FileText },
];

interface Props {
  currentStep: string;
  onStepClick: (step: string) => void;
  completedSteps: string[];
}

export default function StepIndicator({ currentStep, onStepClick, completedSteps }: Props) {
  return (
    <nav className="flex items-center gap-2 px-6 py-3 bg-white border-b border-slate-200">
      {steps.map((step, i) => {
        const Icon = step.icon;
        const isActive = currentStep === step.key;
        const isCompleted = completedSteps.includes(step.key);
        const isClickable = isCompleted || isActive;

        return (
          <div key={step.key} className="flex items-center">
            {i > 0 && <div className="w-8 h-px bg-slate-300 mx-1" />}
            <button
              onClick={() => isClickable && onStepClick(step.key)}
              disabled={!isClickable}
              className={clsx(
                "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors",
                isActive && "bg-blue-100 text-blue-700",
                isCompleted && !isActive && "bg-green-50 text-green-700 hover:bg-green-100",
                !isActive && !isCompleted && "text-slate-400 cursor-default"
              )}
            >
              <Icon className="w-4 h-4" />
              {step.label}
            </button>
          </div>
        );
      })}
    </nav>
  );
}
