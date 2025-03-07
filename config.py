import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables")

# LTA DataMall API Key
LTA_API_KEY = os.getenv("LTA_API_KEY")
if not LTA_API_KEY:
    raise ValueError("LTA_API_KEY not found in environment variables")

# LTA DataMall API URL for traffic images
LTA_API_URL = "http://datamall2.mytransport.sg/ltaodataservice/Traffic-Imagesv2"

# Dictionary of custom checkpoints with their camera IDs
# These are actual camera IDs for Singapore checkpoints
CHECKPOINTS = {
    "Second Link at Tuas": "4703",
    "Tuas Checkpoint": "4713",
    "Woodlands Causeway (Towards Johor)": "2701",
    "Woodlands Checkpoint (Towards BKE)": "2702",
}

# Checkpoint coordinates (updated for actual locations)
CHECKPOINT_COORDINATES = {
    "Second Link at Tuas": (1.3399, 103.6330),  # Second Link coordinates
    "Tuas Checkpoint": (1.3479, 103.6403),  # Tuas Checkpoint coordinates
    "Woodlands Causeway (Towards Johor)": (1.4447, 103.7706),  # Woodlands Causeway coordinates
    "Woodlands Checkpoint (Towards BKE)": (1.4430, 103.7697),  # Woodlands Checkpoint coordinates
} 