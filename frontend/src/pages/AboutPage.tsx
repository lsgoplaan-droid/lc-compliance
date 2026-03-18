import { X, FileCheck, Shield, Zap, Code } from "lucide-react";

interface Props {
  onClose: () => void;
}

export default function AboutPage({ onClose }: Props) {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <FileCheck className="w-7 h-7 text-blue-600" />
            <h2 className="text-lg font-bold text-slate-900">About LC Compliance Checker</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <p className="text-sm text-slate-600 leading-relaxed">
            LC Compliance Checker automates the verification of trade documents against
            Letter of Credit (LC) terms. It extracts structured fields from bank advices
            and supporting documents, then performs field-level comparison to identify
            discrepancies per UCP 600 rules.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <Shield className="w-5 h-5 text-blue-600 mb-2" />
              <h3 className="text-sm font-semibold text-blue-900">UCP 600 Compliance</h3>
              <p className="text-xs text-blue-700 mt-1">
                Validates documents against international trade finance rules
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <Zap className="w-5 h-5 text-green-600 mb-2" />
              <h3 className="text-sm font-semibold text-green-900">Smart Extraction</h3>
              <p className="text-xs text-green-700 mt-1">
                OCR + regex-based field extraction from PDFs and text files
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <Code className="w-5 h-5 text-purple-600 mb-2" />
              <h3 className="text-sm font-semibold text-purple-900">No AI API Costs</h3>
              <p className="text-xs text-purple-700 mt-1">
                All extraction is rule-based — no external AI API calls required
              </p>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-800 mb-2">Supported Documents</h3>
            <ul className="text-sm text-slate-600 space-y-1">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                LC Bank Advice (SWIFT MT700 format, PDF or TXT)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                Commercial Invoice
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                Certificate of Origin
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                Bill of Lading
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                Packing List
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-800 mb-2">How It Works</h3>
            <ol className="text-sm text-slate-600 space-y-2">
              <li><span className="font-medium text-slate-700">1. Upload</span> — Upload your LC bank advice, then supporting trade documents (Invoice, C/O, B/L, Packing List).</li>
              <li><span className="font-medium text-slate-700">2. Review</span> — Review and correct extracted fields from each document.</li>
              <li><span className="font-medium text-slate-700">3. Compare</span> — Run field-level comparison using fuzzy matching, numeric tolerance, date parsing, and port matching.</li>
              <li><span className="font-medium text-slate-700">4. Report</span> — View a compliance report with match/mismatch/missing status, severity, and UCP 600 rule references.</li>
            </ol>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-800 mb-2">Matching Strategies</h3>
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
              <div className="bg-slate-50 rounded px-3 py-2"><span className="font-medium">Fuzzy</span> — Name/address matching with normalization</div>
              <div className="bg-slate-50 rounded px-3 py-2"><span className="font-medium">Numeric</span> — Amount/quantity with unit conversion (MT/KGS)</div>
              <div className="bg-slate-50 rounded px-3 py-2"><span className="font-medium">Date</span> — Multi-format date parsing and comparison</div>
              <div className="bg-slate-50 rounded px-3 py-2"><span className="font-medium">Contains</span> — Goods description keyword matching</div>
              <div className="bg-slate-50 rounded px-3 py-2"><span className="font-medium">Port</span> — "Any seaport of" wildcard matching</div>
              <div className="bg-slate-50 rounded px-3 py-2"><span className="font-medium">Exact</span> — LC number, HS code verification</div>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-4 space-y-1">
            <p className="text-xs text-slate-500 text-center font-medium">
              Developed by LS Gopalan
            </p>
            <p className="text-xs text-slate-400 text-center">
              Built with FastAPI, React, and OCR. No data is sent to external AI services.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
