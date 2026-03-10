import api from "./client";
import { DocumentType } from "../types/document";
import type { ExtractedDocument, UploadResponse } from "../types/document";

export async function uploadDocument(
  sessionId: string,
  file: File,
  documentType: DocumentType
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", documentType);

  const { data } = await api.post(
    `/sessions/${sessionId}/upload`,
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
