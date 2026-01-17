import { useState, useRef } from "react";
import { uploadApi } from "../api_client/upload";

interface FileUploadProps {
  sessionId: string;
}

export default function FileUpload({ sessionId }: FileUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Only PDF files are supported");
      return;
    }

    if (file.size > 100 * 1024 * 1024) {
      alert("File too large. Maximum size is 100MB.");
      return;
    }

    setIsUploading(true);

    try {
      const response = await uploadApi.uploadUserFile(file, sessionId);
      setUploadedFiles((prev) => [...prev, response.filename]);
    } catch (error) {
      alert("Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="relative">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        onChange={handleFileChange}
        className="hidden"
        id="file-upload"
      />
      <label
        htmlFor="file-upload"
        className={`flex items-center justify-center w-10 h-10 rounded-lg border cursor-pointer
          ${isUploading ? "bg-gray-100" : "hover:bg-gray-50"}`}
      >
        {isUploading ? (
          <span className="animate-spin">⏳</span>
        ) : (
          <span>📎</span>
        )}
      </label>

      {uploadedFiles.length > 0 && (
        <div className="absolute bottom-12 left-0 bg-white border rounded-lg shadow-lg p-2 min-w-48">
          <p className="text-xs text-gray-500 mb-1">Uploaded files:</p>
          {uploadedFiles.map((name, idx) => (
            <p key={idx} className="text-sm truncate">
              📄 {name}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
