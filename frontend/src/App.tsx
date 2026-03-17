import { useState, useEffect } from "react";
import { SessionProvider, useSession } from "./context/SessionContext";
import Header from "./components/layout/Header";
import StepIndicator from "./components/layout/StepIndicator";
import UploadPage from "./pages/UploadPage";
import ReviewPage from "./pages/ReviewPage";
import ComparisonPage from "./pages/ComparisonPage";
import ReportPage from "./pages/ReportPage";
import AboutPage from "./pages/AboutPage";

function AppContent() {
  const { session, createSession, error, clearError, documents, comparisons } = useSession();
  const [step, setStep] = useState("upload");
  const [showAbout, setShowAbout] = useState(false);

  useEffect(() => {
    if (!session) {
      createSession();
    }
  }, []);

  const completedSteps: string[] = [];
  const lcUploaded = documents.some((d) => d.document_type === "lc_advice");
  const hasSupportingDocs = documents.filter((d) => d.document_type !== "lc_advice").length > 0;

  if (lcUploaded && hasSupportingDocs) completedSteps.push("upload");
  if (completedSteps.includes("upload")) completedSteps.push("review");
  if (comparisons.length > 0) completedSteps.push("compare");

  return (
    <div className="min-h-screen bg-slate-50">
      <Header onAboutClick={() => setShowAbout(true)} />
      {showAbout && <AboutPage onClose={() => setShowAbout(false)} />}
      <StepIndicator
        currentStep={step}
        onStepClick={setStep}
        completedSteps={completedSteps}
      />

      {error && (
        <div className="max-w-4xl mx-auto mt-4 px-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center justify-between">
            <span className="text-sm text-red-700">{error}</span>
            <button onClick={clearError} className="text-red-500 text-xs hover:underline">
              Dismiss
            </button>
          </div>
        </div>
      )}

      <main className="px-6 py-6">
        {step === "upload" && <UploadPage onComplete={() => setStep("review")} />}
        {step === "review" && (
          <ReviewPage onComplete={() => setStep("compare")} onBack={() => setStep("upload")} />
        )}
        {step === "compare" && (
          <ComparisonPage onComplete={() => setStep("report")} onBack={() => setStep("review")} />
        )}
        {step === "report" && <ReportPage onBack={() => setStep("compare")} />}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <SessionProvider>
      <AppContent />
    </SessionProvider>
  );
}
