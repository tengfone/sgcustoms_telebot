import requests
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple, Union
from PIL import Image
import config
import logging
from datetime import datetime
from cache import api_cache

# Get logger
logger = logging.getLogger(__name__)

def get_all_traffic_images() -> List[Dict[str, Any]]:
    """
    Fetch all traffic images from LTA DataMall API
    
    Returns:
        List of dictionaries containing traffic image data
    """
    # Try to get from cache first
    cached_data = api_cache.get("all_images")
    if cached_data is not None:
        logger.info("Returning cached traffic images")
        return cached_data
    
    headers = {
        'AccountKey': config.LTA_API_KEY,
        'accept': 'application/json'
    }
    
    try:
        logger.info(f"Fetching traffic images from {config.LTA_API_URL}")
        response = requests.get(config.LTA_API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        images = data.get('value', [])
        logger.info(f"Received {len(images)} images from API")
        
        # Cache the response
        api_cache.set("all_images", images)
        
        # Log the available camera IDs for debugging
        camera_ids = [img.get('CameraID') for img in images if 'CameraID' in img]
        logger.debug(f"Available camera IDs: {', '.join(camera_ids[:10])}... (showing first 10)")
        
        return images
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching traffic images: {e}")
        return []

def get_checkpoint_images() -> Dict[str, Dict[str, Any]]:
    """
    Filter traffic images to get only the customs checkpoint cameras
    
    Returns:
        Dictionary mapping checkpoint names to their image data
    """
    # Try to get from cache first
    cached_data = api_cache.get("checkpoint_images")
    if cached_data is not None:
        logger.info("Returning cached checkpoint images")
        return cached_data
    
    all_images = get_all_traffic_images()
    checkpoint_images = {}
    available_camera_ids = set(img.get('CameraID') for img in all_images if 'CameraID' in img)
    
    logger.info(f"Filtering images for {len(config.CHECKPOINTS)} checkpoint cameras")
    
    # Check if configured checkpoint camera IDs exist in the available IDs
    for checkpoint_name, checkpoint_id in config.CHECKPOINTS.items():
        if checkpoint_id not in available_camera_ids:
            logger.warning(f"Camera ID {checkpoint_id} for {checkpoint_name} not found in API response")
    
    # Filter images for checkpoints
    for image_data in all_images:
        camera_id = image_data.get('CameraID')
        for checkpoint_name, checkpoint_id in config.CHECKPOINTS.items():
            if camera_id == checkpoint_id:
                logger.info(f"Found image for {checkpoint_name}")
                checkpoint_images[checkpoint_name] = image_data
                break
    
    # Cache the filtered images
    api_cache.set("checkpoint_images", checkpoint_images)
    
    logger.info(f"Found {len(checkpoint_images)} checkpoint images")
    return checkpoint_images

def get_checkpoint_image(checkpoint_name: str) -> Tuple[Union[bytes, None], str]:
    """
    Get the image for a specific checkpoint
    
    Args:
        checkpoint_name: The name of the checkpoint
    
    Returns:
        Tuple of (image_bytes, timestamp) or (None, error_message)
    """
    logger.info(f"Getting image for checkpoint: {checkpoint_name}")
    
    if checkpoint_name not in config.CHECKPOINTS:
        logger.error(f"Checkpoint '{checkpoint_name}' not found in configuration")
        return None, f"Checkpoint '{checkpoint_name}' not found"
    
    # Try to get checkpoint data from cache
    checkpoint_images = get_checkpoint_images()
    image_data = checkpoint_images.get(checkpoint_name)
    
    if not image_data:
        logger.warning(f"No image data found for checkpoint '{checkpoint_name}'")
        return None, f"No image found for checkpoint '{checkpoint_name}'"
    
    image_url = image_data.get('ImageLink')
    api_timestamp = image_data.get('Timestamp', 'Unknown time')
    
    # Get the actual last updated time from cache
    cache_timestamp = api_cache.get_last_updated("all_images")
    if cache_timestamp:
        timestamp = cache_timestamp.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    else:
        timestamp = api_timestamp
    
    try:
        logger.info(f"Downloading image from: {image_url}")
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        return image_response.content, timestamp
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching image: {e}")
        return None, f"Error fetching image: {e}"

def get_image_with_metadata(checkpoint_name: str) -> Tuple[Optional[bytes], str, str]:
    """
    Get the image for a specific checkpoint along with its metadata
    
    Args:
        checkpoint_name: The name of the checkpoint
    
    Returns:
        Tuple of (image_bytes, timestamp, location_description) or (None, error_message, '')
    """
    image_bytes, timestamp_or_error = get_checkpoint_image(checkpoint_name)
    
    if image_bytes:
        location = checkpoint_name
        return image_bytes, timestamp_or_error, location
    else:
        logger.warning(f"Failed to get image for {checkpoint_name}: {timestamp_or_error}")
        return None, timestamp_or_error, ''

def force_refresh() -> None:
    """Force refresh all cached data."""
    api_cache.clear()
    logger.info("Forced refresh of all cached data") 