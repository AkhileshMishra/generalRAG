import { useEffect, useState } from "react";

interface Document {
  doc_id: string;
  filename: string;
  title: string;
  status: string;
  created_at: string;
  page_count?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export default function DocumentList() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/documents`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error("Failed to fetch documents:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No documents uploaded yet. Upload your first document to get started.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Title
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Pages
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Uploaded
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {documents.map((doc) => (
            <tr key={doc.doc_id}>
              <td className="px-4 py-3">
                <div>
                  <p className="font-medium">{doc.title || doc.filename}</p>
                  <p className="text-sm text-gray-500">{doc.doc_id.slice(0, 8)}...</p>
                </div>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    doc.status === "completed"
                      ? "bg-green-100 text-green-800"
                      : doc.status === "processing"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {doc.status}
                </span>
              </td>
              <td className="px-4 py-3 text-sm">{doc.page_count || "-"}</td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {new Date(doc.created_at).toLocaleDateString()}
              </td>
              <td className="px-4 py-3">
                <button className="text-blue-600 hover:text-blue-800 text-sm">
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
