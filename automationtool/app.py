import os
import sys
import json
import subprocess
import traceback
import time
import threading
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, render_template, send_from_directory, redirect, url_for
from flask_cors import CORS
import logging

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

app = Flask(__name__)

# Enable CORS for frontend communication
CORS(app, origins=['http://localhost:3000', 'https://makereels.live'])

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage for processing status
processing_status = {}

# Global storage for background processing
background_tasks = {}

def process_video_background(task_id, filename):
    """Process video in background thread"""
    try:
        background_tasks[task_id] = {
            'status': 'PROCESSING',
            'message': 'Starting video processing...',
            'progress': 0
        }
        
        logger.info(f"🔍 Starting background processing for task {task_id}: {filename}")
        result = process_video_direct(filename)
        
        if result['status'] == 'SUCCESS':
            background_tasks[task_id] = {
                'status': 'SUCCESS',
                'message': 'Video processed successfully!',
                'progress': 100,
                'result': result
            }
        else:
            background_tasks[task_id] = {
                'status': 'FAILURE',
                'message': 'Video processing failed',
                'progress': 100,
                'error': result.get('error', 'Unknown error')
            }
            
    except Exception as e:
        logger.error(f"❌ Background processing error for task {task_id}: {str(e)}")
        background_tasks[task_id] = {
            'status': 'FAILURE',
            'message': 'Processing failed',
            'progress': 100,
            'error': str(e)
        }

# Import the video processing function from run_pipeline
def process_video_direct(filename):
    """Process video directly without Celery"""
    try:
        # Clear previous logs and old output files
        clear_pipeline_logs()
        
        # Get paths from config
        input_folder, output_folder = get_config_paths()
        
        # Clean up old output files to avoid confusion
        output_dir = Path(output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        for old_file in output_dir.glob('*.mp4'):
            try:
                old_file.unlink()
                logger.info(f"🗑️ Removed old output file: {old_file.name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove old file {old_file.name}: {str(e)}")
        
        # Create input directory
        input_dir = Path(input_folder)
        input_dir.mkdir(exist_ok=True)
        
        # Check if file exists first
        file_path = input_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        logger.info(f"File found: {file_path}")
        
        # Clean up old input files (but keep the current one)
        for old_file in input_dir.glob('*'):
            if old_file.name != filename:  # Don't delete the current file
                try:
                    old_file.unlink()
                    logger.info(f"🗑️ Removed old input file: {old_file.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not remove old file {old_file.name}: {str(e)}")
        
        # Run the pipeline
        result = subprocess.run(
            ['python', 'run_pipeline.py'],
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minute timeout
            cwd=Path(__file__).parent  # Run from the automationtool directory
        )
        
        if result.returncode == 0:
            # Get video base name (e.g., "test1min" from "test1min.mov")
            video_base_name = Path(filename).stem
            
            # Scan for short clips that match this video's pattern
            _, output_folder = get_config_paths()
            output_dir = Path(output_folder)
            
            # DEBUG: Log the paths being searched
            logger.info(f"🔍 DEBUG: Looking for shorts in output_dir: {output_dir}")
            logger.info(f"🔍 DEBUG: Video base name: {video_base_name}")
            logger.info(f"🔍 DEBUG: Pattern: {video_base_name}_short_*.mp4")
            
            # Find all short clips for this specific video
            short_clips = []
            pattern = f"{video_base_name}_short_*.mp4"
            
            # DEBUG: List all files in output directory
            logger.info(f"🔍 DEBUG: All files in output_dir:")
            for item in output_dir.rglob("*"):
                if item.is_file():
                    logger.info(f"🔍 DEBUG: Found file: {item}")
            
            # Look in main output directory first
            for clip_file in output_dir.glob(pattern):
                if clip_file.is_file():
                    short_clips.append({
                        'filename': clip_file.name,
                        'size': round(clip_file.stat().st_size / (1024 * 1024), 2)  # Size in MB
                    })
                    logger.info(f"🔍 DEBUG: Found short in main dir: {clip_file}")
            
            # Also look in shorts subdirectory
            shorts_dir = output_dir / "shorts"
            logger.info(f"🔍 DEBUG: Checking shorts subdirectory: {shorts_dir}")
            if shorts_dir.exists():
                logger.info(f"🔍 DEBUG: Shorts directory exists, listing contents:")
                for item in shorts_dir.rglob("*"):
                    if item.is_file():
                        logger.info(f"🔍 DEBUG: Found file in shorts dir: {item}")
                
                for clip_file in shorts_dir.glob(pattern):
                    if clip_file.is_file():
                        short_clips.append({
                            'filename': clip_file.name,
                            'size': round(clip_file.stat().st_size / (1024 * 1024), 2)  # Size in MB
                        })
                        logger.info(f"🔍 DEBUG: Found short in shorts dir: {clip_file}")
            else:
                logger.info(f"🔍 DEBUG: Shorts directory does not exist: {shorts_dir}")
            
            # Sort clips by name (short_1, short_2, etc.)
            short_clips.sort(key=lambda x: x['filename'])
            
            logger.info(f"🎬 Found {len(short_clips)} short clips for video: {video_base_name}")
            
            # Clean up input file after successful processing
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"🗑️ Cleaned up input file after successful processing: {filename}")
            except Exception as e:
                logger.warning(f"⚠️ Could not clean up input file {filename}: {str(e)}")
            
            # Return only short clips with proper URLs
            short_clips_with_urls = []
            for clip in short_clips:
                # Check if clip is in shorts subdirectory
                clip_path = output_dir / "shorts" / clip['filename']
                if clip_path.exists():
                    url = f'/output/shorts/{clip["filename"]}'
                else:
                    url = f'/output/{clip["filename"]}'
                
                short_clips_with_urls.append({
                    'filename': clip['filename'],
                    'url': url,
                    'size': clip['size']
                })
            
            return {
                'status': 'SUCCESS',
                'message': f'Video processed successfully! Generated {len(short_clips)} short clips.',
                'short_clips': short_clips_with_urls,
                'video_base_name': video_base_name,
                'stdout': result.stdout,
                'file': str(file_path)
            }
        else:
            # Log detailed error information
            logger.error("❌ Pipeline processing failed:")
            logger.error(f"Return code: {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            
            return {
                'status': 'FAILURE',
                'error': 'Pipeline processing failed',
                'details': result.stderr,
                'return_code': result.returncode,
                'stdout': result.stdout
            }
            
    except subprocess.TimeoutExpired as e:
        logger.error(f"❌ Processing timeout: {str(e)}")
        return {
            'status': 'FAILURE',
            'error': 'Processing timeout - video may be too large',
            'message': 'Try with a smaller video file'
        }
        
    except Exception as e:
        # Add traceback to logs for detailed error information
        logger.error("❌ Processing error occurred:")
        logger.error(f"Error: {str(e)}")
        logger.error("Full traceback:")
        traceback.print_exc()
        
        return {
            'status': 'FAILURE',
            'error': 'Processing failed',
            'details': str(e)
        }

def clear_pipeline_logs():
    """Clear pipeline logs before processing a new video"""
    try:
        log_file = Path('pipeline.log')
        if log_file.exists():
            log_file.unlink()
            logger.info("🗑️ Cleared previous pipeline logs")
    except Exception as e:
        logger.warning(f"⚠️ Could not clear logs: {str(e)}")

def get_config_paths():
    """Get input and output paths from config file"""
    try:
        config_path = Path(__file__).parent / "config" / "master_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        input_folder = config.get('input_folder', './input')
        output_folder = config.get('output_folder', './output')
        
        # Normalize paths for the current OS
        input_folder = os.path.normpath(input_folder)
        output_folder = os.path.normpath(output_folder)
        
        logger.info(f"📁 Using configured paths - Input: {input_folder}, Output: {output_folder}")
        
        return input_folder, output_folder
    except Exception as e:
        logger.warning(f"⚠️ Could not read config, using default paths: {str(e)}")
        # Use local development default paths
        return './input', './output'

def validate_environment():
    """Validate that required environment variables and dependencies are available"""
    logger.info("🔍 Validating environment...")
    
    # Check for required environment variables
    required_env_vars = ['PORT']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️ Missing environment variables: {missing_vars}")
    
    # Get paths from config
    input_folder, output_folder = get_config_paths()
    required_dirs = [input_folder, output_folder]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directory ready: {dir_path}")
    
    # Check for ffmpeg availability
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info("✅ ffmpeg is available")
        else:
            logger.error("❌ ffmpeg not working properly")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.error("❌ ffmpeg not found - this will cause pipeline failures")
    
    # Check for Python dependencies
    try:
        import openai
        logger.info("✅ OpenAI library available")
    except ImportError:
        logger.warning("⚠️ OpenAI library not found")
    
    logger.info("🔍 Environment validation complete")

# HTML template for file upload with async processing
UPLOAD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Video Automation Pipeline</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
        .upload-area:hover { border-color: #999; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        .status { margin: 20px 0; padding: 10px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .progress-bar { width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 100%; background-color: #007bff; width: 0%; transition: width 0.3s ease; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; margin-right: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .hidden { display: none; }
        .task-info { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🎬 Video Automation Pipeline</h1>
    <p>Upload a video file to process it through the automation pipeline.</p>
    
    <form id="uploadForm" enctype="multipart/form-data">
        <div class="upload-area">
            <input type="file" name="file" accept=".mp4,.mov,.avi,.mkv" required>
            <p>Select a video file (.mp4, .mov, .avi, .mkv)</p>
        </div>
        <button type="submit" id="submitBtn">📤 Upload Video</button>
    </form>
    
    <div id="phoneForm" class="hidden">
        <h3>📱 Almost there!</h3>
        <p>Please provide your phone number to start processing your video:</p>
        <form id="phoneFormElement">
            <input type="tel" id="phoneNumber" placeholder="Enter your phone number" required>
            <button type="submit" id="phoneSubmitBtn">🚀 Start Processing</button>
        </form>
    </div>
    
    <div id="status"></div>
    
    <script>
        let currentTaskId = null;
        let statusCheckInterval = null;
        
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const statusDiv = document.getElementById('status');
            const submitBtn = document.getElementById('submitBtn');
            
            // Clear previous status
            statusDiv.innerHTML = '';
            
            // Disable submit button and show processing status
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Uploading...';
            statusDiv.innerHTML = '<div class="info">⏳ Uploading video file...</div>';
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    if (result.status === 'UPLOADED') {
                        statusDiv.innerHTML = '<div class="success">✅ Video uploaded successfully!</div>';
                        
                        // Hide upload form and show phone form
                        document.getElementById('uploadForm').style.display = 'none';
                        document.getElementById('phoneForm').classList.remove('hidden');
                        
                        // Reset submit button
                        submitBtn.disabled = false;
                        submitBtn.textContent = '📤 Upload Video';
                    } else {
                        statusDiv.innerHTML = `<div class="error">❌ Upload failed: ${result.error || 'Unknown error'}</div>`;
                        submitBtn.disabled = false;
                        submitBtn.textContent = '📤 Upload Video';
                    }
                } else {
                    statusDiv.innerHTML = `<div class="error">❌ Upload error: ${result.error || 'Unknown error'}</div>`;
                    submitBtn.disabled = false;
                    submitBtn.textContent = '📤 Upload Video';
                }
            } catch (error) {
                console.error('Upload error:', error);
                statusDiv.innerHTML = `<div class="error">❌ Upload error: ${error.message}</div>`;
                submitBtn.disabled = false;
                submitBtn.textContent = '📤 Upload Video';
            }
        });
        
        // Handle phone form submission
        document.getElementById('phoneFormElement').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const phoneNumber = document.getElementById('phoneNumber').value;
            const phoneSubmitBtn = document.getElementById('phoneSubmitBtn');
            const statusDiv = document.getElementById('status');
            
            // Disable submit button and show processing status
            phoneSubmitBtn.disabled = true;
            phoneSubmitBtn.textContent = '⏳ Starting...';
            statusDiv.innerHTML = '<div class="info">⏳ Starting video processing...</div>';
            
            try {
                const response = await fetch('/api/start-processing', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        phone_number: phoneNumber
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    if (result.status === 'PROCESSING') {
                        currentTaskId = result.task_id;
                        statusDiv.innerHTML = '<div class="info">✅ Video processing started! This may take a few minutes...</div>';
                        
                        // Hide phone form
                        document.getElementById('phoneForm').classList.add('hidden');
                        
                        // Start checking status
                        startStatusCheck();
                    } else {
                        statusDiv.innerHTML = `<div class="error">❌ Processing failed to start: ${result.error || 'Unknown error'}</div>`;
                        phoneSubmitBtn.disabled = false;
                        phoneSubmitBtn.textContent = '🚀 Start Processing';
                    }
                } else {
                    statusDiv.innerHTML = `<div class="error">❌ Processing error: ${result.error || 'Unknown error'}</div>`;
                    phoneSubmitBtn.disabled = false;
                    phoneSubmitBtn.textContent = '🚀 Start Processing';
                }
            } catch (error) {
                console.error('Processing error:', error);
                statusDiv.innerHTML = `<div class="error">❌ Processing error: ${error.message}</div>`;
                phoneSubmitBtn.disabled = false;
                phoneSubmitBtn.textContent = '🚀 Start Processing';
            }
        });
        
        function startStatusCheck() {
            if (statusCheckInterval) {
                clearInterval(statusCheckInterval);
            }
            
            statusCheckInterval = setInterval(async () => {
                if (!currentTaskId) return;
                
                try {
                    const response = await fetch(`/task/${currentTaskId}`);
                    const result = await response.json();
                    
                    if (response.ok) {
                        updateStatus(result);
                        
                        if (result.status === 'SUCCESS' || result.status === 'FAILURE') {
                            clearInterval(statusCheckInterval);
                            handleCompletion(result);
                        }
                    }
                } catch (error) {
                    console.error('Error checking task status:', error);
                }
            }, 2000); // Check every 2 seconds
        }
        
        function updateStatus(result) {
            const statusDiv = document.getElementById('status');
            const submitBtn = document.getElementById('submitBtn');
            
            if (result.status === 'PROCESSING') {
                statusDiv.innerHTML = `<div class="info">⏳ ${result.message || 'Processing video...'}</div>`;
            } else if (result.status === 'SUCCESS') {
                statusDiv.innerHTML = '<div class="success">✅ Video processed successfully! Redirecting to result page...</div>';
            } else if (result.status === 'FAILURE') {
                statusDiv.innerHTML = `<div class="error">❌ Processing failed: ${result.error || 'Unknown error'}</div>`;
                // Show upload form again
                document.getElementById('uploadForm').style.display = 'block';
                document.getElementById('phoneForm').classList.add('hidden');
                submitBtn.disabled = false;
                submitBtn.textContent = '📤 Upload Video';
            }
        }
        
        function handleCompletion(result) {
            const statusDiv = document.getElementById('status');
            const submitBtn = document.getElementById('submitBtn');
            
            if (result.status === 'SUCCESS') {
                // Redirect to result page
                setTimeout(() => {
                    window.location.href = `/task/${currentTaskId}/result`;
                }, 2000);
            } else {
                // Show upload form again
                document.getElementById('uploadForm').style.display = 'block';
                document.getElementById('phoneForm').classList.add('hidden');
                submitBtn.disabled = false;
                submitBtn.textContent = '📤 Upload Video';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page with file upload form"""
    return render_template_string(UPLOAD_TEMPLATE)

@app.route('/api/upload', methods=['POST'])
def api_upload_file():
    """Handle file upload from frontend and process video directly"""
    logger.info("🔍 API Upload route called")
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Unsupported file type: {file_ext}. Supported types: {", ".join(allowed_extensions)}'}), 400
        
        # Check file size (max 500MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        max_size = 500 * 1024 * 1024  # 500MB
        if file_size > max_size:
            return jsonify({'error': f'File too large. Maximum size: 500MB, your file: {file_size / (1024*1024):.1f}MB'}), 400
        
        # Get paths from config
        input_folder, output_folder = get_config_paths()
        
        # Clean up old output files to avoid confusion
        output_dir = Path(output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        for old_file in output_dir.glob('*.mp4'):
            try:
                old_file.unlink()
                logger.info(f"🗑️ Removed old output file: {old_file.name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove old file {old_file.name}: {str(e)}")
        
        # Create input directory
        input_dir = Path(input_folder)
        input_dir.mkdir(exist_ok=True)
        
        # Clean up old input files
        for old_file in input_dir.glob('*'):
            try:
                old_file.unlink()
                logger.info(f"🗑️ Removed old input file: {old_file.name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove old file {old_file.name}: {str(e)}")
        
        # Save uploaded file
        file_path = input_dir / file.filename
        file.save(file_path)
        
        logger.info(f"File uploaded: {file_path}")
        
        # Small delay to ensure file is fully written
        import time
        time.sleep(1)
        
        # File uploaded successfully - wait for phone number before processing
        response_data = {
            'message': 'Video uploaded successfully! Please provide your phone number to start processing.',
            'status': 'UPLOADED',
            'filename': file.filename
        }
        logger.info(f"✅ File uploaded successfully: {file.filename}")
        return jsonify(response_data)
            
    except Exception as e:
        # Add traceback to logs for detailed error information
        logger.error("❌ Upload error occurred:")
        logger.error(f"Error: {str(e)}")
        logger.error("Full traceback:")
        traceback.print_exc()
        
        logger.info(f"🔍 Returning error JSON response: {str(e)}")
        return jsonify({
            'error': 'Upload failed',
            'details': str(e)
        }), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process video directly (legacy endpoint)"""
    logger.info("🔍 Upload route called")
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get paths from config
        input_folder, output_folder = get_config_paths()
        
        # Clean up old output files to avoid confusion
        output_dir = Path(output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        for old_file in output_dir.glob('*.mp4'):
            try:
                old_file.unlink()
                logger.info(f"🗑️ Removed old output file: {old_file.name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove old file {old_file.name}: {str(e)}")
        
        # Create input directory
        input_dir = Path(input_folder)
        input_dir.mkdir(exist_ok=True)
        
        # Clean up old input files
        for old_file in input_dir.glob('*'):
            try:
                old_file.unlink()
                logger.info(f"🗑️ Removed old input file: {old_file.name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove old file {old_file.name}: {str(e)}")
        
        # Save uploaded file
        file_path = input_dir / file.filename
        file.save(file_path)
        
        logger.info(f"File uploaded: {file_path}")
        
        # Small delay to ensure file is fully written
        import time
        time.sleep(1)
        
        # File uploaded successfully - wait for phone number before processing
        response_data = {
            'message': 'Video uploaded successfully! Please provide your phone number to start processing.',
            'status': 'UPLOADED',
            'filename': file.filename
        }
        logger.info(f"✅ File uploaded successfully: {file.filename}")
        return jsonify(response_data)
            
    except Exception as e:
        # Add traceback to logs for detailed error information
        logger.error("❌ Upload error occurred:")
        logger.error(f"Error: {str(e)}")
        logger.error("Full traceback:")
        traceback.print_exc()
        
        logger.info(f"🔍 Returning error JSON response: {str(e)}")
        return jsonify({
            'error': 'Upload failed',
            'details': str(e)
        }), 500

@app.route('/cleanup/<video_base_name>', methods=['POST'])
def manual_cleanup(video_base_name):
    """Manually trigger cleanup for a specific video"""
    try:
        # Get paths from config
        input_folder, output_folder = get_config_paths()
        output_dir = Path(output_folder)
        
        # Find all files related to this video
        files_to_delete = []
        
        # Main processed video
        main_video_pattern = f"{video_base_name}_with_subs.mp4"
        for file in output_dir.glob(main_video_pattern):
            if file.is_file():
                files_to_delete.append(file)
        
        # Short clips
        short_clips_pattern = f"{video_base_name}_short_*.mp4"
        for file in output_dir.glob(short_clips_pattern):
            if file.is_file():
                files_to_delete.append(file)
        
        # Trimmed video
        trimmed_pattern = f"{video_base_name}_with_subs_trimmed.mp4"
        trimmed_dir = output_dir / "processed"
        if trimmed_dir.exists():
            for file in trimmed_dir.glob(trimmed_pattern):
                if file.is_file():
                    files_to_delete.append(file)
        
        # Subtitle files
        subtitle_dir = output_dir / "subtitles"
        if subtitle_dir.exists():
            subtitle_pattern = f"{video_base_name}.srt"
            for file in subtitle_dir.glob(subtitle_pattern):
                if file.is_file():
                    files_to_delete.append(file)
        
        # Delete all found files
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"🗑️ Deleted: {file_path.name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not delete {file_path.name}: {str(e)}")
        
        logger.info(f"✅ Manual cleanup completed for {video_base_name}: {deleted_count} files deleted")
        
        return jsonify({
            'message': f'Manual cleanup completed for {video_base_name}: {deleted_count} files deleted',
            'deleted_files': deleted_count,
            'video_base_name': video_base_name
        })
        
    except Exception as e:
        logger.error(f"Error starting manual cleanup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/start-processing', methods=['POST'])
def api_start_processing():
    """Start video processing after phone number is provided"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({'error': 'Phone number is required'}), 400
        
        # Get paths from config
        input_folder, output_folder = get_config_paths()
        input_dir = Path(input_folder)
        
        # Find the uploaded video file
        video_files = list(input_dir.glob('*.mp4')) + list(input_dir.glob('*.mov')) + list(input_dir.glob('*.avi')) + list(input_dir.glob('*.mkv'))
        
        if not video_files:
            return jsonify({'error': 'No video file found. Please upload a video first.'}), 400
        
        # Use the first (and should be only) video file
        video_file = video_files[0]
        filename = video_file.name
        
        # Clear previous pipeline logs
        clear_pipeline_logs()
        
        # Start background processing
        task_id = str(uuid.uuid4())
        logger.info(f"🔍 Starting background processing for: {filename} with task ID: {task_id} (Phone: {phone_number})")
        
        # Start background thread
        thread = threading.Thread(target=process_video_background, args=(task_id, filename))
        thread.daemon = True
        thread.start()
        
        # Return task ID immediately
        response_data = {
            'message': 'Video processing started! This may take a few minutes.',
            'task_id': task_id,
            'status': 'PROCESSING',
            'filename': filename
        }
        logger.info(f"🔍 Returning task ID: {task_id}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error starting video processing: {str(e)}")
        return jsonify({
            'error': 'Failed to start video processing',
            'details': str(e)
        }), 500

@app.route('/api/task/<task_id>')
def api_get_task_status(task_id):
    """Get status of background task (API endpoint for frontend)"""
    if task_id not in background_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task_info = background_tasks[task_id]
    return jsonify(task_info)

@app.route('/task/<task_id>')
def get_task_status(task_id):
    """Get status of background task (legacy endpoint)"""
    if task_id not in background_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task_info = background_tasks[task_id]
    return jsonify(task_info)

@app.route('/api/task/<task_id>/result')
def api_get_task_result(task_id):
    """Get result of completed task (API endpoint for frontend)"""
    if task_id not in background_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task_info = background_tasks[task_id]
    if task_info['status'] == 'SUCCESS':
        result = task_info.get('result', {})
        return jsonify({
            'status': 'SUCCESS',
            'result': result,
            'short_clips': result.get('short_clips', []),
            'video_base_name': result.get('video_base_name')
        })
    else:
        return jsonify({
            'status': task_info['status'],
            'error': task_info.get('error', 'Task not completed successfully')
        }), 400

@app.route('/task/<task_id>/result')
def get_task_result(task_id):
    """Get result of completed task (legacy endpoint)"""
    if task_id not in background_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task_info = background_tasks[task_id]
    if task_info['status'] == 'SUCCESS':
        result = task_info.get('result', {})
        video_base_name = result.get('video_base_name')
        if video_base_name:
            return redirect(url_for('show_result', video_base_name=video_base_name))
        else:
            return jsonify({'error': 'No result available'}), 400
    else:
        return jsonify({'error': 'Task not completed successfully'}), 400

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Video automation pipeline is running'})

@app.route('/debug')
def debug_info():
    """Debug endpoint to show environment and system info"""
    try:
        # Check ffmpeg
        ffmpeg_status = "unknown"
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
            ffmpeg_status = "available" if result.returncode == 0 else "error"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            ffmpeg_status = "not_found"
        
        # Check directories
        input_folder, output_folder = get_config_paths()
        input_dir = Path(input_folder)
        output_dir = Path(output_folder)
        
        return jsonify({
            'ffmpeg_status': ffmpeg_status,
            'input_directory_exists': input_dir.exists(),
            'output_directory_exists': output_dir.exists(),
            'input_directory_writable': input_dir.is_dir() and os.access(input_dir, os.W_OK),
            'output_directory_writable': output_dir.is_dir() and os.access(output_dir, os.W_OK),
            'python_version': sys.version,
            'working_directory': os.getcwd(),
            'environment_variables': {
                'PORT': os.environ.get('PORT'),
                'PYTHONPATH': os.environ.get('PYTHONPATH')
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs')
def get_logs():
    """Get recent logs"""
    try:
        log_file = Path('pipeline.log')
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.read()
            return jsonify({'logs': logs})
        else:
            return jsonify({'logs': 'No logs available yet'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/result')
def show_result():
    """Display processed video with download and logs"""
    try:
        video_base_name = request.args.get('video_base_name')
        
        if not video_base_name:
            return jsonify({'error': 'No video base name specified'}), 400
        
        
        _, output_folder = get_config_paths()
        output_dir = Path(output_folder)
        
        # Look for short clips
        short_clips = []
        pattern = f"{video_base_name}_short_*.mp4"
        
        # Look in main output directory first
        for clip_file in output_dir.glob(pattern):
            if clip_file.is_file():
                clip_size = round(clip_file.stat().st_size / (1024 * 1024), 2)
                short_clips.append({
                    'filename': clip_file.name,
                    'url': f'/output/{clip_file.name}',
                    'size': f"{clip_size} MB"
                })
        
        # Also look in shorts subdirectory
        shorts_dir = output_dir / "shorts"
        if shorts_dir.exists():
            for clip_file in shorts_dir.glob(pattern):
                if clip_file.is_file():
                    clip_size = round(clip_file.stat().st_size / (1024 * 1024), 2)
                    short_clips.append({
                        'filename': clip_file.name,
                        'url': f'/output/shorts/{clip_file.name}',
                        'size': f"{clip_size} MB"
                    })
        # Sort clips by name (short_1, short_2, etc.)
        short_clips.sort(key=lambda x: x['filename'])
        
        # Look for main processed video as fallback
        main_video = None
        main_video_pattern = f"{video_base_name}_with_subs_trimmed.mp4"
        main_video_path = output_dir / main_video_pattern
        if main_video_path.exists():
            file_size = main_video_path.stat().st_size
            file_size_mb = round(file_size / (1024 * 1024), 2)
            main_video = {
                'filename': main_video_path.name,
                'url': f'/output/{main_video_path.name}',
                'size': f"{file_size_mb} MB"
            }
        
        # Read logs from pipeline.log
        log_file = Path('pipeline.log')
        logs = "No logs available yet."
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = f.read()
            except Exception as e:
                logs = f"Error reading logs: {str(e)}"
        
        # Get current timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return render_template('result.html', 
                             main_video=main_video,
                             short_clips=short_clips,
                             video_base_name=video_base_name,
                             timestamp=timestamp,
                             logs=logs)
    except Exception as e:
        logger.error(f"Error in show_result: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/output/<path:filename>')
def serve_video(filename):
    """Serve output video files"""
    try:
        _, output_folder = get_config_paths()
        return send_from_directory(output_folder, filename)
    except Exception as e:
        logger.error(f"Error serving video {filename}: {str(e)}")
        return jsonify({'error': f'File not found: {filename}'}), 404

@app.route('/output/shorts/<path:filename>')
def serve_short_video(filename):
    """Serve short video files from shorts subdirectory"""
    try:
        _, output_folder = get_config_paths()
        shorts_dir = Path(output_folder) / "shorts"
        return send_from_directory(shorts_dir, filename)
    except Exception as e:
        logger.error(f"Error serving short video {filename}: {str(e)}")
        return jsonify({'error': f'File not found: {filename}'}), 404

if __name__ == '__main__':
    # Validate environment before starting
    validate_environment()
    
    # Get port from environment (Railway sets this)
    port = int(os.environ.get('PORT', 8000))
    
    logger.info(f"🚀 Starting web server on port {port}")
    # Increase timeout for video processing
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
