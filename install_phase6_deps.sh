#!/bin/bash

# Phase 6: File Processing Enhancement - Dependency Installation Script
# This script installs the required libraries for enhanced file processing

echo "🚀 Installing Phase 6: File Processing Enhancement Dependencies"
echo "================================================================"

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

echo "📦 Installing Python dependencies..."

# Core file processing libraries
echo "Installing PDF processing libraries..."
pip install PyPDF2==3.0.1
pip install pymupdf==1.23.8

echo "Installing DOCX processing libraries..."
pip install python-docx==1.1.0

echo "Installing image processing libraries..."
pip install Pillow==10.1.0

echo "Installing security and validation libraries..."
# Note: python-magic requires libmagic
pip install python-magic==0.4.27
pip install chardet==5.2.0

# Optional: ClamAV for virus scanning (commented out as it requires system-level installation)
# pip install clamd==1.0.2

echo ""
echo "🔧 System-level dependencies (may require admin privileges):"
echo ""

# Check operating system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "On Linux, install libmagic:"
    echo "  Ubuntu/Debian: sudo apt-get install libmagic1"
    echo "  CentOS/RHEL: sudo yum install file-libs"
    echo "  Arch: sudo pacman -S file"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "On macOS, install libmagic:"
    echo "  With Homebrew: brew install libmagic"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "On Windows:"
    echo "  python-magic-bin is already included in requirements"
    echo "  No additional system dependencies needed"
fi

echo ""
echo "📋 Optional dependencies for enhanced features:"
echo ""
echo "For ClamAV virus scanning:"
echo "  Linux: sudo apt-get install clamav clamav-daemon"
echo "  macOS: brew install clamav"
echo "  Windows: Download ClamAV from https://www.clamav.net/downloads"
echo "  Then: pip install clamd==1.0.2"

echo ""
echo "✅ Installation complete!"
echo ""
echo "🧪 To test the installation:"
echo "  python -c \"import fitz; import docx; from PIL import Image; import magic; import chardet; print('All dependencies loaded successfully!')\""
echo ""
echo "📝 Phase 6 Features now available:"
echo "  ✓ Enhanced PDF text extraction (PyPDF2 + PyMuPDF)"
echo "  ✓ Comprehensive DOCX processing"
echo "  ✓ Security validation and file scanning"
echo "  ✓ Document preview generation"
echo "  ✓ Advanced metadata extraction"
echo "  ✓ File deduplication with hashing"
echo "  ✓ Content encoding detection"
echo ""