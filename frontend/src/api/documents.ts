import axios from "axios";
import api from "./client";
import { DocumentType } from "../types/document";
import type { ExtractedDocument, UploadResponse } from "../types/document";

// For uploads, call Render directly to avoid Netlify proxy timeout (~26s limit).
const DIRECT_API_URL = import.meta.env.VITE_DIRECT_API_URL || "";

export async function uploadDocument(
  sessionId: string,
  file: File,
  documentType: DocumentType
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", documentType);

  const url = `/sessions/${sessionId}/upload`;

  if (DIRECT_API_URL) {
    // Call Render backend directly (bypasses Netlify proxy timeout)
    const { data } = await axios.post(
      `${DIRECT_API_URL}${url}`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" }, timeout: 0 }
    );
    return data;
  }

  const { data } = await api.post(
    url,
    formData,
    { headers: { "Content-Type": "multipart/form-data" }, timeout: 0 }
  );
  return data;
}

export async function listDocuments(sessionId: string): Promise<ExtractedDocument[]> {
  const { data } = await api.get(`/sessions/${sessionId}/documents`);
  return data;
}

export async function updateFields(
  sessionId: string,
  docId: string,
  fields: Record<string, string>
): Promise<void> {
  await api.patch(`/sessions/${sessionId}/documents/${docId}/fields`, { fields });
}

export async function deleteDocument(sessionId: string, docId: string): Promise<void> {
  await api.delete(`/sessions/${sessionId}/documents/${docId}`);
}
