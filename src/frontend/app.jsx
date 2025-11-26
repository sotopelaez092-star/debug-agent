import { useState } from "react";
import HomePage from "./pages/HomePage.jsx";
import WorkspacePage from "./pages/WorkspacePage.jsx";

export default function App() {
  const [view, setView] = useState("home"); // 'home' | 'workspace'
  const [projectPath, setProjectPath] = useState("");
  const [fileTree, setFileTree] = useState([]);

  const handleOpenProject = () => {
    // 现在先用假数据，后面你可以接后端扫项目目录
    const mockPath = "~/projects/debug-agent";
    const mockTree = [
      {
        type: "dir",
        name: "src",
        children: [
          { type: "file", name: "main.py" },
          { type: "file", name: "docker_executor.py" },
          { type: "file", name: "debug_agent.py" },
        ],
      },
      {
        type: "dir",
        name: "tests",
        children: [
          { type: "file", name: "test_docker_executor.py" },
          { type: "file", name: "test_agent_workflow.py" },
        ],
      },
      { type: "file", name: "README.md" },
    ];

    setProjectPath(mockPath);
    setFileTree(mockTree);
    setView("workspace");
  };

  const handleBackHome = () => {
    setView("home");
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#e6edf3]">
      {view === "home" ? (
        <HomePage onOpenProject={handleOpenProject} />
      ) : (
        <WorkspacePage
          projectPath={projectPath}
          fileTree={fileTree}
          onBack={handleBackHome}
        />
      )}
    </div>
  );
}
