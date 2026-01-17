"use client";

import { useState } from "react";
import DocumentUpload from "../components/DocumentUpload";
import DocumentList from "../components/DocumentList";

export default function AdminDashboard() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadComplete = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">
            Admin Portal - Document Management
          </h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Upload Documents</h2>
              <DocumentUpload onUploadComplete={handleUploadComplete} />
            </div>
          </div>

          {/* Document List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Knowledge Base Documents</h2>
              <DocumentList key={refreshKey} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
