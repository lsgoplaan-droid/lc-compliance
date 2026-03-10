import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileUp } from "lucide-react";
import { clsx } from "clsx";

interface Props {
  onFileSelected: (file: File) => void;
  label: string;
  disabled?: boolean;
}

export default function FileDropzone({ onFileSelected, label, disabled }: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) {
        onFileSelected(accepted[0]);
      }
    },
    [onFileSelected]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "text/plain": [".txt"] },
    maxFiles: 1,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
        isDragActive && "border-blue-400 bg-blue-50",
        !isDragActive && !disabled && "border-slate-300 hover:border-blue-400 hover:bg-slate-50",
        disabled && "border-slate-200 bg-slate-50 cursor-not-allowed opacity-60"
      )}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-2">
        {isDragActive ? (
          <FileUp className="w-10 h-10 text-blue-500" />
        ) : (
          <Upload className="w-10 h-10 text-slate-400" />
        )}
        <p className="text-sm font-medium text-slate-700">{label}</p>
        <p className="text-xs text-slate-500">
          {isDragActive ? "Drop the file here" : "Drag & drop a PDF or TXT file, or click to browse"}
        </p>
      </div>
    </div>
  );
}
