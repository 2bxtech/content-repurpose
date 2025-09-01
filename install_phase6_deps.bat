@echo off
REM Phase 6: File Processing Enhancement - Windows Dependency Installation Script

echo 🚀 Installing Phase 6: File Processing Enhancement Dependencies
echo ================================================================

REM Check if we're in the backend directory
if not exist "requirements.txt" (
    echo ❌ Error: Please run this script from the backend directory
    exit /b 1
)

echo 📦 Installing Python dependencies...

REM Core file processing libraries
echo Installing PDF processing libraries...
pip install PyPDF2==3.0.1
pip install pymupdf==1.23.8

echo Installing DOCX processing libraries...
pip install python-docx==1.1.0

echo Installing image processing libraries...
pip install Pillow==10.1.0

echo Installing security and validation libraries...
pip install python-magic==0.4.27
pip install python-magic-bin==0.4.14
pip install chardet==5.2.0

echo.
echo ✅ Installation complete!
echo.
echo 🧪 To test the installation:
echo   python -c "import fitz; import docx; from PIL import Image; import magic; import chardet; print('All dependencies loaded successfully!')"
echo.
echo 📝 Phase 6 Features now available:
echo   ✓ Enhanced PDF text extraction (PyPDF2 + PyMuPDF)
echo   ✓ Comprehensive DOCX processing
echo   ✓ Security validation and file scanning
echo   ✓ Document preview generation
echo   ✓ Advanced metadata extraction
echo   ✓ File deduplication with hashing
echo   ✓ Content encoding detection
echo.
echo 📋 Optional: For ClamAV virus scanning
echo   Download ClamAV from https://www.clamav.net/downloads
echo   Then: pip install clamd==1.0.2
echo.