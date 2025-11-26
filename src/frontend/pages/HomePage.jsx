export default function HomePage({ onOpenProject }) {
  const recent = [
    {
      name: "debug-agent",
      path: "~/projects/debug-agent",
    },
    {
      name: "mini-blog",
      path: "~/Desktop/mini-blog",
    },
    {
      name: "llm-playground",
      path: "~/Desktop/llm-playground",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* 顶部 Bar */}
      <div className="flex justify-between px-10 py-6 text-[18px]">
        <div className="font-semibold flex items-center gap-2">
          🐛 AI Debug Agent
        </div>
        <div className="text-sm text-gray-400">Preview Demo</div>
      </div>

      {/* 中间主内容（居中） */}
      <div className="flex-1 flex flex-col items-center mt-10">
        {/* 小副标题，保持很克制 */}
        <div className="text-center mb-10">
          <div className="text-sm text-gray-400 mb-2">
            Python Debug · LLM · Docker Sandbox
          </div>
          <div className="text-2xl font-semibold">
            Debug, with an AI co-pilot.
          </div>
        </div>

        {/* 两个主卡片按钮区域 */}
        <div className="flex gap-6 w-[650px] justify-center mb-10">
          {/* Open Project */}
          <div
            className="
              bg-[#161b22] border border-white/10 
              rounded-xl px-8 py-6 cursor-pointer
              transition hover:bg-[#1b222c] hover:border-white/20
              flex flex-col items-start w-64
            "
            onClick={onOpenProject}
          >
            <div className="text-2xl mb-2">📁</div>
            <div className="text-[17px] font-medium mb-1">Open project</div>
            <div className="text-xs text-gray-400">
              Select a local Python project to start debugging.
            </div>
          </div>

          {/* Recent Section Card（只是装饰，不是必点） */}
          <div
            className="
              bg-[#161b22] border border-white/10 
              rounded-xl px-8 py-6
              flex flex-col items-start w-64
            "
          >
            <div className="text-2xl mb-2">🕒</div>
            <div className="text-[17px] font-medium mb-1">Recent</div>
            <div className="text-xs text-gray-400">
              Quickly jump back into a recent project.
            </div>
          </div>
        </div>

        {/* Recent 列表 */}
        <div className="w-[650px] mt-4">
          <div className="text-gray-400 text-xs mb-2 uppercase tracking-wide">
            Recent projects
          </div>

          <div className="flex flex-col gap-1">
            {recent.map((item) => (
              <div
                key={item.name}
                className="
                  px-3 py-2 rounded-lg text-gray-400 text-sm 
                  hover:bg-[#1b222c] hover:text-[#e6edf3] cursor-pointer
                  flex justify-between
                "
              >
                <div>{item.name}</div>
                <div className="text-xs text-gray-500">{item.path}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
