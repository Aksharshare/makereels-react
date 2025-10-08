#!/usr/bin/env python3
"""
Video Orientation Detection Module
Detects if a video is horizontal (landscape) or vertical (portrait)
"""

import cv2
import json
from pathlib import Path
from moviepy.editor import VideoFileClip

def detect_video_orientation(video_path):
    """
    Detect if a video is horizontal (landscape) or vertical (portrait)
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        str: 'horizontal' or 'vertical'
    """
    try:
        # Method 1: Using OpenCV (faster)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return 'unknown'
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Determine orientation based on aspect ratio
        aspect_ratio = width / height
        
        print(f"Video dimensions: {width}x{height} (aspect ratio: {aspect_ratio:.2f})")
        
        # Horizontal if width > height (aspect ratio > 1.0)
        if aspect_ratio > 1.0:
            print("📱 Detected: HORIZONTAL video (landscape)")
            return 'horizontal'
        else:
            print("📱 Detected: VERTICAL video (portrait)")
            return 'vertical'
            
    except Exception as e:
        print(f"Error detecting orientation: {str(e)}")
        # Fallback: Try with MoviePy
        try:
            clip = VideoFileClip(video_path)
            width, height = clip.size
            clip.close()
            
            aspect_ratio = width / height
            print(f"Fallback detection - Video dimensions: {width}x{height} (aspect ratio: {aspect_ratio:.2f})")
            
            if aspect_ratio > 1.0:
                print("📱 Fallback detected: HORIZONTAL video (landscape)")
                return 'horizontal'
            else:
                print("📱 Fallback detected: VERTICAL video (portrait)")
                return 'vertical'
                
        except Exception as e2:
            print(f"Error in fallback detection: {str(e2)}")
            return 'unknown'

def get_orientation_config():
    """Get orientation detection configuration from master_config.json"""
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config" / "master_config.json"
    
    fallback_paths = [
        config_path,
        Path("/app/config/master_config.json"),  # Docker container path
        Path("config/master_config.json"),     # Relative path
        Path("./config/master_config.json")     # Current directory relative
    ]
    
    for path in fallback_paths:
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('orientation_detection', {
                        'enabled': True,
                        'horizontal_threshold': 1.0
                    })
        except Exception as e:
            print(f"Warning: Could not load orientation config from {path}: {e}")
            continue
    
    print("Warning: Could not load orientation config from any path, using defaults")
    return {'enabled': True, 'horizontal_threshold': 1.0}

def is_horizontal_video(video_path):
    """
    Check if video is horizontal with configurable threshold
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        bool: True if horizontal, False if vertical
    """
    config = get_orientation_config()
    
    if not config.get('enabled', True):
        print("Orientation detection is disabled in config")
        return False
    
    orientation = detect_video_orientation(video_path)
    threshold = config.get('horizontal_threshold', 1.0)
    
    # Get actual aspect ratio for threshold comparison
    try:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            aspect_ratio = width / height
            return aspect_ratio > threshold
    except:
        pass
    
    return orientation == 'horizontal'

if __name__ == "__main__":
    # Test the orientation detection
    import sys
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        orientation = detect_video_orientation(video_path)
        is_horizontal = is_horizontal_video(video_path)
        print(f"Final result: {'HORIZONTAL' if is_horizontal else 'VERTICAL'}")
    else:
        print("Usage: python video_orientation.py <video_path>")
