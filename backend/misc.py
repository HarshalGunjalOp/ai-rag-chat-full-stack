import os

output_file = "backend_flattened.txt"
ignore_dirs = {".git", "__pycache__", ".venv", ".pytest_cache", "test_files", "storage"}
ignore_files = {output_file}

with open(output_file, "w", encoding="utf-8") as outfile:
    for root, dirs, files in os.walk("."):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file.endswith(".py") and file not in ignore_files:
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, ".")

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    continue  # Skip unreadable files

                # Add file marker and content
                outfile.write(f"\n# path: {relpath.replace(os.sep, '/')}\n")
                outfile.write(content)
                outfile.write("\n" + "=" * 80 + "\n")  # separator between files

#
# import os
#
# # Directories and file types to ignore
# IGNORE_DIRS = {'__pycache__', '.venv', '.git', '.pytest_cache', 'storage'}
# VALID_EXTENSIONS = {'.py'}
#
# def should_ignore(path):
#     return any(part in IGNORE_DIRS for part in path.parts)
#
# def has_path_comment(lines, rel_path):
#     comment = f"# File: {rel_path.replace(os.sep, '/')}"
#     return any(comment in line for line in lines[:5])  # check top 5 lines
#
# def prepend_path_comment(file_path, rel_path):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         lines = f.readlines()
#
#     if has_path_comment(lines, rel_path):
#         return False  # Already has path
#
#     # Prepend comment
#     lines.insert(0, f"# File: {rel_path.replace(os.sep, '/')}\n")
#
#     with open(file_path, 'w', encoding='utf-8') as f:
#         f.writelines(lines)
#
#     return True
#
# def main():
#     base_dir = os.path.abspath('.')
#     updated_files = []
#
#     for root, dirs, files in os.walk(base_dir):
#         # Skip ignored directories
#         dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
#
#         for file in files:
#             if os.path.splitext(file)[1] in VALID_EXTENSIONS:
#                 abs_path = os.path.join(root, file)
#                 rel_path = os.path.relpath(abs_path, base_dir)
#                 if prepend_path_comment(abs_path, rel_path):
#                     updated_files.append(rel_path)
#
#     print("Added path comments to:")
#     for f in updated_files:
#         print(f"  - {f}")
#
# if __name__ == "__main__":
#     main()
