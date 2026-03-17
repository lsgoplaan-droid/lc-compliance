import api from "./client";
import type { SessionResponse } from "../types/document";

export async function createSession(): Promise<SessionResponse> {
  const { data } = await api.post("/sessions");
  return data;
}

export async function listSessions(): Promise<SessionResponse[]> {
  const { data } = await api.get("/sessions");
  return data;
}

export async function getSession(sessionId: string): Promise<SessionResponse> {
  const { data } = await api.get(`/sessions/${sessionId}`);
  return data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/sessions/${sessionId}`);
}

export async function createDemoSession(): Promise<SessionResponse> {
  const { data } = await api.post("/demo");
  return data;
}
