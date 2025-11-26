import { useState } from "react";
import FileTree from "../components/FileTree.jsx";
import CodeEditor from "../components/CodeEditor.jsx";
import StepLogPanel from "../components/StepLogPanel.jsx";

export default function WorkspacePage({ projectPath, fileTree, onBack }) {
  const [selectedFile, setSelectedFile] = useState("src/main.py");
  const [code, setCode] = useState(`# Example: buggy code
def greet(name):
    print("Hello" + name)

greet(123)
`);

  return (
    <div className="min-h-screen flex flex-col">
      {/* 顶部 Bar */}
      <div className="flex justify-between items-center px-6 py-3 border-b border-white/10 bg-[#0d1117]">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="text-xs px-2 py-1 rounded-md border border-white/10 text-gray-300 hover:bg-[#1b222c]"
          >
            ← Back
          </button>
          <div className="text-sm text-gray-400">Project</div>
          <div className="text-sm font-mono text-gray-200">{projectPath}</div>
        </div>
        <div className="text-xs text-gray-500">AI Debug Workspace</div>
      </div>

      {/* 三栏布局 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左：文件树 */}
        <div className="w-56 border-r border-white/10 bg-[#0d1117] overflow-auto">
          <FileTree
            tree={fileTree}
            selectedFile={selectedFile}
            onSelectFile={setSelectedFile}
          />
        </div>

        {/* 中：代码编辑器 */}
        <div className="flex-1 border-r border-white/10 bg-[#0d1117]">
          <CodeEditor
            filePath={selectedFile}
            code={code}
            onChange={setCode}
          />
        </div>

        {/* 右：Step Log Panel（6 步） */}
        <div className="w-80 bg-[#0d1117]">
          <StepLogPanel />
        </div>
      </div>
    </div>
  );
}
