#!/usr/bin/env python3
"""
Horizontal Video Processing Pipeline
For horizontal videos: trim silence → find highlights → crop highlights → add subtitles
"""

import sys
import os
import json
import logging
from pathlib import Path
import subprocess
import shutil

# Add modules to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "modules"))

from video_orientation import is_horizontal_video
from face_tracking import crop_to_vertical, combine_videos, get_face_tracking_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_horizontal_video(input_video_path, output_folder):
    """
    Process horizontal video with the new flow:
    1. Create SRT and JSON files from original video
    2. Trim silence
    3. Find highlights/clips
    4. Crop each highlight to vertical
    5. Add subtitles to each cropped highlight
    6. Clean up and organize final videos
    
    Args:
        input_video_path (str): Path to input horizontal video
        output_folder (str): Path to output folder
        
    Returns:
        dict: Processing results with paths to generated clips
    """
    logger.info("🎬 Starting horizontal video processing pipeline...")
    logger.info(f"Input: {input_video_path}")
    logger.info(f"Output folder: {output_folder}")
    
    # Verify it's actually horizontal
    if not is_horizontal_video(input_video_path):
        logger.warning("⚠️ Video is not horizontal, skipping horizontal processing")
        return {'status': 'skipped', 'reason': 'not_horizontal'}
    
    try:
        # Step 1: Create SRT and JSON files from original video (like vertical workflow)
        logger.info("📝 Step 1: Creating transcription and scoring data from original video...")
        
        # Import transcription handler
        sys.path.append(str(project_root / "modules"))
        from transcription import TranscriptionHandler
        
        # Create transcription handler
        handler = TranscriptionHandler()
        
        # Generate SRT and JSON files from original video
        srt_path = handler.transcribe_video(input_video_path)
        logger.info(f"✅ Transcription completed: {srt_path}")
        
        # Step 2: Trim silence from the horizontal video
        logger.info("🔇 Step 2: Trimming silence from horizontal video...")
        trimmed_video_path = str(Path(output_folder) / f"{Path(input_video_path).stem}_trimmed.mp4")
        
        # Run silence trimming
        trim_command = f'python src/trim_silence.py "{input_video_path}"'
        result = subprocess.run(trim_command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Silence trimming failed: {result.stderr}")
            return {'status': 'error', 'error': 'silence_trimming_failed'}
        
        # Find the trimmed video (trim_silence.py creates it in processed subfolder)
        processed_dir = Path(output_folder) / "processed"
        trimmed_files = list(processed_dir.glob("*_trimmed.mp4"))
        if not trimmed_files:
            logger.error("❌ Trimmed video not found after silence trimming")
            logger.error(f"Looked in: {processed_dir}")
            return {'status': 'error', 'error': 'trimmed_video_not_found'}
        
        # Sort by modification time to get the most recent file
        trimmed_files.sort(key=lambda x: x.stat().st_mtime)
        trimmed_video_path = str(trimmed_files[-1])  # Get most recent file
        logger.info(f"✅ Silence trimmed: {trimmed_video_path}")
        
        # Step 3: Find highlights/clips from the trimmed video
        logger.info("🎯 Step 3: Finding highlights/clips...")
        
        # Run create_shorts.py to find highlights
        shorts_command = 'python src/create_shorts.py'
        result = subprocess.run(shorts_command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Highlight detection failed: {result.stderr}")
            return {'status': 'error', 'error': 'highlight_detection_failed'}
        
        # Find generated short clips (create_shorts.py saves them in shorts subfolder)
        shorts_dir = Path(output_folder) / "shorts"
        
        # Only look for clips from the current video, not all existing clips
        current_video_name = Path(input_video_path).stem
        short_clips = list(shorts_dir.glob(f"{current_video_name}_short_*.mp4"))
        
        if not short_clips:
            logger.error("❌ No short clips found after highlight detection")
            logger.error(f"Looked in: {shorts_dir}")
            logger.error(f"Expected pattern: {current_video_name}_short_*.mp4")
            return {'status': 'error', 'error': 'no_clips_found'}
        
        logger.info(f"✅ Found {len(short_clips)} highlight clips for {current_video_name}")
        
        # Step 4: Crop each highlight to vertical format with face tracking
        logger.info("✂️ Step 4: Cropping highlights to vertical format...")
        
        cropped_clips = []
        for i, clip_path in enumerate(short_clips):
            logger.info(f"📋 Processing clip {i+1}/{len(short_clips)}: {clip_path.name}")
            
            # Create cropped version
            cropped_path = str(Path(output_folder) / f"{clip_path.stem}_cropped.mp4")
            
            # Apply face tracking and cropping
            config = get_face_tracking_config()
            debug_overlay = config.get('debug_overlay', False)
            
            crop_to_vertical(str(clip_path), cropped_path, debug_overlay=debug_overlay)
            
            # Combine with original audio from the clip
            final_cropped_path = str(Path(output_folder) / f"{clip_path.stem}_final.mp4")
            combine_videos(str(clip_path), cropped_path, final_cropped_path)
            
            # Clean up intermediate file
            if os.path.exists(cropped_path):
                os.remove(cropped_path)
            
            cropped_clips.append(final_cropped_path)
            logger.info(f"✅ Cropped clip {i+1}: {final_cropped_path}")
        
        # Step 5: Add subtitles to each cropped clip
        logger.info("📝 Step 5: Adding subtitles to cropped clips...")
        
        subtitled_clips = []
        for i, clip_path in enumerate(cropped_clips):
            logger.info(f"📝 Adding subtitles to clip {i+1}/{len(cropped_clips)}: {Path(clip_path).name}")
            
            # Run subtitle addition
            subtitle_command = f'python src/add_subtitles.py "{clip_path}"'
            result = subprocess.run(subtitle_command, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"⚠️ Subtitle addition failed for clip {i+1}: {result.stderr}")
                # Continue with other clips even if one fails
                subtitled_clips.append(clip_path)  # Use original if subtitle fails
            else:
                # Find the subtitled version
                subtitled_files = list(Path(output_folder).glob(f"{Path(clip_path).stem}_with_subs.mp4"))
                if subtitled_files:
                    subtitled_clips.append(str(subtitled_files[0]))
                    logger.info(f"✅ Subtitles added to clip {i+1}")
                else:
                    subtitled_clips.append(clip_path)  # Use original if subtitle file not found
                    logger.warning(f"⚠️ Subtitle file not found for clip {i+1}, using original")
        
        # Step 6: Clean up and organize final videos
        logger.info("🧹 Step 6: Cleaning up and organizing final videos...")
        
        # Create shorts directory if it doesn't exist
        shorts_dir = Path(output_folder) / "shorts"
        shorts_dir.mkdir(parents=True, exist_ok=True)
        
        # Move final videos to shorts folder and clean up
        final_videos = []
        for i, clip_path in enumerate(subtitled_clips):
            # Get the original video name for consistent naming
            original_video_name = Path(input_video_path).stem
            final_name = f"{original_video_name}_short_{i+1}.mp4"
            final_path = shorts_dir / final_name
            
            # Move the final video to shorts folder
            shutil.move(clip_path, final_path)
            final_videos.append(str(final_path))
            logger.info(f"📁 Moved final video {i+1}: {final_name}")
        
        # Clean up intermediate files
        logger.info("🗑️ Cleaning up intermediate files...")
        
        # Clean up cropped clips (without subtitles)
        for clip_path in cropped_clips:
            if os.path.exists(clip_path):
                os.remove(clip_path)
                logger.info(f"🗑️ Removed: {Path(clip_path).name}")
        
        # Clean up original shorts from output folder (not shorts folder)
        for clip_path in short_clips:
            # Only remove if it's still in the output folder, not in shorts folder
            if os.path.exists(clip_path) and "shorts" not in str(clip_path):
                os.remove(clip_path)
                logger.info(f"🗑️ Removed: {Path(clip_path).name}")
        
        # Clean up any remaining intermediate files in shorts folder
        # Remove files with double underscore pattern (intermediate files)
        for file_path in shorts_dir.glob("*_short__*.mp4"):
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Removed intermediate from shorts: {file_path.name}")
        
        # Only clean up intermediate files with double underscore pattern
        # Don't remove files from other videos - they should be preserved
        
        # Clean up any other intermediate files in output folder
        output_path = Path(output_folder)
        for file_path in output_path.glob("*_final.mp4"):
            if not file_path.name.endswith("_with_subs.mp4"):
                os.remove(file_path)
                logger.info(f"🗑️ Removed intermediate: {file_path.name}")
        
        logger.info("🎉 Horizontal video processing completed!")
        logger.info(f"📊 Generated {len(final_videos)} final clips in shorts folder")
        
        return {
            'status': 'success',
            'clips': final_videos,
            'shorts_folder': str(shorts_dir)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in horizontal video processing: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python process_horizontal_video.py <input_video_path> [output_folder]")
        sys.exit(1)
    
    input_video_path = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else "app/output"
    
    # Ensure output folder exists
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    result = process_horizontal_video(input_video_path, output_folder)
    
    if result['status'] == 'success':
        print(f"✅ Successfully processed horizontal video!")
        print(f"📁 Generated {len(result['clips'])} clips:")
        for i, clip in enumerate(result['clips']):
            print(f"  {i+1}. {clip}")
    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
