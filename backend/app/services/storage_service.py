"""
Serviço de Storage para upload de arquivos via Supabase
"""

import os
from typing import Optional, Set, Tuple
from uuid import UUID
from fastapi import UploadFile, HTTPException
from loguru import logger

from app.config import settings


class StorageService:
    """Serviço para gerenciar uploads de arquivos no Supabase Storage"""

    # Extensões permitidas por tipo
    ALLOWED_EXTENSIONS = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'},
        'document': {'.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx'},
        'video': {'.mp4', '.mov', '.avi', '.mkv'},
        'archive': {'.zip', '.rar', '.7z'},
    }

    # Tamanho máximo: 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __init__(self):
        """Inicializa o serviço de storage"""
        self.supabase = settings.supabase

    def _validate_file_extension(
        self,
        filename: str,
        allowed_types: list[str]
    ) -> Tuple[bool, str]:
        """
        Valida a extensão do arquivo

        Args:
            filename: Nome do arquivo
            allowed_types: Lista de tipos permitidos (image, document, video, archive)

        Returns:
            Tuple (is_valid, extension)
        """
        _, ext = os.path.splitext(filename.lower())

        # Verificar se extensão está nos tipos permitidos
        allowed_extensions: Set[str] = set()
        for file_type in allowed_types:
            if file_type in self.ALLOWED_EXTENSIONS:
                allowed_extensions.update(self.ALLOWED_EXTENSIONS[file_type])

        is_valid = ext in allowed_extensions
        return is_valid, ext

    async def upload_file(
        self,
        bucket: str,
        file: UploadFile,
        project_id: UUID,
        item_id: UUID,
        allowed_types: list[str] = ['image', 'document', 'video', 'archive']
    ) -> dict:
        """
        Faz upload de um arquivo para o Supabase Storage

        Args:
            bucket: Nome do bucket (project-deliveries, project-approvals, payment-proofs)
            file: Arquivo a ser enviado
            project_id: ID do projeto
            item_id: ID do item (delivery, approval ou payment)
            allowed_types: Tipos de arquivo permitidos

        Returns:
            Dict com url, filename, size, content_type

        Raises:
            HTTPException: Se arquivo for inválido
        """
        try:
            # Validar tamanho
            contents = await file.read()
            file_size = len(contents)

            if file_size > self.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"Arquivo muito grande. Máximo: {self.MAX_FILE_SIZE / (1024*1024):.0f}MB"
                )

            # Validar extensão
            is_valid, ext = self._validate_file_extension(file.filename or '', allowed_types)
            if not is_valid:
                allowed_exts = []
                for t in allowed_types:
                    if t in self.ALLOWED_EXTENSIONS:
                        allowed_exts.extend(self.ALLOWED_EXTENSIONS[t])
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo de arquivo não permitido. Permitidos: {', '.join(allowed_exts)}"
                )

            # Construir caminho do arquivo
            # Formato: {project_id}/{item_id}/{filename}
            file_path = f"{project_id}/{item_id}/{file.filename}"

            # Upload para Supabase Storage
            try:
                result = self.supabase.storage.from_(bucket).upload(
                    path=file_path,
                    file=contents,
                    file_options={
                        "content-type": file.content_type or "application/octet-stream",
                        "upsert": "true"  # Sobrescrever se já existir
                    }
                )
            except Exception as e:
                logger.error(f"Erro ao fazer upload no Supabase: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Erro ao fazer upload do arquivo"
                )

            # Gerar URL assinada (válida por 1 ano)
            try:
                url_data = self.supabase.storage.from_(bucket).create_signed_url(
                    path=file_path,
                    expires_in=31536000  # 1 ano em segundos
                )
                file_url = url_data.get('signedURL') or url_data.get('signedUrl')
            except Exception as e:
                logger.error(f"Erro ao gerar URL assinada: {e}")
                # Se falhar, tentar URL pública
                file_url = self.supabase.storage.from_(bucket).get_public_url(file_path)

            return {
                'url': file_url,
                'filename': file.filename,
                'size': file_size,
                'content_type': file.content_type
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado no upload: {e}")
            raise HTTPException(status_code=500, detail="Erro ao processar upload")

    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Deleta um arquivo do Supabase Storage

        Args:
            bucket: Nome do bucket
            file_path: Caminho do arquivo

        Returns:
            True se deletado com sucesso
        """
        try:
            self.supabase.storage.from_(bucket).remove([file_path])
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo: {e}")
            return False


# Instância global do serviço
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Retorna instância do StorageService"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
