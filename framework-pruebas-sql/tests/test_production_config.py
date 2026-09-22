import os
import pytest
from pathlib import Path
import tempfile
import zipfile
import sys

def test_production_files_exist():
    base = Path(__file__).parent.parent
    assert (base / "Dockerfile").exists()
    assert (base / ".dockerignore").exists()
    assert (base / "infra/production/compose.yml").exists()
    assert (base / "infra/production/README.md").exists()
    assert (base / "infra/production/.env.production.example").exists()
    assert (base / "scripts/start_production.sh").exists()
    
def test_compose_config_has_sqlite_volume():
    compose_path = Path(__file__).parent.parent / "infra/production/compose.yml"
    with open(compose_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "framework_data:/data" in content
        assert "FRAMEWORK_DB_URL=sqlite:////data/framework_interno.db" in content

def test_dockerfile_and_dockerignore():
    base = Path(__file__).parent.parent
    with open(base / "Dockerfile", "r", encoding="utf-8") as f:
        content = f.read()
        assert "FROM python:" in content
        assert "appuser" in content
    
    with open(base / ".dockerignore", "r", encoding="utf-8") as f:
        content = f.read()
        assert ".env" in content
        assert "*.db" in content

def run_verify_on_crafted_zip(namelist_with_contents):
    zipper_script = Path(__file__).parent.parent / "scripts" / "build_clean_zip.py"
    
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        output_zip = tdp / "test_output.zip"
        
        with zipfile.ZipFile(output_zip, 'w') as zf:
            for name, content in namelist_with_contents.items():
                zf.writestr(name, content)
        
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scripts.build_clean_zip import verify_zip
        
        try:
            verify_zip(output_zip)
            return True
        except SystemExit:
            return False
        except BaseException:
            return False
        finally:
            sys.path.pop(0)

def test_zipper_blocks_real_password(capsys):
    assert not run_verify_on_crafted_zip({"config.txt": "password" + "=RealSecret123"})
    assert not run_verify_on_crafted_zip({"config.txt": "APP_ACCESS_PASSWORD" + "=RealSecret123"})
    assert not run_verify_on_crafted_zip({"config.txt": "FRAMEWORK_TEST_PASSWORD" + "=RealSecret123"})
    
    # Check that it does not leak
    captured = capsys.readouterr()
    assert "RealSecret123" not in captured.out
    assert "RealSecret123" not in captured.err

def test_zipper_blocks_real_oracle_pwd():
    assert not run_verify_on_crafted_zip({"config.txt": "ORACLE_PWD" + "=MySuperSecretPassword"})

def test_zipper_blocks_private_key():
    assert not run_verify_on_crafted_zip({"key.txt": "-----BEGIN PRIVATE" + " KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQD..."})

def test_zipper_allows_fictitious_examples():
    assert run_verify_on_crafted_zip({".env.production.example": "password" + "=contraseña_ficticia\nORACLE_PWD" + "=mi_password_ficticio"})

def test_zipper_blocks_forbidden_files():
    # .env
    assert not run_verify_on_crafted_zip({".env": "test=1"})
    # .env.production
    assert not run_verify_on_crafted_zip({".env.production": "test=1"})
    # .db
    assert not run_verify_on_crafted_zip({"test.db": "sqlite"})
    # .sqlite
    assert not run_verify_on_crafted_zip({"test.sqlite": "sqlite"})
    # .log
    assert not run_verify_on_crafted_zip({"test.log": "log"})
    # venv
    assert not run_verify_on_crafted_zip({"venv/test.txt": "test"})
    # nested zip
    assert not run_verify_on_crafted_zip({"nested.zip": "PK"})

