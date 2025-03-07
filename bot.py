import logging
from io import BytesIO
from typing import Dict, List, Any, Tuple, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
import lta_api
import utils
import requests
import json

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Check API access at startup
def check_api_access():
    """Test LTA API access and log available camera IDs"""
    try:
        images = lta_api.get_all_traffic_images()
        if not images:
            logger.warning("No images returned from LTA API")
            return False
        
        # Log all camera IDs for reference
        camera_ids = [img.get('CameraID') for img in images if 'CameraID' in img]
        logger.info(f"Available camera IDs: {', '.join(camera_ids[:20])}... (showing first 20)")
        
        # Check if our configured checkpoint IDs are in the available IDs
        available_ids = set(camera_ids)
        checkpoint_ids = set(config.CHECKPOINTS.values())
        missing_ids = checkpoint_ids - available_ids
        
        if missing_ids:
            logger.warning(f"Some configured checkpoint IDs are not available: {missing_ids}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking API access: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when the command /start is issued."""
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Hello {user.mention_html()}!\n\n"
        f"Welcome to the Singapore Customs Checkpoint Bot. This bot provides real-time "
        f"traffic images from Singapore's customs checkpoints.\n\n"
        f"<b>This bot works with buttons only.</b> Please use the commands below or tap on buttons.\n\n"
        f"Use /checkpoints to see available checkpoints or /help for more information.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Show Checkpoints", callback_data="show_checkpoints"),
            InlineKeyboardButton("Help", callback_data="help")
        ]])
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    # Show typing indicator
    if update.message:
        await update.message.chat.send_action("typing")
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.chat.send_action("typing")
    
    help_text = (
        "🔍 *Available Commands*\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/checkpoints - Show available customs checkpoints\n"
        "/about - Information about this bot\n"
        "/status - Check API connection status\n\n"
        "📱 *How to Use*\n\n"
        "1. Use /checkpoints to see a list of checkpoints\n"
        "2. Tap on any checkpoint to view its traffic image\n"
        "3. Use the refresh button to get the latest image\n"
        "4. Use the location button to see the checkpoint location\n\n"
        "💡 *Tip:* This bot only works with buttons. Text messages will be ignored."
    )
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Show Checkpoints", callback_data="show_checkpoints")
    ]])
    
    # If called from callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(
                text=help_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message in help_command: {e}")
            await query.message.reply_markdown(
                help_text,
                reply_markup=keyboard
            )
    else:  # If called from command
        await update.message.reply_markdown(
            help_text,
            reply_markup=keyboard
        )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send information about the bot when the command /about is issued."""
    # Show typing indicator
    if update.message:
        await update.message.chat.send_action("typing")
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.chat.send_action("typing")
    
    about_text = (
        "📊 *Singapore Customs Checkpoint Bot*\n\n"
        "This bot provides real-time traffic images from Singapore's customs checkpoints "
        "using data from the Land Transport Authority (LTA) DataMall API.\n\n"
        "🔄 *Data Source*\n"
        "All images are provided by LTA DataMall and are refreshed approximately every few minutes.\n\n"
        "🛠 *Technical Information*\n"
        "Built with Python using the python-telegram-bot library.\n\n"
        "If you have any feedback or suggestions, please contact the bot administrator."
    )
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Show Checkpoints", callback_data="show_checkpoints"),
        InlineKeyboardButton("Help", callback_data="help")
    ]])
    
    # If called from callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(
                text=about_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message in about_command: {e}")
            await query.message.reply_markdown(
                about_text,
                reply_markup=keyboard
            )
    else:  # If called from command
        await update.message.reply_markdown(
            about_text,
            reply_markup=keyboard
        )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check API connection status and report to user."""
    # Show typing indicator
    if update.message:
        await update.message.chat.send_action("typing")
        initial_message = await update.message.reply_text("🔄 Checking connection to LTA DataMall API...")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.chat.send_action("typing")
        initial_message = await query.message.reply_text("🔄 Checking connection to LTA DataMall API...")
    else:
        return
    
    # Show typing indicator again for the API call
    if update.message:
        await update.message.chat.send_action("typing")
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.chat.send_action("typing")
    
    try:
        images = lta_api.get_all_traffic_images()
        if images:
            # Show typing indicator for processing results
            if update.message:
                await update.message.chat.send_action("typing")
            elif update.callback_query and update.callback_query.message:
                await update.callback_query.message.chat.send_action("typing")
            
            checkpoint_images = lta_api.get_checkpoint_images()
            found_checkpoints = list(checkpoint_images.keys())
            
            status_text = (
                "✅ *Connection to LTA DataMall API successful*\n\n"
                f"📊 Total images available: {len(images)}\n"
                f"🚧 Checkpoint cameras found: {len(checkpoint_images)}/{len(config.CHECKPOINTS)}\n\n"
            )
            
            if found_checkpoints:
                status_text += "📷 *Available Checkpoints:*\n" + "\n".join([f"- {cp}" for cp in found_checkpoints])
            else:
                status_text += "❓ No configured checkpoint cameras found in API response.\n\n"
                status_text += "Try updating the camera IDs in config.py."
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("Show Checkpoints", callback_data="show_checkpoints"),
                InlineKeyboardButton("Help", callback_data="help")
            ]])
            
            await initial_message.edit_text(
                text=status_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            await initial_message.edit_text(
                text="⚠️ *Connection issue with LTA DataMall API*\n\n"
                     "The API returned an empty response. Please check your API key.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Try Again", callback_data="status"),
                    InlineKeyboardButton("Help", callback_data="help")
                ]])
            )
    except Exception as e:
        await initial_message.edit_text(
            text=f"❌ *Error connecting to LTA DataMall API*\n\n"
                 f"Error: {str(e)}\n\n"
                 f"Please check your API key and internet connection.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Try Again", callback_data="status"),
                InlineKeyboardButton("Help", callback_data="help")
            ]])
        )

async def show_checkpoints(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available checkpoints with an inline keyboard."""
    # Show typing indicator
    if update.message:
        await update.message.chat.send_action("typing")
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.chat.send_action("typing")
    
    keyboard = utils.create_checkpoint_keyboard()
    
    message_text = "🚧 *Singapore Customs Checkpoints*\n\nSelect a checkpoint to view its current traffic situation:"
    
    # Handle both direct commands and callback queries
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            # Try to edit the message if it has text
            if query.message and hasattr(query.message, 'text') and query.message.text:
                await query.edit_message_text(
                    text=message_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                # If not a text message, send a new message
                await query.message.reply_text(
                    text=message_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Error in show_checkpoints: {e}")
            # Send new message as fallback
            await query.message.reply_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    else:  # Command handler
        await update.message.reply_markdown(
            text=message_text,
            reply_markup=keyboard
        )

async def checkpoint_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the traffic image for a specific checkpoint."""
    query = update.callback_query
    await query.answer()
    
    # Extract checkpoint name from callback data
    _, checkpoint_name = query.data.split(":", 1)
    
    # Show "typing" action to indicate processing
    await query.message.chat.send_action("typing")
    
    # Get checkpoint image and metadata
    image_bytes, timestamp, location = lta_api.get_image_with_metadata(checkpoint_name)
    
    if image_bytes:
        formatted_timestamp = utils.format_timestamp(timestamp)
        caption = f"🚧 *{checkpoint_name}*\n📅 Last updated: {formatted_timestamp}"
        
        # Create keyboard for this checkpoint
        keyboard = utils.create_checkpoint_detail_keyboard(checkpoint_name)
        
        # Send image with caption and keyboard
        await query.message.reply_photo(
            photo=BytesIO(image_bytes),
            caption=caption,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Delete the original message with checkpoint list to keep the chat clean
        await query.delete_message()
    else:
        # If fetching image failed, show error message
        error_message = f"❌ Error: {timestamp}"
        await query.edit_message_text(
            text=error_message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="show_checkpoints")
            ]])
        )

async def refresh_checkpoint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Refresh the traffic image for a specific checkpoint."""
    query = update.callback_query
    await query.answer("Refreshing image...")
    
    # Extract checkpoint name from callback data
    _, checkpoint_name = query.data.split(":", 1)
    
    # Show "typing" action to indicate processing
    await query.message.chat.send_action("typing")
    
    # Get updated checkpoint image and metadata
    image_bytes, timestamp, location = lta_api.get_image_with_metadata(checkpoint_name)
    
    if image_bytes:
        formatted_timestamp = utils.format_timestamp(timestamp)
        caption = f"🚧 *{checkpoint_name}* (Refreshed)\n📅 Last updated: {formatted_timestamp}"
        
        # Create keyboard for this checkpoint
        keyboard = utils.create_checkpoint_detail_keyboard(checkpoint_name)
        
        try:
            # Update the image message
            with BytesIO(image_bytes) as bio:
                await query.message.edit_media(
                    media=InputMediaPhoto(
                        media=bio,
                        caption=caption,
                        parse_mode="Markdown"
                    ),
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Error editing media: {e}")
            # Send as a new message if editing fails
            await query.message.reply_photo(
                photo=BytesIO(image_bytes),
                caption=caption,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    else:
        # If fetching image failed, show error message
        await query.message.reply_text(
            text=f"❌ Error refreshing image: {timestamp}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Try Again", callback_data=f"refresh:{checkpoint_name}")
            ]])
        )

async def refresh_all_checkpoints(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all checkpoint images in a series of messages."""
    query = update.callback_query
    await query.answer("Fetching all checkpoint images...")
    
    # Show typing indicator
    await query.message.chat.send_action("typing")
    
    await query.edit_message_text(
        text="🔄 Loading images from all checkpoints. Please wait...",
        reply_markup=None
    )
    
    # Fetch images for all checkpoints
    for checkpoint_name in config.CHECKPOINTS.keys():
        # Show typing indicator for each checkpoint
        await query.message.chat.send_action("typing")
        
        image_bytes, timestamp, location = lta_api.get_image_with_metadata(checkpoint_name)
        
        if image_bytes:
            formatted_timestamp = utils.format_timestamp(timestamp)
            caption = f"🚧 *{checkpoint_name}*\n📅 Last updated: {formatted_timestamp}"
            
            # Send each checkpoint image as a separate message
            await query.message.reply_photo(
                photo=BytesIO(image_bytes),
                caption=caption,
                parse_mode="Markdown"
            )
        else:
            # Skip failed images or notify about the failure
            await query.message.reply_text(
                text=f"❌ Could not load image for {checkpoint_name}: {timestamp}"
            )
    
    # Show the checkpoints keyboard again
    keyboard = utils.create_checkpoint_keyboard()
    await query.message.reply_text(
        text="👆 Here are all the latest checkpoint images. Select a checkpoint for more options:",
        reply_markup=keyboard
    )

async def show_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the location of a specific checkpoint on the map."""
    query = update.callback_query
    await query.answer()
    
    # Show typing indicator
    await query.message.chat.send_action("typing")
    
    # Extract checkpoint name from callback data
    _, checkpoint_name = query.data.split(":", 1)
    
    # Get coordinates if available
    coordinates = config.CHECKPOINT_COORDINATES.get(checkpoint_name)
    
    if coordinates:
        latitude, longitude = coordinates
        # Send location message
        await query.message.reply_location(
            latitude=latitude,
            longitude=longitude
        )
        
        await query.message.reply_text(
            text=f"📍 Location of {checkpoint_name}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data=f"checkpoint:{checkpoint_name}")
            ]])
        )
    else:
        await query.message.reply_text(
            text=f"❌ Location information for {checkpoint_name} is not available.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data=f"checkpoint:{checkpoint_name}")
            ]])
        )

async def force_refresh_checkpoint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Force refresh the traffic image for a specific checkpoint."""
    query = update.callback_query
    await query.answer("Force refreshing image...")
    
    # Extract checkpoint name from callback data
    _, checkpoint_name = query.data.split(":", 1)
    
    # Show "typing" action to indicate processing
    await query.message.chat.send_action("typing")
    
    # Force refresh the cache
    lta_api.force_refresh()
    
    # Get updated checkpoint image and metadata
    image_bytes, timestamp, location = lta_api.get_image_with_metadata(checkpoint_name)
    
    if image_bytes:
        formatted_timestamp = utils.format_timestamp(timestamp)
        caption = f"🚧 *{checkpoint_name}* (Force Refreshed)\n📅 Last updated: {formatted_timestamp}"
        
        # Create keyboard for this checkpoint
        keyboard = utils.create_checkpoint_detail_keyboard(checkpoint_name)
        
        try:
            # Update the image message
            with BytesIO(image_bytes) as bio:
                await query.message.edit_media(
                    media=InputMediaPhoto(
                        media=bio,
                        caption=caption,
                        parse_mode="Markdown"
                    ),
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Error editing media: {e}")
            # Send as a new message if editing fails
            await query.message.reply_photo(
                photo=BytesIO(image_bytes),
                caption=caption,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    else:
        # If fetching image failed, show error message
        await query.message.reply_text(
            text=f"❌ Error refreshing image: {timestamp}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Try Again", callback_data=f"force_refresh:{checkpoint_name}")
            ]])
        )

async def force_refresh_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Force refresh and show all checkpoint images."""
    query = update.callback_query
    await query.answer("Force refreshing all images...")
    
    # Show typing indicator
    await query.message.chat.send_action("typing")
    
    # Force refresh the cache
    lta_api.force_refresh()
    
    await query.edit_message_text(
        text="🔄 Force refreshing all checkpoints. Please wait...",
        reply_markup=None
    )
    
    # Fetch images for all checkpoints
    for checkpoint_name in config.CHECKPOINTS.keys():
        # Show typing indicator for each checkpoint
        await query.message.chat.send_action("typing")
        
        image_bytes, timestamp, location = lta_api.get_image_with_metadata(checkpoint_name)
        
        if image_bytes:
            formatted_timestamp = utils.format_timestamp(timestamp)
            caption = f"🚧 *{checkpoint_name}*\n📅 Last updated: {formatted_timestamp}"
            
            # Send each checkpoint image as a separate message
            await query.message.reply_photo(
                photo=BytesIO(image_bytes),
                caption=caption,
                parse_mode="Markdown"
            )
        else:
            # Skip failed images or notify about the failure
            await query.message.reply_text(
                text=f"❌ Could not load image for {checkpoint_name}: {timestamp}"
            )
    
    # Show the checkpoints keyboard again
    keyboard = utils.create_checkpoint_keyboard()
    await query.message.reply_text(
        text="👆 Here are all the latest checkpoint images. Select a checkpoint for more options:",
        reply_markup=keyboard
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the different callback queries."""
    query = update.callback_query
    
    # Show typing indicator for all callback queries
    if query.message:
        await query.message.chat.send_action("typing")
    
    try:
        # Route to appropriate handler based on callback data
        if query.data == "show_checkpoints":
            await show_checkpoints(update, context)
        elif query.data == "refresh_all":
            await refresh_all_checkpoints(update, context)
        elif query.data == "force_refresh":
            await force_refresh_all(update, context)
        elif query.data == "help":
            await help_command(update, context)
        elif query.data == "about":
            await about_command(update, context)
        elif query.data == "status":
            await status_command(update, context)
        elif query.data.startswith("checkpoint:"):
            await checkpoint_detail(update, context)
        elif query.data.startswith("refresh:"):
            await refresh_checkpoint(update, context)
        elif query.data.startswith("force_refresh:"):
            await force_refresh_checkpoint(update, context)
        elif query.data.startswith("location:"):
            await show_location(update, context)
        else:
            await query.answer("Unknown command")
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        try:
            # Safely notify the user of the error
            await query.answer(f"Error: {str(e)[:200]}")
            # Only try to edit message if it has text content
            if query.message and query.message.text:
                await query.edit_message_text(
                    text=f"❌ Something went wrong.\n\nUse /checkpoints to start over.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Show Checkpoints", callback_data="show_checkpoints")
                    ]])
                )
        except Exception:
            # If even the error handler fails, just log it
            logger.exception("Error in error handler")

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input by suggesting to use buttons instead."""
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Get the first name of the user if available
    user_first_name = update.effective_user.first_name if update.effective_user else "there"
    
    await update.message.reply_text(
        f"👋 Hi {user_first_name}! This bot works with buttons only.\n\n"
        "I don't understand text messages. Please use the buttons below or these commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show help information\n"
        "/checkpoints - Show available checkpoints\n"
        "/about - Information about this bot\n"
        "/status - Check API connection status",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Show Checkpoints", callback_data="show_checkpoints"),
                InlineKeyboardButton("Help", callback_data="help")
            ],
            [
                InlineKeyboardButton("About", callback_data="about"),
                InlineKeyboardButton("Check Status", callback_data="status")
            ]
        ])
    )

def main() -> None:
    """Start the bot."""
    # Check API access at startup
    api_status = check_api_access()
    if not api_status:
        logger.warning("Could not access LTA API during startup. The bot will still run, but may not function correctly.")
    
    # Create the Application
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("checkpoints", show_checkpoints))
    application.add_handler(CommandHandler("status", status_command))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add handler for text messages (to ignore keyboard input)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 