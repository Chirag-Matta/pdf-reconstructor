import React, { useState, useEffect } from "react";
import axios from "axios";

const Index: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [originalPdfUrl, setOriginalPdfUrl] = useState<string | null>(null);
  const [reconstructedPdfUrl, setReconstructedPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (originalPdfUrl) {
        URL.revokeObjectURL(originalPdfUrl);
      }
      if (reconstructedPdfUrl) {
        URL.revokeObjectURL(reconstructedPdfUrl);
      }
    };
  }, [originalPdfUrl, reconstructedPdfUrl]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    setError(null);
    setReconstructedPdfUrl(null); // Clear previous result
    if (selectedFile) {
      setOriginalPdfUrl(URL.createObjectURL(selectedFile));
    } else {
      setOriginalPdfUrl(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a PDF file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setProgress(0);
      setError(null);
      setReconstructedPdfUrl(null);

      const response = await axios.post("http://127.0.0.1:8000/reconstruct", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        responseType: "blob",
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setProgress(percent);
          }
        },
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      setReconstructedPdfUrl(url);

    } catch (err: unknown) {
      console.error(err);
      setError("Upload failed. Please check the backend connection or file format.");
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="bg-white shadow-lg rounded-2xl p-8 max-w-md w-full text-center mx-auto">
        <h1 className="text-2xl font-bold mb-4 text-gray-800">📄 Loan Agreement Reconstructor</h1>

        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 mb-4"
        />

        {file && (
          <p className="text-sm text-gray-600 mb-3">
            Selected file: <span className="font-medium">{file.name}</span>
          </p>
        )}

        {error && (
          <p className="text-red-500 text-sm mb-3">{error}</p>
        )}

        {loading && (
          <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
            <div
              className="bg-green-500 h-3 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={loading || !file}
          className={`w-full py-2 rounded-lg text-white font-semibold transition-colors ${
            loading || !file ? "bg-gray-400 cursor-not-allowed" : "bg-green-600 hover:bg-green-700"
          }`}
        >
          {loading ? "Processing..." : "Upload & Reconstruct"}
        </button>
      </div>

      {(originalPdfUrl || reconstructedPdfUrl) && (
        <div className="mt-8 w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h2 className="text-xl font-bold mb-4 text-gray-800 text-center">Original PDF</h2>
            {originalPdfUrl ? (
              <iframe src={originalPdfUrl} className="w-full h-[80vh] border rounded-lg" title="Original PDF" />
            ) : (
               <div className="w-full h-[80vh] border rounded-lg flex items-center justify-center bg-gray-50">
                <p className="text-gray-500">No original PDF selected</p>
              </div>
            )}
          </div>
          <div>
            <h2 className="text-xl font-bold mb-4 text-gray-800 text-center">Reconstructed PDF</h2>
            {reconstructedPdfUrl ? (
              <iframe src={reconstructedPdfUrl} className="w-full h-[80vh] border rounded-lg" title="Reconstructed PDF" />
            ) : (
              <div className="w-full h-[80vh] border rounded-lg flex items-center justify-center bg-gray-50">
                <p className="text-gray-500">{loading ? "Reconstructing..." : "Reconstructed PDF will appear here"}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Index;
