import zipfile
import pathlib
import sys
import re

def build_zip(output_path, base_dir):
    exclusions = {
        ".git", ".pytest_cache", "__pycache__", ".coverage", "htmlcov", "dist"
    }
    ext_exclusions = {".pyc", ".pyo", ".pyd", ".db", ".sqlite", ".sqlite3", ".pem", ".key"}
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in base_dir.rglob('*'):
            if path.resolve() == output_path.resolve():
                continue
                
            parts = path.relative_to(base_dir).parts
            if any(part.lower() in exclusions or part.lower() == "venv" or part.lower().startswith(".venv") or part.lower().endswith("-venv") or part.lower().endswith("_venv") for part in parts):
                continue
            if path.suffix.lower() in ext_exclusions:
                continue
            if path.name.lower().endswith(".zip") or path.name.lower().endswith(".log"):
                continue
            
            # .env files logic
            if path.name.lower() == ".env" or (path.name.lower().startswith(".env.") and not path.name.lower().endswith(".example")):
                continue

            arcname = path.relative_to(base_dir).as_posix()
            zf.write(path, arcname)
    
    print(f"Created {output_path}")

def verify_zip(output_path):
    with zipfile.ZipFile(output_path, 'r') as zf:
        namelist = zf.namelist()
        
        for name in namelist:
            if '\\' in name:
                print(f"ERROR: Backslash found in path: {name}")
                sys.exit(1)
            if name.startswith('/') or name.startswith('C:') or name.startswith('c:'):
                print(f"ERROR: Absolute path found: {name}")
                sys.exit(1)
            if '..' in name.split('/'):
                print(f"ERROR: Parent directory traversal found: {name}")
                sys.exit(1)
            
            parts = name.split('/')
            exclusions = {".git", ".pytest_cache", "__pycache__", ".coverage", "htmlcov", "dist"}
            if any(part.lower() in exclusions or part.lower() == "venv" or part.lower().startswith(".venv") or part.lower().endswith("-venv") or part.lower().endswith("_venv") for part in parts):
                print(f"ERROR: Excluded directory found in zip: {name}")
                sys.exit(1)
            
            filename = parts[-1].lower()
            if filename == ".env" or (filename.startswith(".env.") and not filename.endswith(".example")):
                print(f"ERROR: Sensitive file found in zip: {name}")
                sys.exit(1)
            
            if filename.endswith(".db") or filename.endswith(".sqlite") or filename.endswith(".sqlite3") or filename.endswith(".log") or filename.endswith(".zip") or filename.endswith(".pem") or filename.endswith(".key"):
                print(f"ERROR: Forbidden file type found in zip: {name}")
                sys.exit(1)
            
            # Read content to check for real secrets
            with zf.open(name) as f:
                try:
                    content = f.read().decode('utf-8')
                    if "BEGIN PRIVATE" + " KEY" in content or "BEGIN OPENSSH PRIVATE" + " KEY" in content:
                        print(f"ERROR: Private key content found in {name}")
                        sys.exit(1)
                    
                    lines = content.split('\n')
                    for line in lines:
                        # Skip typical python/js kwargs that are safe
                        if "password=password" in line or "password=None" in line or "password=''" in line or 'password=""' in line:
                            continue
                        
                        lower_line = line.lower().strip()
                        # Search for assignments
                        for key in ["password" + "=", "app_access_password" + "=", "oracle_pwd" + "=", "framework_test_password" + "="]:
                            if key in lower_line:
                                val = lower_line.split(key)[-1].strip()
                                # Allow if empty or obviously fake
                                if val and not any(fake in val for fake in ["fictici", "example", "my_password", "your_", "secret_pass", "oracle_pwd", "${", "request.password", "getenv", "db_credentials.password", "self.password", "contrasena"]):
                                    print(f"ERROR: Potential real secret found in {name}")
                                    sys.exit(1)
                except UnicodeDecodeError:
                    pass
                
    print(f"Verified {output_path}. It contains {len(namelist)} entries.")

if __name__ == "__main__":
    base_dir = pathlib.Path(__file__).parent.parent.resolve()
    
    # Manejar argumento --output
    output_path = None
    if "--output" in sys.argv:
        try:
            output_idx = sys.argv.index("--output")
            output_path = pathlib.Path(sys.argv[output_idx + 1]).resolve()
        except IndexError:
            print("ERROR: --output requires a path")
            sys.exit(1)
    
    if not output_path:
        output_path = base_dir / "dist" / "Fase_4_2_Limpio.zip"
    
    if output_path.exists():
        output_path.unlink()
        
    build_zip(output_path, base_dir)
    verify_zip(output_path)
