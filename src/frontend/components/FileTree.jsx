function TreeNode({ node, level, selectedFile, onSelectFile }) {
  const isFile = node.type === "file";
  const paddingLeft = 12 + level * 14;

  const handleClick = () => {
    if (isFile) onSelectFile(node.path || node.name);
  };

  return (
    <div>
      <div
        className={`
          flex items-center text-xs cursor-pointer select-none
          ${isFile ? "hover:bg-[#1b222c]" : ""}
          ${
            isFile && selectedFile === (node.path || node.name)
              ? "bg-[#1b222c] text-[#e6edf3]"
              : "text-gray-400"
          }
        `}
        style={{ paddingLeft, paddingTop: 3, paddingBottom: 3 }}
        onClick={handleClick}
      >
        {!isFile ? (
          <span className="mr-1 text-gray-500">▸</span>
        ) : (
          <span className="mr-1 text-gray-700">•</span>
        )}
        <span>{node.name}</span>
      </div>
      {node.children &&
        node.children.map((child) => (
          <TreeNode
            key={child.name}
            node={child}
            level={level + 1}
            selectedFile={selectedFile}
            onSelectFile={onSelectFile}
          />
        ))}
    </div>
  );
}

export default function FileTree({ tree, selectedFile, onSelectFile }) {
  // 给每个 file 加个 path 字段（简单拼一下）
  const normalized = tree.map((n) => addPath(n, ""));

  return (
    <div className="text-xs font-mono p-2">
      <div className="text-gray-500 mb-2">EXPLORER</div>
      {normalized.map((node) => (
        <TreeNode
          key={node.path || node.name}
          node={node}
          level={0}
          selectedFile={selectedFile}
          onSelectFile={onSelectFile}
        />
      ))}
    </div>
  );
}

function addPath(node, parentPath) {
  const path = parentPath ? `${parentPath}/${node.name}` : node.name;
  const newNode = { ...node, path };
  if (node.children) {
    newNode.children = node.children.map((child) => addPath(child, path));
  }
  return newNode;
}
