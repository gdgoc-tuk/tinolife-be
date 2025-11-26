"""이미지 업로드 유틸리티"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile

from app.core.config import settings
from app.common.exceptions import BadRequestException


class ImageUploader:
    """이미지 업로드 처리 클래스"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_size = settings.MAX_IMAGE_SIZE
        self.allowed_types = settings.ALLOWED_IMAGE_TYPES
        self.use_s3 = settings.USE_S3
        
        # 로컬 업로드 디렉토리 생성
        if not self.use_s3:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _validate_image(self, file: UploadFile) -> None:
        """이미지 유효성 검사"""
        # MIME 타입 확인
        if file.content_type not in self.allowed_types:
            raise BadRequestException(
                f"허용되지 않는 이미지 형식입니다. 허용 형식: {', '.join(self.allowed_types)}"
            )
    
    def _generate_filename(self, original_filename: str, prefix: str = "") -> str:
        """고유한 파일명 생성"""
        ext = Path(original_filename).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:8]
        
        if prefix:
            return f"{prefix}/{timestamp}/{unique_id}{ext}"
        return f"{timestamp}/{unique_id}{ext}"
    
    async def upload_local(
        self, 
        file: UploadFile, 
        prefix: str = "images"
    ) -> Tuple[str, str, int, str]:
        """
        로컬에 이미지 업로드
        
        Args:
            file: 업로드할 파일
            prefix: 저장 경로 prefix (images, questions, answers)
            
        Returns:
            (image_url, image_key, file_size, mime_type)
        """
        self._validate_image(file)
        
        # 파일 내용 읽기
        content = await file.read()
        file_size = len(content)
        
        # 파일 크기 확인
        if file_size > self.max_size:
            raise BadRequestException(
                f"파일 크기가 너무 큽니다. 최대 {self.max_size // (1024*1024)}MB까지 허용됩니다."
            )
        
        # 파일명 생성
        image_key = self._generate_filename(file.filename, prefix)
        file_path = self.upload_dir / image_key
        
        # 디렉토리 생성
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(content)
        
        # URL 생성 (정적 파일 서빙 경로)
        image_url = f"/uploads/{image_key}"
        
        return image_url, image_key, file_size, file.content_type
    
    async def upload_s3(
        self, 
        file: UploadFile, 
        prefix: str = "images"
    ) -> Tuple[str, str, int, str]:
        """
        S3에 이미지 업로드
        
        Args:
            file: 업로드할 파일
            prefix: S3 키 prefix
            
        Returns:
            (image_url, image_key, file_size, mime_type)
        """
        self._validate_image(file)
        
        # boto3 동적 import (S3 사용 시에만)
        try:
            import boto3
        except ImportError:
            raise BadRequestException("S3 업로드를 위해 boto3가 필요합니다")
        
        # 파일 내용 읽기
        content = await file.read()
        file_size = len(content)
        
        # 파일 크기 확인
        if file_size > self.max_size:
            raise BadRequestException(
                f"파일 크기가 너무 큽니다. 최대 {self.max_size // (1024*1024)}MB까지 허용됩니다."
            )
        
        # 파일명 생성
        image_key = self._generate_filename(file.filename, prefix)
        
        # S3 클라이언트 생성 (MinIO 지원)
        client_config = {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
        }
        
        # MinIO 또는 S3 호환 스토리지 사용 시 endpoint_url 설정
        if settings.AWS_S3_ENDPOINT_URL:
            client_config['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
        else:
            client_config['region_name'] = settings.AWS_S3_REGION
        
        s3_client = boto3.client('s3', **client_config)
        
        # S3 업로드
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=image_key,
            Body=content,
            ContentType=file.content_type
        )
        
        # URL 생성
        if settings.AWS_S3_ENDPOINT_URL:
            # MinIO URL (외부 접근용 URL 사용)
            # Docker 내부: http://minio:9000, 외부: http://localhost:9000
            external_endpoint = settings.AWS_S3_ENDPOINT_URL.replace("minio", "localhost")
            image_url = f"{external_endpoint}/{settings.AWS_S3_BUCKET}/{image_key}"
        else:
            # AWS S3 URL
            image_url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{image_key}"
        
        return image_url, image_key, file_size, file.content_type
    
    async def upload(
        self, 
        file: UploadFile, 
        prefix: str = "images"
    ) -> Tuple[str, str, int, str]:
        """
        이미지 업로드 (설정에 따라 로컬 또는 S3)
        
        Args:
            file: 업로드할 파일
            prefix: 저장 경로/키 prefix
            
        Returns:
            (image_url, image_key, file_size, mime_type)
        """
        if self.use_s3:
            return await self.upload_s3(file, prefix)
        return await self.upload_local(file, prefix)
    
    def delete_local(self, image_key: str) -> bool:
        """로컬 이미지 삭제"""
        file_path = self.upload_dir / image_key
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def delete_s3(self, image_key: str) -> bool:
        """S3/MinIO 이미지 삭제"""
        try:
            import boto3
        except ImportError:
            return False
        
        # S3 클라이언트 생성 (MinIO 지원)
        client_config = {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
        }
        
        if settings.AWS_S3_ENDPOINT_URL:
            client_config['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
        else:
            client_config['region_name'] = settings.AWS_S3_REGION
        
        s3_client = boto3.client('s3', **client_config)
        
        s3_client.delete_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=image_key
        )
        return True
    
    def delete(self, image_key: str) -> bool:
        """이미지 삭제 (설정에 따라 로컬 또는 S3)"""
        if self.use_s3:
            return self.delete_s3(image_key)
        return self.delete_local(image_key)


def get_image_uploader() -> ImageUploader:
    """ImageUploader 인스턴스 반환"""
    return ImageUploader()
