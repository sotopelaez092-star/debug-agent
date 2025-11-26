import { useState } from "react";

const STEPS = [
  "Load project context",
  "Analyze error",
  "Retrieve solutions (RAG)",
  "Generate patch",
  "Run in sandbox",
  "Summarize result",
];

export default function StepLogPanel() {
  const [currentStep, setCurrentStep] = useState(0);
  const [status, setStatus] = useState("idle"); // 'idle' | 'running' | 'done'

  const runDebug = () => {
    setStatus("running");
    setCurrentStep(0);

    // 简单 mock 一下依次前进
    STEPS.forEach((_, index) => {
      setTimeout(() => {
        setCurrentStep(index + 1);
        if (index === STEPS.length - 1) {
          setStatus("done");
        }
      }, 500 * (index + 1));
    });
  };

  const buttonLabel =
    status === "running" ? "Running..." : status === "done" ? "Run again" : "Run debug";

  return (
    <div className="h-full flex flex-col border-l border-white/10">
      {/* 顶部 */}
      <div className="px-4 py-3 border-b border-white/10 flex justify-between items-center">
        <div className="text-xs font-semibold text-gray-300">
          Debug timeline
        </div>
        <button
          onClick={runDebug}
          disabled={status === "running"}
          className={`
            text-xs px-3 py-1 rounded-md 
            ${
              status === "running"
                ? "bg-gray-700 text-gray-400"
                : "bg-[#238636] text-white hover:bg-[#2ea043]"
            }
          `}
        >
          {buttonLabel}
        </button>
      </div>

      {/* 步骤列表 */}
      <div className="flex-1 px-4 py-3 overflow-auto text-xs">
        {STEPS.map((label, index) => {
          const stepIndex = index + 1;
          const isDone = currentStep > stepIndex;
          const isActive = currentStep === stepIndex && status === "running";

          return (
            <div key={label} className="mb-3">
              <div className="flex items-center gap-2">
                <div
                  className={`
                    w-5 h-5 flex items-center justify-center rounded-full border text-[10px]
                    ${
                      isDone
                        ? "bg-[#238636] border-[#238636] text-white"
                        : isActive
                        ? "border-[#2f81f7] text-[#2f81f7]"
                        : "border-gray-600 text-gray-500"
                    }
                  `}
                >
                  {isDone ? "✓" : stepIndex}
                </div>
                <div
                  className={`
                    ${isDone ? "text-gray-300" : isActive ? "text-[#2f81f7]" : "text-gray-500"}
                  `}
                >
                  {label}
                </div>
              </div>
              {isActive && (
                <div className="ml-7 mt-1 text-gray-500">
                  Running…
                </div>
              )}
              {isDone && (
                <div className="ml-7 mt-1 text-gray-600">
                  ✓ Completed
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
