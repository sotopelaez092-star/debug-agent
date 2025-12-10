import json
from pathlib import Path

bugs_to_extract = [
    # Pandas
    ("pandas", 108),
    ("pandas", 113),
    ("pandas", 114),
    ("pandas", 118),
    # FastAPI
    ("fastapi", 7),
    # Scrapy
    ("scrapy", 3),
    ("scrapy", 7),
    ("scrapy", 9),
    ("scrapy", 10),
]

def extract_bug_info(project, bug_id):
    """提取bug的关键信息"""
    base_dir = Path(f"projects/{project}/bugs/{bug_id}")
    
    # 读取patch
    patch = (base_dir / "bug_patch.txt").read_text()
    
    # 提取添加的import行
    added_imports = []
    for line in patch.split('\n'):
        if line.startswith('+') and 'import' in line and not line.startswith('+++'):
            added_imports.append(line[1:].strip())
    
    # 读取测试命令
    test_cmd = (base_dir / "run_test.sh").read_text().strip()
    
    # 提取修改的文件
    modified_files = []
    for line in patch.split('\n'):
        if line.startswith('diff --git'):
            file_path = line.split()[2].replace('a/', '')
            modified_files.append(file_path)
    
    return {
        "project": project,
        "bug_id": bug_id,
        "modified_files": modified_files,
        "added_imports": added_imports,
        "test_command": test_cmd,
        "description": f"{project} Bug {bug_id} - Missing import"
    }

# 提取所有bug
results = []
for project, bug_id in bugs_to_extract:
    try:
        bug_info = extract_bug_info(project, bug_id)
        results.append(bug_info)
        print(f"✅ Extracted {project} bug {bug_id}")
    except Exception as e:
        print(f"❌ Failed {project} bug {bug_id}: {e}")

# 保存
output_file = "bugsinpy_import_bugs.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ 提取了 {len(results)} 个bug，保存到 {output_file}")