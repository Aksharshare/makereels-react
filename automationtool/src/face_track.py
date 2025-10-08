#!/usr/bin/env python3
"""
Face Tracking Integration Script for Automation Tool
This script integrates face tracking functionality into the automation pipeline.
"""

import sys
import os
from pathlib import Path
import logging

# Docker-optimized path resolution for modules
project_root = Path(__file__).parent.parent
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

from face_tracking import process_video_with_face_tracking, get_face_tracking_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to process video with face tracking.
    This can be called from the pipeline or run standalone.
    """
    if len(sys.argv) < 2:
        print("Usage: python face_tracking_integration.py <input_video_path> [output_video_path]")
        sys.exit(1)
    
    input_video_path = sys.argv[1]
    output_video_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not output_video_path:
        # Generate output path based on input
        input_path = Path(input_video_path)
        output_video_path = str(input_path.parent / f"{input_path.stem}_face_tracked.mp4")
    
    # Check if face tracking is enabled in config
    config = get_face_tracking_config()
    if not config.get('enabled', False):
        logger.warning("Face tracking is disabled in config. Skipping face tracking processing.")
        return
    
    logger.info(f"Processing video with face tracking: {input_video_path}")
    logger.info(f"Output will be saved to: {output_video_path}")
    logger.info(f"Debug overlay: {'Enabled' if config.get('debug_overlay', False) else 'Disabled'}")
    
    try:
        # Process video with face tracking
        process_video_with_face_tracking(
            input_video_path=input_video_path,
            output_video_path=output_video_path,
            final_video_path=None  # We'll handle audio separately in the pipeline
        )
        logger.info("Face tracking processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during face tracking processing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
