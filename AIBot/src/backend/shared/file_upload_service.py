import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
from fastapi import HTTPException, UploadFile


class FileUploadService:
    """Shared service for handling file uploads across the application."""
    
    @staticmethod
    def create_upload_directory(base_path: str, *subdirs: str) -> Path:
        """
        Create upload directory structure.
        
        Args:
            base_path: Base directory path (e.g., "uploads")
            *subdirs: Additional subdirectories to create
            
        Returns:
            Path object for the created directory
        """
        upload_dir = Path(base_path)
        for subdir in subdirs:
            upload_dir = upload_dir / str(subdir)
        
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> Tuple[str, str]:
        """
        Generate a unique filename while preserving the extension.
        
        Args:
            original_filename: Original filename from upload
            
        Returns:
            Tuple of (unique_filename, file_extension)
        """
        file_extension = Path(original_filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        return unique_filename, file_extension
    
    @staticmethod
    async def save_uploaded_file(file: UploadFile, file_path: Path) -> bytes:
        """
        Save uploaded file to specified path.
        
        Args:
            file: FastAPI UploadFile object
            file_path: Path where file should be saved
            
        Returns:
            File content as bytes
            
        Raises:
            HTTPException: If file saving fails
        """
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            return content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    @staticmethod
    def get_file_type_info(file_extension: str, filename: str) -> Tuple[str, str]:
        """
        Get file type information and appropriate message text.
        
        Args:
            file_extension: File extension (e.g., '.jpg', '.pdf')
            filename: Original filename
            
        Returns:
            Tuple of (message_text, analysis_prompt)
        """
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            message_text = f"🖼️ {filename}"
            analysis_prompt = f"Please analyze this image and describe what you see. Image: {filename}"
        elif file_extension == '.pdf':
            message_text = f"📄 {filename}"
            analysis_prompt = f"Please summarize this PDF document. Document: {filename}"
        else:
            message_text = f"📎 {filename}"
            analysis_prompt = f"I've uploaded a file: {filename}. Please acknowledge the upload."
        
        return message_text, analysis_prompt
    
    @staticmethod
    def create_file_url(base_url: str, *path_parts: str) -> str:
        """
        Create a file URL from path components.
        
        Args:
            base_url: Base URL (e.g., "/uploads")
            *path_parts: URL path components
            
        Returns:
            Complete file URL
        """
        url_parts = [base_url.rstrip('/')]
        url_parts.extend(str(part) for part in path_parts)
        return '/'.join(url_parts)


# Convenience instance for easy importing
file_upload_service = FileUploadService()
