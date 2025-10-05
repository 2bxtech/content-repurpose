#!/usr/bin/env python3
"""
Archive old development scripts

This script safely archives the old development setup scripts 
after confirming the new unified dev.py script is working.
"""

import shutil
from pathlib import Path
from datetime import datetime

def main():
    project_root = Path(__file__).parent
    archive_dir = project_root / "archive" / "old-dev-scripts"
    
    # Scripts to archive
    old_scripts = [
        "start-dev.sh",
        "start-dev.bat", 
        "start-celery-dev.sh",
        "start-celery-dev.bat",
        "setup_dev_environment.py",
        "quick_test.sh",
        "quick_test.bat"
    ]
    
    print("🗂️  Archiving old development scripts...")
    print("=" * 50)
    
    # Create archive directory
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archived_count = 0
    
    for script in old_scripts:
        script_path = project_root / script
        if script_path.exists():
            # Archive the script
            archive_path = archive_dir / script
            
            print(f"📦 Archiving {script}...")
            shutil.move(str(script_path), str(archive_path))
            archived_count += 1
        else:
            print(f"⚪ {script} (not found)")
    
    # Create archive info file
    info_file = archive_dir / "ARCHIVE_INFO.md"
    info_content = f"""# Archived Development Scripts

These scripts were archived on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 
after being replaced by the unified `dev.py` script.

## Archived Scripts

{chr(10).join(f'- {script}' for script in old_scripts if (project_root / script).exists())}

## Replacement

All functionality has been consolidated into `dev.py`:

```bash
# Old way
./start-dev.sh

# New way  
python dev.py start
```

See `docs/DEVELOPMENT_ENVIRONMENT.md` for complete documentation.

## Restoration

If you need to restore these scripts:

```bash
cp archive/old-dev-scripts/* .
```
"""
    
    info_file.write_text(info_content)
    
    print("=" * 50)
    print(f"✅ Archived {archived_count} old scripts to archive/old-dev-scripts/")
    print("📋 Created ARCHIVE_INFO.md with restoration instructions")
    print("")
    print("🚀 You can now use the unified development script:")
    print("   python dev.py --help")

if __name__ == "__main__":
    main()