import { Citation } from "../api_client/types";

interface CitationPanelProps {
  citation: Citation;
  onClose: () => void;
}

export default function CitationPanel({ citation, onClose }: CitationPanelProps) {
  return (
    <div className="w-96 border-l bg-white flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="font-semibold">Citation Details</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div>
          <label className="text-xs text-gray-500 uppercase">Document</label>
          <p className="font-medium">{citation.doc_id}</p>
        </div>

        <div>
          <label className="text-xs text-gray-500 uppercase">Page</label>
          <p className="font-medium">{citation.page_number}</p>
        </div>

        <div>
          <label className="text-xs text-gray-500 uppercase">Element ID</label>
          <p className="text-sm text-gray-600">{citation.element_id}</p>
        </div>

        <div>
          <label className="text-xs text-gray-500 uppercase">Excerpt</label>
          <p className="text-sm bg-yellow-50 p-3 rounded border border-yellow-200">
            {citation.snippet}
          </p>
        </div>

        {citation.crop_uri && (
          <div>
            <label className="text-xs text-gray-500 uppercase">Visual</label>
            <img
              src={citation.crop_uri}
              alt="Citation visual"
              className="mt-2 border rounded"
            />
          </div>
        )}

        <div>
          <label className="text-xs text-gray-500 uppercase">Bounding Box</label>
          <p className="text-xs text-gray-500 font-mono">
            [{citation.bbox.map((v) => v.toFixed(1)).join(", ")}]
          </p>
        </div>
      </div>
    </div>
  );
}
