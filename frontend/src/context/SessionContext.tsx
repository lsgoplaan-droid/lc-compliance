import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { ExtractedDocument, SessionResponse } from "../types/document";
import type { DocumentComparison, ComplianceReport } from "../types/comparison";
import * as sessionsApi from "../api/sessions";
import * as documentsApi from "../api/documents";
import * as compareApi from "../api/compare";

interface SessionState {
  session: SessionResponse | null;
  documents: ExtractedDocument[];
  comparisons: DocumentComparison[];
  report: ComplianceReport | null;
  loading: boolean;
  error: string | null;
}

interface SessionContextType extends SessionState {
  createSession: () => Promise<void>;
  loadDemoSession: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  refreshDocuments: () => Promise<void>;
  runComparison: () => Promise<void>;
  loadReport: () => Promise<void>;
  clearError: () => void;
}

const SessionContext = createContext<SessionContextType | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({
    session: null,
    documents: [],
    comparisons: [],
    report: null,
    loading: false,
    error: null,
  });

  const setLoading = (loading: boolean) => setState((s) => ({ ...s, loading }));
  const setError = (error: string | null) => setState((s) => ({ ...s, error, loading: false }));

  const createSession = useCallback(async () => {
    setLoading(true);
    try {
      const session = await sessionsApi.createSession();
      setState((s) => ({
        ...s,
        session,
        documents: [],
        comparisons: [],
        report: null,
        loading: false,
        error: null,
      }));
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to create session");
    }
  }, []);

  const loadDemoSession = useCallback(async () => {
    setLoading(true);
    try {
      const session = await sessionsApi.createDemoSession();
      const documents = await documentsApi.listDocuments(session.session_id);
      setState((s) => ({
        ...s,
        session,
        documents,
        comparisons: [],
        report: null,
        loading: false,
        error: null,
      }));
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to load demo");
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string) => {
    setLoading(true);
    try {
      const session = await sessionsApi.getSession(sessionId);
      const documents = await documentsApi.listDocuments(sessionId);
      setState((s) => ({
        ...s,
        session,
        documents,
        comparisons: [],
        report: null,
        loading: false,
        error: null,
      }));
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to load session");
    }
  }, []);

  const refreshDocuments = useCallback(async () => {
    if (!state.session) return;
    try {
      const documents = await documentsApi.listDocuments(state.session.session_id);
      // Clear stale comparisons/report when doc list changes
      setState((s) => ({ ...s, documents, comparisons: [], report: null }));
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to refresh documents");
    }
  }, [state.session]);

  const runComparison = useCallback(async () => {
    if (!state.session) return;
    setLoading(true);
    try {
      const comparisons = await compareApi.runComparison(state.session.session_id);
      setState((s) => ({ ...s, comparisons, report: null, loading: false }));
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to run comparison");
    }
  }, [state.session]);

  const loadReport = useCallback(async () => {
    if (!state.session) return;
    setLoading(true);
    try {
      const report = await compareApi.getReport(state.session.session_id);
      setState((s) => ({ ...s, report, loading: false }));
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to load report");
    }
  }, [state.session]);

  const clearError = useCallback(() => setState((s) => ({ ...s, error: null })), []);

  return (
    <SessionContext.Provider
      value={{
        ...state,
        createSession,
        loadDemoSession,
        loadSession,
        refreshDocuments,
        runComparison,
        loadReport,
        clearError,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
