import { useCallback } from 'react';
import { Upload, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface PDFUploadProps {
  onFileSelect: (file: File) => void;
  isProcessing: boolean;
}

export const PDFUpload = ({ onFileSelect, isProcessing }: PDFUploadProps) => {
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file && file.type === 'application/pdf') {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  return (
    <div
      className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:border-primary transition-colors"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      <div className="flex flex-col items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
          <Upload className="w-8 h-8 text-primary" />
        </div>
        <div>
          <h3 className="text-lg font-semibold mb-2">Upload Shuffled PDF</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Drag and drop your PDF here, or click to browse
          </p>
        </div>
        <label>
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileInput}
            className="hidden"
            disabled={isProcessing}
          />
          <Button disabled={isProcessing} asChild>
            <span className="cursor-pointer">
              <FileText className="w-4 h-4 mr-2" />
              Select PDF File
            </span>
          </Button>
        </label>
      </div>
    </div>
  );
};
