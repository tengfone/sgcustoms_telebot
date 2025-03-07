from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any
import config
from datetime import datetime
import pytz

def create_checkpoint_keyboard() -> InlineKeyboardMarkup:
    """
    Create an inline keyboard with checkpoint options
    
    Returns:
        InlineKeyboardMarkup with checkpoint buttons
    """
    keyboard = []
    
    # Create rows with 2 buttons per row
    for i in range(0, len(config.CHECKPOINTS), 2):
        row = []
        checkpoints = list(config.CHECKPOINTS.keys())[i:i+2]
        
        for checkpoint in checkpoints:
            button = InlineKeyboardButton(
                text=checkpoint,
                callback_data=f"checkpoint:{checkpoint}"
            )
            row.append(button)
        
        keyboard.append(row)
    
    # Add refresh and force refresh buttons at the bottom
    keyboard.append([
        InlineKeyboardButton(
            text="🔄 Refresh All",
            callback_data="refresh_all"
        ),
        InlineKeyboardButton(
            text="🔄 Force Refresh",
            callback_data="force_refresh"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_checkpoint_detail_keyboard(checkpoint_name: str) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for a specific checkpoint
    
    Args:
        checkpoint_name: The name of the checkpoint
    
    Returns:
        InlineKeyboardMarkup with checkpoint-specific buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔄 Refresh",
                callback_data=f"refresh:{checkpoint_name}"
            ),
            InlineKeyboardButton(
                text="🔄 Force Refresh",
                callback_data=f"force_refresh:{checkpoint_name}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📍 Location",
                callback_data=f"location:{checkpoint_name}"
            ),
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data="show_checkpoints"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def format_timestamp(timestamp: str) -> str:
    """
    Format the timestamp to be more readable
    
    Args:
        timestamp: The timestamp string from the API
    
    Returns:
        Formatted timestamp string
    """
    try:
        # Parse the timestamp
        if 'T' in timestamp:
            dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S+08:00")
        else:
            # If it's already a formatted string, return it
            return timestamp
        
        # Convert to Singapore timezone
        sg_tz = pytz.timezone('Asia/Singapore')
        dt = pytz.utc.localize(dt).astimezone(sg_tz)
        
        # Get current time in Singapore timezone
        now = datetime.now(sg_tz)
        
        # Calculate time difference
        diff = now - dt
        
        # If less than a minute
        if diff.total_seconds() < 60:
            return "Just now"
        # If less than an hour
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        # If less than a day
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            # Format as date and time
            return dt.strftime("%d %b %Y, %H:%M:%S")
    except Exception as e:
        # Return original if parsing fails
        return timestamp 