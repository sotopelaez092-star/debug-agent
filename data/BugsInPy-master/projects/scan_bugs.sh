#!/bin/bash

echo "项目,Bug ID,修改文件数,文件列表" > bug_summary.csv

for project in */; do
    project_name=${project%/}
    
    for bug_dir in $project_name/bugs/*/; do
        if [ -f "$bug_dir/bug_patch.txt" ]; then
            bug_id=$(basename $bug_dir)
            
            # 统计修改了多少个文件
            file_count=$(grep -c "^diff --git" "$bug_dir/bug_patch.txt" 2>/dev/null || echo "0")
            
            # 提取文件列表
            files=$(grep "^diff --git" "$bug_dir/bug_patch.txt" 2>/dev/null | sed 's/diff --git a\///' | sed 's/ b\/.*//' | tr '\n' ';')
            
            echo "$project_name,$bug_id,$file_count,$files"
        fi
    done
done
