import cv2
import numpy as np
from moviepy.editor import *
import os
import warnings
import json
from pathlib import Path

# Suppress MoviePy warnings about FFmpeg
warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")

def get_face_tracking_config():
    """Get face tracking configuration from master_config.json with Docker-optimized paths"""
    # Docker-optimized path resolution
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config" / "master_config.json"
    
    # Fallback paths for different deployment scenarios
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
                    return config.get('face_tracking', {
                        'enabled': False,
                        'debug_overlay': False
                    })
        except Exception as e:
            print(f"Warning: Could not load face tracking config from {path}: {e}")
            continue
    
    print("Warning: Could not load face tracking config from any path, using defaults")
    return {'enabled': False, 'debug_overlay': False}

def crop_to_vertical(input_video_path, output_video_path, debug_overlay=None):
    """
    Crop video to vertical format (9:16) with face tracking and strict 2-second rule.
    
    Args:
        input_video_path (str): Path to input video
        output_video_path (str): Path to output video
        debug_overlay (bool, optional): Whether to add debug overlay to video. 
                                       If None, will use config setting.
    """
    # Get debug overlay setting from config if not specified
    if debug_overlay is None:
        config = get_face_tracking_config()
        debug_overlay = config.get('debug_overlay', False)
    # STRICT 2-second rule: Only switch after current speaker has been active for 2+ seconds
    cap = cv2.VideoCapture(input_video_path, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate vertical dimensions (9:16 aspect ratio)
    vertical_height = int(original_height)
    vertical_width = int(vertical_height * 9 / 16)
    
    print(f"Original: {original_width}x{original_height}")
    print(f"Vertical: {vertical_width}x{vertical_height}")

    if original_width < vertical_width:
        print("Error: Original video width is less than the desired vertical width.")
        return

    # Load face cascade - Docker-optimized path resolution
    cascade_paths = [
        Path(__file__).parent / "haarcascade_frontalface_default.xml",  # Local modules directory
        Path("/app/modules/haarcascade_frontalface_default.xml"),       # Docker container path
        Path("modules/haarcascade_frontalface_default.xml"),             # Relative path
        Path("./modules/haarcascade_frontalface_default.xml"),          # Current directory relative
        Path(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')  # OpenCV default
    ]
    
    face_cascade = None
    for cascade_path in cascade_paths:
        try:
            if cascade_path.exists():
                face_cascade = cv2.CascadeClassifier(str(cascade_path))
                print(f"Using haarcascade from: {cascade_path}")
                break
        except Exception as e:
            print(f"Warning: Could not load cascade from {cascade_path}: {e}")
            continue
    
    if face_cascade is None:
        print("Error: Could not find haarcascade file in any location")
        return

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (vertical_width, vertical_height))
    print(f"Processing {total_frames} frames at {fps} FPS")

    # STRICT 2-second rule variables
    current_speaker_center = original_width // 2  # Start with center
    face_center_history = []
    
    # STRICT 2-second rule: Current speaker must be active for 2+ seconds
    speaker_start_frame = 0
    speaker_duration_frames = 0
    min_speaker_duration = int(fps * 2)  # EXACTLY 2 seconds as discussed
    
    # Additional guardrails to prevent quick switches
    face_detection_history = []
    last_switch_frame = 0
    min_switch_interval = int(fps * 2)  # 2 seconds between switches (guardrail)
    
    # Speaker counting variables
    speaker_count_history = []
    total_speakers_detected = 0
    frame_speaker_counts = []
    
    # Track consecutive frames without faces
    no_face_frames = 0
    max_no_face_frames = int(fps * 3)  # Allow 3 seconds without faces before resetting
    
    count = 0
    for _ in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            print(f"Error: Could not read frame {count}")
            break

        # Face detection with filtering
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.2,
            minNeighbors=8,
            minSize=(60, 60),
            maxSize=(350, 350),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Filter out false positives
        filtered_faces = []
        for (x, y, w, h) in faces:
            aspect_ratio = w / h
            if 0.7 <= aspect_ratio <= 1.3:
                if x > 30 and y > 30 and x + w < original_width - 30 and y + h < original_height - 30:
                    face_area = w * h
                    frame_area = original_width * original_height
                    if 0.001 <= face_area / frame_area <= 0.25:
                        face_center_y = y + h // 2
                        if face_center_y < original_height * 0.7:
                            filtered_faces.append((x, y, w, h))
        
        # Additional filtering: remove faces that are too close together
        final_faces = []
        for i, (x1, y1, w1, h1) in enumerate(filtered_faces):
            is_valid = True
            for j, (x2, y2, w2, h2) in enumerate(filtered_faces):
                if i != j:
                    center1_x, center1_y = x1 + w1 // 2, y1 + h1 // 2
                    center2_x, center2_y = x2 + w2 // 2, y2 + h2 // 2
                    distance = np.sqrt((center1_x - center2_x)**2 + (center1_y - center2_y)**2)
                    
                    if distance < 100:
                        area1 = w1 * h1
                        area2 = w2 * h2
                        if area1 < area2:
                            is_valid = False
                            break
            
            if is_valid:
                final_faces.append((x1, y1, w1, h1))
        
        faces = final_faces
        current_face_center = current_speaker_center  # Default to current speaker
        
        if len(faces) > 0:
            # Reset no-face counter
            no_face_frames = 0
            
            # Count speakers in this frame
            current_speaker_count = len(faces)
            frame_speaker_counts.append(current_speaker_count)
            
            # Track unique speaker counts
            if current_speaker_count not in speaker_count_history:
                speaker_count_history.append(current_speaker_count)
                total_speakers_detected = max(speaker_count_history)
                print(f"Frame {count}: New speaker count detected: {current_speaker_count} speakers")
            
            # Log speaker count every 30 frames
            if count % 30 == 0:
                print(f"Frame {count}: {current_speaker_count} speakers detected")
            
            # Find the largest face (most prominent)
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = largest_face
            detected_face_center = x + w // 2
            
            # STRICT 2-SECOND RULE: Only switch if current speaker has been active for 2+ seconds
            face_distance = abs(detected_face_center - current_speaker_center)
            is_significant_change = face_distance > 120
            
            # STRICT rule: Current speaker must be active for EXACTLY 2+ seconds
            time_since_last_switch = count - last_switch_frame
            can_switch = (time_since_last_switch >= min_switch_interval and 
                         speaker_duration_frames >= min_speaker_duration)
            
            if is_significant_change and can_switch:
                # STRICT: Only switch after 2+ seconds of current speaker
                current_speaker_center = detected_face_center
                speaker_start_frame = count
                speaker_duration_frames = 0
                last_switch_frame = count
                print(f"Frame {count}: STRICT 2-SEC RULE: Switching to new speaker at position {detected_face_center} (current speaker was active for {speaker_duration_frames/fps:.1f}s)")
            elif is_significant_change:
                # STRICT: Keep current speaker, ignore new face (2-second rule not satisfied)
                current_face_center = current_speaker_center
                remaining_time = (min_speaker_duration - speaker_duration_frames) / fps
                print(f"Frame {count}: STRICT 2-SEC RULE: Ignoring new speaker (current speaker needs {remaining_time:.1f}s more)")
            else:
                # Small movement, update current speaker position smoothly
                current_speaker_center = int(0.8 * current_speaker_center + 0.2 * detected_face_center)
                current_face_center = current_speaker_center
            
            # Update speaker duration
            speaker_duration_frames += 1
            face_center_history.append(current_face_center)
            face_detection_history.append(detected_face_center)
            
            # Keep only last 10 face positions for smoothing
            if len(face_center_history) > 10:
                face_center_history.pop(0)
            if len(face_detection_history) > 20:
                face_detection_history.pop(0)
        else:
            # No face detected - STRICT: Still count time for current speaker
            no_face_frames += 1
            speaker_duration_frames += 1  # Still count time for current speaker
            
            # Use history intelligently
            if len(face_center_history) > 0:
                # Use recent history to maintain position
                recent_positions = face_center_history[-5:] if len(face_center_history) >= 5 else face_center_history
                current_face_center = sum(recent_positions) // len(recent_positions)
                
                # If too many frames without faces, gradually move to center
                if no_face_frames > max_no_face_frames:
                    center_x = original_width // 2
                    current_face_center = int(0.9 * current_face_center + 0.1 * center_x)
                    print(f"Frame {count}: No faces for {no_face_frames} frames, gradually moving to center")
                else:
                    print(f"Frame {count}: No faces detected, using history (frames without face: {no_face_frames})")
            else:
                # No history, use center
                current_face_center = current_speaker_center
                print(f"Frame {count}: No faces and no history, using current speaker center")

        # Calculate crop position centered on face
        x_start = current_face_center - vertical_width // 2
        x_end = x_start + vertical_width
        
        # Ensure crop stays within bounds
        if x_start < 0:
            x_start = 0
            x_end = vertical_width
        elif x_end > original_width:
            x_end = original_width
            x_start = original_width - vertical_width

        # Crop the frame
        cropped_frame = frame[:, x_start:x_end]
        
        # Ensure frame has correct dimensions
        if cropped_frame.shape[1] != vertical_width:
            center_x = original_width // 2
            x_start = center_x - vertical_width // 2
            x_end = x_start + vertical_width
            cropped_frame = frame[:, x_start:x_end]
        
        # Resize if needed to ensure correct dimensions
        if cropped_frame.shape[:2] != (vertical_height, vertical_width):
            cropped_frame = cv2.resize(cropped_frame, (vertical_width, vertical_height))
        
        # DEBUG: Add frame number and face center info to video (only if debug enabled)
        if debug_overlay:
            debug_text = f"Frame: {count}"
            debug_text2 = f"Face Center: {current_face_center}"
            debug_text3 = f"Crop: {x_start}-{x_end}"
            debug_text4 = f"Speakers: {len(faces) if len(faces) > 0 else 0}"
            debug_text5 = f"Speaker Time: {speaker_duration_frames/fps:.1f}s"
            debug_text6 = f"2-Sec Rule: {'SATISFIED' if speaker_duration_frames >= min_speaker_duration else 'PENDING'}"
            
            # Add text overlay
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.4
            color = (0, 255, 0)  # Green
            thickness = 1
            
            # Position text at top of frame
            cv2.putText(cropped_frame, debug_text, (10, 15), font, font_scale, color, thickness)
            cv2.putText(cropped_frame, debug_text2, (10, 30), font, font_scale, color, thickness)
            cv2.putText(cropped_frame, debug_text3, (10, 45), font, font_scale, color, thickness)
            cv2.putText(cropped_frame, debug_text4, (10, 60), font, font_scale, color, thickness)
            cv2.putText(cropped_frame, debug_text5, (10, 75), font, font_scale, color, thickness)
            cv2.putText(cropped_frame, debug_text6, (10, 90), font, font_scale, color, thickness)
            
            # Add visual debugging for detected faces
            if len(faces) > 0:
                # Draw rectangles around all detected faces in the cropped frame
                for i, (fx, fy, fw, fh) in enumerate(faces):
                    # Convert face coordinates to crop coordinates
                    face_x_in_crop = fx - x_start
                    face_y_in_crop = fy
                    face_w_in_crop = fw
                    face_h_in_crop = fh
                    
                    # Only draw if face is within crop bounds
                    if (face_x_in_crop >= 0 and face_x_in_crop + face_w_in_crop <= vertical_width and
                        face_y_in_crop >= 0 and face_y_in_crop + face_h_in_crop <= vertical_height):
                        
                        # Draw rectangle around face
                        color = (0, 255, 0) if i == 0 else (255, 0, 0)  # Green for primary, red for others
                        cv2.rectangle(cropped_frame, 
                                    (int(face_x_in_crop), int(face_y_in_crop)), 
                                    (int(face_x_in_crop + face_w_in_crop), int(face_y_in_crop + face_h_in_crop)), 
                                    color, 2)
                        
                        # Add face number label
                        cv2.putText(cropped_frame, f"Face {i+1}", 
                                  (int(face_x_in_crop), int(face_y_in_crop) - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
            
            # Add a small indicator showing current speaker position
            if current_face_center > 0:
                # Draw a small circle at the face center position (scaled to crop)
                indicator_x = int((current_face_center - x_start) * vertical_width / (x_end - x_start))
                if 0 <= indicator_x < vertical_width:
                    cv2.circle(cropped_frame, (indicator_x, vertical_height - 30), 8, (0, 0, 255), -1)  # Red circle
        
        out.write(cropped_frame)
        count += 1
        
        if count % 30 == 0:  # Progress indicator
            print(f"Processed {count}/{total_frames} frames (face center: {current_face_center})")

    cap.release()
    out.release()
    
    # Print speaker detection summary
    print(f"\n=== SPEAKER DETECTION SUMMARY ===")
    print(f"Total frames processed: {count}")
    print(f"Unique speaker counts detected: {speaker_count_history}")
    print(f"Maximum speakers detected in any frame: {max(frame_speaker_counts) if frame_speaker_counts else 0}")
    print(f"Average speakers per frame: {sum(frame_speaker_counts)/len(frame_speaker_counts) if frame_speaker_counts else 0:.1f}")
    print(f"Frames with 1 speaker: {frame_speaker_counts.count(1)}")
    print(f"Frames with 2 speakers: {frame_speaker_counts.count(2)}")
    print(f"Frames with 3+ speakers: {sum(1 for x in frame_speaker_counts if x >= 3)}")
    
    print("Cropping complete. The video has been saved to", output_video_path, count)

def combine_videos(video_with_audio, video_without_audio, output_filename):
    """
    Combine video with audio from another video.
    
    Args:
        video_with_audio (str): Path to video with audio
        video_without_audio (str): Path to video without audio
        output_filename (str): Path to output combined video
    """
    clip_with_audio = None
    clip_without_audio = None
    combined_clip = None
    
    try:
        clip_with_audio = VideoFileClip(video_with_audio)
        clip_without_audio = VideoFileClip(video_without_audio)
        audio = clip_with_audio.audio
        combined_clip = clip_without_audio.set_audio(audio)
        
        # Get FPS from the video clip
        fps = clip_without_audio.fps
        combined_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac', fps=fps, preset='medium', bitrate='3000k')
        print(f"Combined video saved successfully as {output_filename}")
        
    except Exception as e:
        print(f"Error combining video and audio: {str(e)}")
    finally:
        # Properly close all clips to prevent FFmpeg handle issues
        if combined_clip:
            combined_clip.close()
        if clip_without_audio:
            clip_without_audio.close()
        if clip_with_audio:
            clip_with_audio.close()

def process_video_with_face_tracking(input_video_path, output_video_path, final_video_path=None):
    """
    Process video with face tracking and vertical cropping.
    
    Args:
        input_video_path (str): Path to input video
        output_video_path (str): Path to output cropped video
        final_video_path (str, optional): Path to final video with audio
    """
    print(f"Starting face tracking processing for: {input_video_path}")
    
    # Crop to vertical format with face tracking
    crop_to_vertical(input_video_path, output_video_path)
    
    # If final path is provided, combine with original audio
    if final_video_path:
        combine_videos(input_video_path, output_video_path, final_video_path)
        print(f"Face tracking processing complete. Output saved to: {final_video_path}")
    else:
        print(f"Face tracking processing complete. Output saved to: {output_video_path}")

if __name__ == "__main__":
    # Example usage
    input_video_path = r'input_video.mp4'
    output_video_path = 'cropped_output_video.mp4'
    final_video_path = 'final_video_with_audio.mp4'
    
    process_video_with_face_tracking(input_video_path, output_video_path, final_video_path)
