""" CivitAi API Module | by ANXETY """

from typing import Optional, Tuple, Dict, Any, List, Union
from urllib.parse import urlparse, parse_qs, urlencode
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import requests
import json
import os
import re
import io


class CivitAiLogger:
    """Provides colored logging functionality for API events"""

    @staticmethod
    def error(message: str):
        print(f"\033[31m[API Error]:\033[0m {message}")

    @staticmethod
    def warning(message: str):
        print(f"\033[33m[API Warning]:\033[0m {message}")

    @staticmethod
    def success(message: str):
        print(f"\033[32m[API Success]:\033[0m {message}")

    @staticmethod
    def info(message: str):
        print(f"\033[34m[API Info]:\033[0m {message}")


@dataclass
class ModelData:
    """Container for validated model metadata"""
    download_url: str
    clean_url: str
    model_name: str
    model_type: str
    version_id: str
    model_id: str
    image_url: Optional[str] = None
    image_name: Optional[str] = None
    is_early_access: bool = False


class CivitAiAPI:
    """
    Usage Example:
        api = CivitAiAPI()
        result = api.validate_download(
            url='https://civitai.com/models/...',
            file_name='model.safetensors'
        )
    """
    SUPPORTED_TYPES = {'Checkpoint', 'TextualInversion', 'LORA'}
    BASE_URL = 'https://civitai.com/api/v1'
    is_KAGGLE = os.getenv('KAGGLE_URL_BASE')    # to check NSFW

    def __init__(self, token: str = None):
        """Initialize API client with optional authentication token"""
        self.token = token or '65b66176dcf284b266579de57fbdc024'    # FAKE
        self.logger = CivitAiLogger()

    def _build_url(self, endpoint: str) -> str:
        """Construct full API endpoint URL"""
        return f"{self.BASE_URL}/{endpoint}"

    def _fetch_json(self, url: str) -> Optional[Dict]:
        """Execute GET request and return parsed JSON response"""
        try:
            headers = {'Authorization': f"Bearer {self.token}"} if self.token else {}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Request to {url} failed: {str(e)}")
            return None

    def _process_download_url(self, download_url: str) -> Tuple[str, str]:
        """Sanitize download URL and add authentication token"""
        parsed_url = urlparse(download_url)
        query_params = parse_qs(parsed_url.query)
        query_params.pop('token', None)

        clean_url = parsed_url._replace(query=urlencode(query_params, doseq=True)).geturl()
        full_url = f"{clean_url}?token={self.token}" if self.token else clean_url
        return clean_url, full_url

    def _extract_version_id(self, url: str) -> Optional[str]:
        """Extract model version ID from different URL formats"""
        try:
            # Basic URL format validation
            if not url.startswith(('http://', 'https://')):
                self.logger.error(f"Invalid URL format: {url}")
                return None

            # Handle model page URLs
            if 'civitai.com/models/' in url:
                if 'modelVersionId=' in url:
                    version_part = url.split('modelVersionId=')[1]
                    return version_part.split('&')[0].split('#')[0]

                model_id_part = url.split('/models/')[1]
                model_id = model_id_part.split('/')[0].split('?')[0]
                if not model_id.isdigit():
                    self.logger.error(f"Invalid model ID format: {model_id}")
                    return None

                model_data = self._fetch_json(self._build_url(f"models/{model_id}"))
                return model_data['modelVersions'][0]['id'] if model_data else None

            # Handle direct download URLs
            if '/api/download/models/' in url:
                version_part = url.split('/api/download/models/')[1]
                return version_part.split('?')[0].split('/')[0]

            self.logger.error(f"Unsupported URL format: {url}")
            return None

        except (IndexError, AttributeError, KeyError) as e:
            self.logger.error(f"Failed to parse URL: {url} ({str(e)})")
            return None

    def _get_preview_metadata(self, images: list, model_name: str, skip_video_previews: bool = True) -> Tuple[Optional[str], Optional[str]]:
        """Extract appropriate preview image from model metadata

        Args:
            images: List of image metadata from API
            model_name: Base name for the preview file
            skip_video_previews: If True, will skip video previews (default: True)
        """
        if not images:
            return None, None

        for img in images:
            try:
                image_url = img['url']

                # Skip video previews if enabled
                if skip_video_previews and any(image_url.lower().endswith(ext) for ext in ('.gif', '.mp4', '.webm', '.mov', '.avi')):
                    continue

                if img['nsfwLevel'] >= 4 and self.is_KAGGLE:   # Filter NSFW images for Kaggle
                    continue

                file_extension = image_url.split('.')[-1].split('?')[0]
                base_name = Path(model_name).stem
                return image_url, f"{base_name}.preview.{file_extension}"
            except (KeyError, IndexError):
                continue
        return None, None

    def _prepare_model_metadata(self, data: Dict, file_name: Optional[str]) -> ModelData:
        """Transform raw API response into structured ModelData"""
        model_type, final_name = self._determine_model_name(
            data=data,
            custom_name=file_name
        )
        clean_url, full_url = self._process_download_url(data['downloadUrl'])

        preview_url, preview_name = None, None
        if model_type in self.SUPPORTED_TYPES:
            preview_url, preview_name = self._get_preview_metadata(
                images=data.get('images', []),
                model_name=final_name
            )

        early_access = data.get('availability') == 'EarlyAccess' or data.get('earlyAccessEndsAt', None)

        return ModelData(
            download_url=full_url,
            clean_url=clean_url,
            model_name=final_name,
            model_type=model_type,
            version_id=data['id'],
            model_id=data['modelId'],
            is_early_access=early_access,
            image_url=preview_url,
            image_name=preview_name
        )

    def _determine_model_name(self, data: Dict, custom_name: Optional[str]) -> Tuple[str, str]:
        """Generate final model filename with proper extension"""
        original_name = data['files'][0]['name']
        original_extension = original_name.split('.')[-1]

        if custom_name:
            if '.' not in custom_name:
                custom_name = f"{custom_name}.{original_extension}"
            return data['model']['type'], custom_name
        return data['model']['type'], original_name

    def _get_version_data(self, url: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Helper method to extract version ID and fetch API data"""
        version_id = self._extract_version_id(url)
        if not version_id:
            self.logger.error('Invalid model URL')
            return None, None
        api_data = self._fetch_json(self._build_url(f"model-versions/{version_id}"))
        return api_data

    def _check_early_access(self, data: Dict[str, Any]) -> bool:
        """Check if model requires early access"""
        if 'modelVersions' in data:
            # Model page data
            for version in data.get('modelVersions', []):
                if version.get('availability') == 'EarlyAccess':
                    model_id = data.get('id')
                    version_id = version.get('id')
                    page = f'https://civitai.com/models/{model_id}?modelVersionId={version_id}'
                    self.logger.warning(f"Model requires Early Access: {page}")
                    return True
        else:
            # Version data
            if data.get('availability') == 'EarlyAccess' or data.get('earlyAccessEndsAt'):
                model_id = data.get('modelId')
                version_id = data.get('id')
                page = f'https://civitai.com/models/{model_id}?modelVersionId={version_id}'
                self.logger.warning(f"Model requires Early Access: {page}")
                return True
        return False

    # -- Special function for 'sdAIgen' --
    def validate_download(self, url: str, file_name: Optional[str] = None) -> Optional[ModelData]:
        """
        Validate and process model download URL

        Args:
            url: CivitAI model URL in any supported format
            file_name: Optional custom filename for the model

        Returns:
            ModelData object with processed metadata or None
        """
        api_data = self._get_version_data(url)
        if not api_data:
            return None

        model_info = self._prepare_model_metadata(api_data, file_name)
        if model_info.is_early_access:
            self.logger.warning(
                f"Model: {model_info.model_id} | Version: {model_info.version_id} -> requires Early Access\n"
                f"    > URL: https://civitai.com/models/{model_info.model_id}?modelVersionId={model_info.version_id}"
            )
            return None

        return model_info

    def get_data(self, url: str) -> Optional[Dict]:
        """Get Full Model Version metadata"""
        return self._get_version_data(url)

    # === !!! POS Func !!! ===
    def find_by_sha256(self, sha256: str) -> Optional[Dict]:
        """Find model by SHA256 hash"""
        try:
            api_url = f"{self.BASE_URL}/model-versions/by-hash/{sha256}"
            return self._fetch_json(api_url)
        except Exception as e:
            self.logger.error(f"Failed to find model by SHA256 {sha256}: {str(e)}")
            return None

    def download_preview_image(self, model_data: ModelData, save_path: Path, resize_image: bool = False, skip_video_previews: bool = True):
        """Download and save preview image for model

        Args:
            model_data: ModelData object containing image metadata
            save_path: Path where to save the preview image
            resize_image: If True, resize image to 512px (default: False)
            skip_video_previews: If True, will skip video previews (default: True)
        """
        save_path = Path(save_path)
        if not model_data.image_url:
            return

        preview_url, preview_name = self._get_preview_metadata(
            images=model_data._raw_images,
            model_name=model_data.model_name,
            skip_video_previews=skip_video_previews
        )

        if not preview_url or not preview_name:
            return

        preview_path = save_path / preview_name

        if preview_path.exists():
            return

        # Download preview image
        try:
            headers = {'User-Agent': 'CivitaiLink:Automatic1111'}
            response = requests.get(preview_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Process image data based on resize_image parameter
            if resize_image:
                image_data = self._resize_image(response.content, size=512)
            else:
                # Use original image data without resizing
                image_data = io.BytesIO(response.content)
                image_data.seek(0)

            # Save image
            preview_path.write_bytes(image_data.read())
            self.logger.success(f"Preview image saved: {preview_path}")

        except Exception as e:
            self.logger.error(f"Failed to download preview image: {str(e)}")

    def _resize_image(self, image_bytes: bytes, size: int = 512) -> io.BytesIO:
        """Resize image to specified size while maintaining aspect ratio"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            w, h = image.size

            # Calculate new size maintaining aspect ratio
            if w > h:
                new_size = (size, int(h * size / w))
            else:
                new_size = (int(w * size / h), size)

            resized_image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = io.BytesIO()
            resized_image.save(output, format='PNG')
            output.seek(0)
            return output

        except Exception as e:
            self.logger.error(f"Failed to resize image: {str(e)}")
            # Return original image if resize fails
            output = io.BytesIO(image_bytes)
            output.seek(0)
            return output

    def save_model_info(self, model_data: ModelData, save_path: Path):
        """Save model metadata to JSON file"""
        save_path = Path(save_path)

        # Generate info-json path
        model_name = model_data.model_name
        info_path = save_path / f'{Path(model_name).stem}.json'

        if info_path.exists():
            return

        # Save MetaData to JSON
        try:
            base_list = {
                'SD 1': 'SD1',
                'SD 1.5': 'SD1',
                'SD 2': 'SD2',
                'SD 3': 'SD3',
                'SDXL': 'SDXL',
                'Pony': 'SDXL',
                'Illustrious': 'SDXL',
            }

            info_data = {
                'model_type': model_data.model_type,
                'sd version': next((s for k, s in base_list.items() if k in model_data.base_model), ''),
                'modelId': model_data.model_id,
                'modelVersionId': model_data.version_id,
                'activation text': ', '.join(model_data.trained_words or []),
                'sha256': model_data.sha256
            }
            info_path.write_text(json.dumps(info_data, indent=4))

            self.logger.success(f"Model info saved: {info_path}")

        except Exception as e:
            self.logger.error(f"Failed to save model info: {str(e)}")

    def get_model_versions(self, model_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get all versions of a model"""
        try:
            api_data = self._fetch_json(self._build_url(f"models/{model_id}"))
            if api_data and 'modelVersions' in api_data:
                return api_data['modelVersions']
            return None
        except Exception as e:
            self.logger.error(f"Failed to get model versions for {model_id}: {str(e)}")
            return None