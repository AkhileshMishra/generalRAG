import { useState, useRef } from "react";

interface DocumentUploadProps {
  onUploadComplete: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export default function DocumentUpload({ onUploadComplete }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const [description, setDescription] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append("file", file);
    if (title) formData.append("title", title);
    if (tags) formData.append("tags", tags);
    if (description) formData.append("description", description);

    try {
      const response = await fetch(`${API_BASE}/api/admin/upload/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const result = await response.json();
      alert(`Document uploaded! ID: ${result.doc_id}`);

      // Reset form
      setFile(null);
      setTitle("");
      setTags("");
      setDescription("");
      if (fileInputRef.current) fileInputRef.current.value = "";

      onUploadComplete();
    } catch (error) {
      alert("Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          PDF File *
        </label>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="w-full border rounded-lg p-2"
          required
        />
        {file && (
          <p className="text-sm text-gray-500 mt-1">
            {file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)
          </p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Document title"
          className="w-full border rounded-lg p-2"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Tags (comma-separated)
        </label>
        <input
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="sop, compliance, legal"
          className="w-full border rounded-lg p-2"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief description of the document"
          rows={3}
          className="w-full border rounded-lg p-2"
        />
      </div>

      <button
        type="submit"
        disabled={!file || isUploading}
        className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {isUploading ? "Uploading..." : "Upload Document"}
      </button>

      {isUploading && (
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </form>
  );
}
