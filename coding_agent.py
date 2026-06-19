import os
import subprocess
import sys
import py_compile
import shutil
from ai import ask_ai

def read_repository(dir_path: str) -> dict:
    """Scans directory path and provides file structure details and line count statistics."""
    if not os.path.exists(dir_path):
        return {"error": "Path does not exist."}
    
    stats = {
        "files_count": 0,
        "dirs_count": 0,
        "lines_of_code": 0,
        "extensions": {},
        "structure": []
    }
    
    for root, dirs, files in os.walk(dir_path):
        # Exclude common build directories
        dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".venv", "node_modules", "dist", "build"]]
        
        rel_path = os.path.relpath(root, dir_path)
        indent = "  " * (0 if rel_path == "." else rel_path.count(os.sep) + 1)
        stats["structure"].append(f"{indent}[Dir] {os.path.basename(root) or root}")
        stats["dirs_count"] += 1
        
        for file in files:
            file_path = os.path.join(root, file)
            stats["files_count"] += 1
            ext = os.path.splitext(file)[1].lower() or "no_extension"
            stats["extensions"][ext] = stats["extensions"].get(ext, 0) + 1
            
            stats["structure"].append(f"{indent}  - {file}")
            
            # Count lines of code for text files
            if ext in [".py", ".js", ".ts", ".html", ".css", ".json", ".txt", ".md", ".sql", ".sh", ".bat", ".ps1"]:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        stats["lines_of_code"] += sum(1 for _ in f)
                except Exception:
                    pass
                    
    return stats

def generate_project(project_name: str, description: str, base_dir: str = None) -> str:
    """Generates project template files (main.py, README, .gitignore, requirements.txt)."""
    if not base_dir:
        base_dir = os.path.join(os.environ["USERPROFILE"], "Desktop")
    
    project_path = os.path.join(base_dir, project_name)
    try:
        os.makedirs(project_path, exist_ok=True)
        
        # 1. README
        readme_content = f"# {project_name}\n\n{description}\n\n## Setup\nRun commands:\n```bash\npip install -r requirements.txt\npython main.py\n```"
        with open(os.path.join(project_path, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)
            
        # 2. .gitignore
        gitignore_content = "__pycache__/\n.venv/\n*.pyc\n.env\n"
        with open(os.path.join(project_path, ".gitignore"), "w", encoding="utf-8") as f:
            f.write(gitignore_content)
            
        # 3. requirements.txt
        with open(os.path.join(project_path, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write("# Add dependencies here\n")
            
        # 4. main.py
        main_content = f'"""\n{project_name} - {description}\n"""\n\ndef main():\n    print("Welcome to {project_name}!")\n\nif __name__ == "__main__":\n    main()\n'
        with open(os.path.join(project_path, "main.py"), "w", encoding="utf-8") as f:
            f.write(main_content)
            
        return f"Project created successfully at: {project_path}"
    except Exception as e:
        return f"Failed to generate project: {e}"

def explain_file(file_path: str) -> str:
    """Reads file contents and calls OpenAI to explain the logic."""
    if not os.path.exists(file_path):
        return "File path does not exist."
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(4000)  # limit input size
        prompt = f"Explain this code code briefly and highlight its key functions:\n\n```\n{content}\n```"
        return ask_ai(prompt)
    except Exception as e:
        return f"Error explaining file: {e}"

def debug_code(file_path: str) -> str:
    """Compiles python syntax or analyzes error patterns in text files, providing AI recommendations."""
    if not os.path.exists(file_path):
        return "File path does not exist."
        
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".py":
        try:
            py_compile.compile(file_path, doraise=True)
            return "Python syntax is correct! No syntax errors detected."
        except py_compile.PyCompileError as err:
            err_msg = str(err)
            prompt = f"The following Python code file has compilation/syntax issues. Here is the traceback:\n\n{err_msg}\n\nPlease explain how to fix this error."
            return f"Syntax Error detected in file!\n\nTraceback:\n{err_msg}\n\nAI Suggestion:\n" + ask_ai(prompt)
    else:
        return "Automatic syntax validation is only supported for Python (.py) files. If you have run logs or traceback errors, read the file with screen vision agent."

def run_build_or_install(command: str, working_dir: str) -> str:
    """Installs dependencies (pip, npm) or builds binaries, reporting console log output."""
    if not os.path.exists(working_dir):
        return f"Directory path {working_dir} does not exist."
        
    try:
        proc = subprocess.run(
            command, 
            cwd=working_dir, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        output = f"Exit code: {proc.returncode}\n\nStdout:\n{proc.stdout or 'None'}\n\nStderr:\n{proc.stderr or 'None'}"
        return output
    except subprocess.TimeoutExpired:
        return "Process timed out after 60 seconds."
    except Exception as e:
        return f"Command execution failed: {e}"

def generate_readme_for_repo(dir_path: str) -> str:
    """Generates a professional README.md by scanning files."""
    stats = read_repository(dir_path)
    if "error" in stats:
        return stats["error"]
        
    structure_text = "\n".join(stats["structure"][:30]) # limit structure size
    prompt = f"Write a professional, comprehensive markdown README.md for a repository with the following file structure:\n\n```\n{structure_text}\n```\n\nInclude a brief description, installation instructions, usage guidelines, and features list."
    return ask_ai(prompt)

def generate_schema_or_api(tech: str, desc: str) -> str:
    """Generates database schemas or API boilerplate."""
    prompt = f"Write a production-ready boilerplate/schema for a project using technology stack: {tech}.\nProject details: {desc}.\nEnsure cleanly formatted code blocks."
    return ask_ai(prompt)
