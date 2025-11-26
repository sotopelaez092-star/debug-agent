export default function CodeEditor({ filePath, code, onChange }) {
  return (
    <div className="h-full flex flex-col">
      {/* 顶部文件路径 */}
      <div className="px-4 py-2 border-b border-white/10 flex items-center justify-between text-xs text-gray-400">
        <div className="font-mono">{filePath}</div>
        <div className="text-gray-500">Python</div>
      </div>

      {/* 编辑器区域 */}
      <div className="flex-1 p-3">
        <textarea
          className="
            w-full h-full bg-[#0d1117] text-[#e6edf3] 
            font-mono text-xs leading-5
            border border-white/10 rounded-md
            outline-none resize-none
            p-3
          "
          value={code}
          onChange={(e) => onChange(e.target.value)}
          spellCheck={false}
        />
      </div>
    </div>
  );
}
