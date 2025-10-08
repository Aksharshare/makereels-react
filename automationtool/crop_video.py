#!/usr/bin/env python3
"""
Process entire video with face tracking - skip AI highlight generation
Adapted for automationtool structure
"""

import shutil
import os
import sys
import warnings
from pathlib import Path

# Suppress MoviePy warnings
warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")

# Docker-optimized path resolution for modules
project_root = Path(__file__).parent
modules_paths = [
    project_root / "modules",           # Local development
    Path("/app/modules"),               # Docker container path
    Path("modules"),                    # Relative path
    Path("./modules")                   # Current directory relative
]

for modules_path in modules_paths:
    if modules_path.exists():
        sys.path.append(str(modules_path))
        break

from face_tracking import crop_to_vertical, combine_videos, get_face_tracking_config

def process_entire_video_with_face_tracking(input_video_path=None, output_video_path=None):
    """
    Process entire video with face tracking.
    
    Args:
        input_video_path (str, optional): Path to input video. If None, will look in input directory.
        output_video_path (str, optional): Path to output video. If None, will generate based on input.
    """
    # If no input path provided, look in the input directory
    if not input_video_path:
        input_dir = Path(__file__).parent / "input"
        if not input_dir.exists():
            print("❌ No input directory found and no input video specified")
            return
        
        # Find the first video file in input directory
        video_files = [f for f in input_dir.glob("*.mp4")] + [f for f in input_dir.glob("*.mov")] + [f for f in input_dir.glob("*.avi")]
        if not video_files:
            print("❌ No video files found in input directory")
            return
        
        input_video_path = str(video_files[0])
    
    # Generate output path if not provided
    if not output_video_path:
        input_path = Path(input_video_path)
        output_video_path = str(input_path.parent / f"{input_path.stem}_face_tracked_full.mp4")
    
    print("🎬 Processing entire video with face tracking...")
    print(f"Input: {input_video_path}")
    print(f"Output: {output_video_path}")
    
    # Create a temporary copy for processing
    temp_video = "temp_processing_video.mp4"
    print("📋 Creating temporary copy for processing...")
    shutil.copy2(input_video_path, temp_video)
    print(f"✅ Copied to {temp_video}")
    
    # Apply face tracking to the entire video
    print("👤 Applying face tracking to entire video...")
    face_tracked_video = "temp_face_tracked_video.mp4"
    
    # Get debug overlay setting from config
    config = get_face_tracking_config()
    debug_overlay = config.get('debug_overlay', False)
    
    crop_to_vertical(temp_video, face_tracked_video, debug_overlay=debug_overlay)
    print("✅ Face tracking complete!")
    
    # Combine with original audio
    print("🔊 Combining with original audio...")
    combine_videos(input_video_path, face_tracked_video, output_video_path)
    
    # Clean up temporary files
    print("🗑️ Cleaning up temporary files...")
    if os.path.exists(temp_video):
        os.remove(temp_video)
    if os.path.exists(face_tracked_video):
        os.remove(face_tracked_video)
    
    print("🎉 Complete!")
    print(f"📁 Output: {output_video_path}")
    print("📱 Ready for YouTube Shorts upload!")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) > 1:
        input_video = sys.argv[1]
        output_video = sys.argv[2] if len(sys.argv) > 2 else None
        process_entire_video_with_face_tracking(input_video, output_video)
    else:
        process_entire_video_with_face_tracking()

if __name__ == "__main__":
    main()
