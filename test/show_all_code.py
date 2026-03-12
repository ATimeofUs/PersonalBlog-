import os

total_lines = 0  # 统计总行数，避免覆盖内置 sum

def count_lines_in_file(filepath):
    """统计单个文件的行数"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception as e:
        print(f"无法读取文件 {filepath}: {e}")
        return 0


def find_py_and_count(now):
    global total_lines

    for entry in os.listdir(now):
        full_path = os.path.join(now, entry)  

        if os.path.isdir(full_path):
            find_py_and_count(full_path)
        elif os.path.isfile(full_path) and entry.endswith('.py'):
            lines = count_lines_in_file(full_path)
            print(f"{full_path}: {lines} 行")
            total_lines += lines

def main():
    # 指定要扫描的目录（可以多个）
    roots = ["app", "test"]
    for root in roots:
        if os.path.exists(root) and os.path.isdir(root):
            find_py_and_count(root)
        else:
            print(f"目录 {root} 不存在，跳过")

    print("总行数:", total_lines)

if __name__ == "__main__":
    main()