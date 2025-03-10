await status_message.edit_text("Encoding failed. Please try again with a different video.")
            return ConversationHandler.END
        
        # Apply custom thumbnail if provided
        if user_data.get("thumbnail_path"):
            thumb_cmd = [
                'ffmpeg',
                '-i', output_filename,
                '-i', user_data["thumbnail_path"],
                '-map', '0',
                '-map', '1',
                '-c', 'copy',
                '-disposition:v:1', 'attached_pic',
                f"encoded/temp_{user_data['new_filename']}"
            ]
            
            thumb_process = subprocess.Popen(
                thumb_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            thumb_stdout, thumb_stderr = thumb_process.communicate()
            
            if thumb_process.returncode == 0:
                os.replace(f"encoded/temp_{user_data['new_filename']}", output_filename)
        
        # Send the encoded video back to user
        await status_message.edit_text(f"Encoding completed! Uploading {user_data['quality']} video...")
        
        # Create thumbnail for Telegram
        thumbnail_file = None
        if user_data.get("thumbnail_path"):
            thumbnail_file = open(user_data["thumbnail_path"], "rb")
        
        with open(output_filename, "rb") as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                thumb=thumbnail_file,
                filename=user_data["new_filename"],
                caption=f"Encoded to {user_data['quality']}"
            )
            
        if thumbnail_file:
            thumbnail_file.close()
            
        # Clean up
        try:
            os.remove(user_data["download_path"])
            os.remove(output_filename)
            if user_data.get("thumbnail_path"):
                os.remove(user_data["thumbnail_path"])
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
        
        # Clean up user data
        del user_data_store[user_id]
        
        await status_message.edit_text("Video processing completed! Send me another video to process.")
        
    except Exception as e:
        logger.error(f"Error in encoding process: {e}")
        await status_message.edit_text("An error occurred during processing. Please try again.")
    
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.VIDEO | filters.Document.VIDEO, receive_video)],
        states={
            CHOOSE_QUALITY: [CallbackQueryHandler(quality_selection)],
            RENAME: [MessageHandler(filters.TEXT, rename_file)],
            THUMBNAIL: [
                MessageHandler(filters.PHOTO, receive_thumbnail),
                MessageHandler(filters.Regex("^/skip$"), receive_thumbnail)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    
    # Start the Bot
    application.run_polling()

if name == "main":
    main()