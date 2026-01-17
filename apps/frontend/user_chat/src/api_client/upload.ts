import { UploadResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export const uploadApi = {
  async uploadUserFile(file: File, sessionId: string): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionId);

    const response = await fetch(`${API_BASE}/api/upload/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${getToken()}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }

    return response.json();
  },

  async listUserDocuments(): Promise<{ documents: UploadResponse[] }> {
    const response = await fetch(`${API_BASE}/api/upload/my-documents`, {
      headers: {
        Authorization: `Bearer ${getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to list documents: ${response.status}`);
    }

    return response.json();
  },

  async deleteDocument(docId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/upload/${docId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Delete failed: ${response.status}`);
    }
  },
};

function getToken(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("access_token") || "";
  }
  return "";
}
