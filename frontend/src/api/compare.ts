import api from "./client";
import type { DocumentComparison, ComplianceReport } from "../types/comparison";

export async function runComparison(sessionId: string): Promise<DocumentComparison[]> {
  const { data } = await api.post(`/sessions/${sessionId}/compare`);
  return data;
}

export async function getReport(sessionId: string): Promise<ComplianceReport> {
  const { data } = await api.get(`/sessions/${sessionId}/report`);
  return data;
}
