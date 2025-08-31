import PyPDF2
import docx
import aiofiles
from typing import Dict, Any
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class FileProcessor:
    """Real content extraction from PDF/DOCX files"""
    
    async def process_file(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """Process uploaded file and extract content"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Route to appropriate processor based on content type
            if content_type == "application/pdf":
                return await self._process_pdf(file_path)
            elif "wordprocessingml" in content_type or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return await self._process_docx(file_path)
            elif content_type.startswith("text/"):
                return await self._process_text(file_path)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return {
                "content": "",
                "metadata": {"error": str(e)},
                "word_count": 0,
                "extraction_method": "error"
            }
    
    async def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract content from PDF"""
        content = ""
        metadata = {}
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract metadata
                if pdf_reader.metadata:
                    metadata.update({
                        "title": pdf_reader.metadata.get("/Title", ""),
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "subject": pdf_reader.metadata.get("/Subject", ""),
                        "creator": pdf_reader.metadata.get("/Creator", ""),
                        "pages": len(pdf_reader.pages)
                    })
                else:
                    metadata["pages"] = len(pdf_reader.pages)
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            content += f"\\n\\n--- Page {page_num + 1} ---\\n"
                            content += page_text
                    except Exception as page_error:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {str(page_error)}")
                        continue
        
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            metadata["error"] = str(e)
        
        return {
            "content": content.strip(),
            "metadata": metadata,
            "word_count": len(content.split()) if content else 0,
            "extraction_method": "PyPDF2"
        }
    
    async def _process_docx(self, file_path: str) -> Dict[str, Any]:
        """Extract content from DOCX"""
        try:
            doc = docx.Document(file_path)
            
            # Extract text content
            content = "\\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            
            # Extract metadata
            props = doc.core_properties
            metadata = {
                "title": props.title or "",
                "author": props.author or "",
                "subject": props.subject or "",
                "keywords": props.keywords or "",
                "paragraphs": len(doc.paragraphs),
                "tables": len(doc.tables)
            }
            
            # Add creation and modified dates if available
            if props.created:
                metadata["created"] = props.created.isoformat()
            if props.modified:
                metadata["modified"] = props.modified.isoformat()
        
        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {str(e)}")
            content = ""
            metadata = {"error": str(e)}
        
        return {
            "content": content.strip(),
            "metadata": metadata,
            "word_count": len(content.split()) if content else 0,
            "extraction_method": "python-docx"
        }
    
    async def _process_text(self, file_path: str) -> Dict[str, Any]:
        """Process plain text files"""
        try:
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
                content = await file.read()
            
            # Get file stats
            file_stat = os.stat(file_path)
            metadata = {
                "file_size": file_stat.st_size,
                "lines": len(content.split('\\n')) if content else 0,
                "encoding": "utf-8"
            }
        
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                async with aiofiles.open(file_path, mode='r', encoding='latin-1') as file:
                    content = await file.read()
                metadata = {"encoding": "latin-1"}
            except Exception as e:
                logger.error(f"Error processing text file {file_path}: {str(e)}")
                content = ""
                metadata = {"error": str(e)}
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            content = ""
            metadata = {"error": str(e)}
        
        return {
            "content": content.strip(),
            "metadata": metadata,
            "word_count": len(content.split()) if content else 0,
            "extraction_method": "text"
        }
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def validate_file_type(self, content_type: str, filename: str) -> bool:
        """Validate file type based on content type and extension"""
        from app.core.config import settings
        
        # Get file extension
        file_ext = Path(filename).suffix.lower().lstrip('.')
        
        # Check if extension is allowed
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            return False
        
        # Validate content type matches extension
        valid_combinations = {
            'pdf': ['application/pdf'],
            'docx': [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/octet-stream'  # Sometimes browsers send this for .docx
            ],
            'txt': ['text/plain', 'text/txt'],
            'md': ['text/markdown', 'text/plain']
        }
        
        return content_type in valid_combinations.get(file_ext, [])

# Global instance
file_processor = FileProcessor()