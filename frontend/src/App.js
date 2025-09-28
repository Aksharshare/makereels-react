import React, { useState, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import PricingPage from './PricingPage';
import FeaturesPage from './FeaturesPage';

function App() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [currentTask, setCurrentTask] = useState(null);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [resultFiles, setResultFiles] = useState([]);
  const [downloadingFiles, setDownloadingFiles] = useState(new Set());
  const [uploadedVideo, setUploadedVideo] = useState(null);
  const [showPhoneInput, setShowPhoneInput] = useState(false);
  const [dummyProgress, setDummyProgress] = useState(0);
  const fileInputRef = useRef(null);

  // Phone number validation function
  const validatePhoneNumber = (phone) => {
    // Remove all non-digit characters for validation
    const cleanPhone = phone.replace(/\D/g, '');
    
    // Check if it's empty
    if (!cleanPhone) {
      return { isValid: false, message: 'Please enter your phone number' };
    }
    
    // Check length (7-15 digits is reasonable for international numbers)
    if (cleanPhone.length < 7 || cleanPhone.length > 15) {
      return { isValid: false, message: 'Please enter a valid phone number (7-15 digits)' };
    }
    
    // Check if it contains only digits (after cleaning)
    if (!/^\d+$/.test(cleanPhone)) {
      return { isValid: false, message: 'Phone number should contain only digits' };
    }
    
    return { isValid: true, message: '' };
  };

  // Dummy progress bar that runs for 6 minutes and stops at 99%
  const startDummyProgress = () => {
    setDummyProgress(0);
    const startTime = Date.now();
    const duration = 6 * 60 * 1000; // 6 minutes in milliseconds
    
    const updateProgress = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min((elapsed / duration) * 99, 99); // Cap at 99%
      setDummyProgress(progress);
      
      if (progress < 99) {
        setTimeout(updateProgress, 100); // Update every 100ms
      }
    };
    
    updateProgress();
  };

  const handleJoinBeta = async (e) => {
    e.preventDefault();
    
    // Validate phone number
    const phoneValidation = validatePhoneNumber(phoneNumber);
    if (!phoneValidation.isValid) {
      setUploadStatus({
        type: 'error',
        message: phoneValidation.message
      });
      return;
    }
    
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      alert('Thank you for joining our beta! We\'ll be in touch soon.');
      setPhoneNumber('');
    }, 1000);
  };

  const handleGetShorts = async (e) => {
    e.preventDefault();
    
    // Validate phone number
    const phoneValidation = validatePhoneNumber(phoneNumber);
    if (!phoneValidation.isValid) {
      setUploadStatus({
        type: 'error',
        message: phoneValidation.message
      });
      return;
    }
    
    if (!uploadedVideo) {
      setUploadStatus({
        type: 'error',
        message: 'No video uploaded'
      });
      return;
    }
    
    try {
      // Send phone number to Make.com webhook
      const makeWebhookUrl = 'https://hook.us2.make.com/8hamrtcq1dj54cfvmrpwb72mok8lb417';
      
      try {
        await fetch(makeWebhookUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            phone: phoneNumber,
            timestamp: new Date().toISOString(),
            source: 'makereels_app'
          }),
        });
      } catch (webhookError) {
        console.error('Failed to send to Make.com webhook:', webhookError);
        // Continue with processing even if webhook fails
      }

      // Start processing the uploaded video
      setUploadStatus({
        type: 'info',
        message: 'Starting video processing...'
      });
      
      const response = await fetch('/api/start-processing', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setUploadStatus({
          type: 'success',
          message: 'Processing started! We\'ll notify you when your shorts are ready.'
        });
        setCurrentTask(result.task_id);
        setProcessingStatus('PROCESSING');
        setShowPhoneInput(false);
         setPhoneNumber('');
         // Start dummy progress bar
         startDummyProgress();
         // Start polling for processing status
         startStatusPolling(result.task_id);
      } else {
        const errorData = await response.json();
        setUploadStatus({
          type: 'error',
          message: errorData.message || 'Failed to start processing. Please try again.'
        });
      }
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: 'Network error. Please check your connection and try again.'
      });
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Clear any previous status
      setUploadStatus(null);
      setDummyProgress(0); // Reset progress bar
      setProcessingStatus(null); // Reset processing status
      
      // Validate file type - check both MIME type and file extension
      const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/mkv', 'video/quicktime'];
      const validExtensions = ['.mp4', '.avi', '.mov', '.wmv', '.mkv'];
      
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
      const isValidType = validTypes.includes(file.type) || validExtensions.includes(fileExtension);
      
      if (!isValidType) {
        setUploadStatus({
          type: 'error',
          message: 'Please select a valid video file (MP4, AVI, MOV, WMV, MKV)'
        });
        return;
      }
      
      // Validate file size (max 100MB)
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (file.size > maxSize) {
        setUploadStatus({
          type: 'error',
          message: 'File size must be less than 100MB'
        });
        return;
      }
      
      setSelectedFile(file);
      setUploadStatus(null);
    } else {
      // No file selected, clear status
      setUploadStatus(null);
    }
  };

  const handleVideoUpload = async () => {
    if (!selectedFile) {
      setUploadStatus({
        type: 'error',
        message: 'Please select a video file first'
      });
      return;
    }
    
    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus(null);
    
    const formData = new FormData();
    formData.append('video', selectedFile);
    
    try {
      const xhr = new XMLHttpRequest();
      
      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(progress);
        }
      });
      
      // Handle response
      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          setUploadStatus({
            type: 'success',
            message: 'Video uploaded successfully!'
          });
          setUploadedVideo({
            task_id: response.task_id,
            filename: response.filename,
            file: selectedFile
          });
          setShowPhoneInput(true);
          setSelectedFile(null);
          setUploadProgress(0);
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        } else {
          setUploadStatus({
            type: 'error',
            message: 'Upload failed. Please try again.'
          });
        }
        setIsUploading(false);
      });
      
      // Handle errors
      xhr.addEventListener('error', () => {
        setUploadStatus({
          type: 'error',
          message: 'Upload failed. Please check your connection and try again.'
        });
        setIsUploading(false);
      });
      
      // Send request
      xhr.open('POST', '/upload', true);
      xhr.send(formData);
      
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: 'Upload failed. Please try again.'
      });
      setIsUploading(false);
    }
  };

  const removeSelectedFile = () => {
    setSelectedFile(null);
    setUploadStatus(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const startStatusPolling = (taskId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/task/${taskId}`);
        const data = await response.json();
        
        if (response.ok) {
          if (data.status === 'PROCESSING') {
            setProcessingStatus('PROCESSING');
           } else if (data.result?.status === 'SUCCESS') {
            // Transform the short clips to match expected format
            const shortClips = data.result?.short_clips || [];
            const transformedClips = shortClips.map(clip => ({
              filename: clip.filename,
              size: clip.size * 1024 * 1024, // Convert MB to bytes
              download_url: clip.url // Use the URL directly from backend
            }));
            setResultFiles(transformedClips);
            setProcessingStatus('completed');
            setDummyProgress(100); // Complete the progress bar
            clearInterval(pollInterval);
          } else if (data.status === 'FAILURE') {
            setUploadStatus({
              type: 'error',
              message: `Processing failed: ${data.error}`
            });
            clearInterval(pollInterval);
          }
        }
      } catch (error) {
        console.error('Status polling error:', error);
      }
    }, 2000); // Poll every 2 seconds
    
    // Clear interval after 10 minutes to prevent infinite polling
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 600000);
  };

  const downloadFile = async (downloadUrl, filename) => {
    try {
      // Add to downloading set
      setDownloadingFiles(prev => new Set([...prev, filename]));
      
      // Show download progress
      setUploadStatus({ type: 'info', message: `Downloading ${filename}...` });
      
      // Create a more robust download mechanism
      const response = await fetch(downloadUrl, {
        method: 'GET',
        headers: {
          'Accept': 'video/mp4, video/*, */*'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Download failed: ${response.status} ${response.statusText}`);
      }
      
      // Get the file blob
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up
      window.URL.revokeObjectURL(url);
      
      // Show success message
      setUploadStatus({ type: 'success', message: `✅ ${filename} downloaded successfully!` });
      
      // Clear status after 3 seconds
      setTimeout(() => {
        setUploadStatus(null);
      }, 3000);
      
    } catch (error) {
      console.error('Download error:', error);
      setUploadStatus({ type: 'error', message: `❌ Download failed: ${error.message}` });
      
      // Clear error after 5 seconds
      setTimeout(() => {
        setUploadStatus(null);
      }, 5000);
    } finally {
      // Remove from downloading set
      setDownloadingFiles(prev => {
        const newSet = new Set(prev);
        newSet.delete(filename);
        return newSet;
      });
    }
  };

  return (
    <Router>
      <div className="App">
        {/* Header */}
        <header className="header">
          <div className="logo">
            <Link to="/">
              <img src="/assets/images/headerlogo.png" alt="MAKEREELS" className="logo-image" />
            </Link>
          </div>
          <nav className="nav">
            <Link to="/features" className="nav-link">Features</Link>
            <Link to="/pricing" className="nav-link">Pricing</Link>
            <button className="sign-up-btn">Sign Up</button>
          </nav>
        </header>

        <Routes>
          <Route path="/" element={
            <>
              {/* Hero Section */}
              <main className="hero">
        <div className="hero-content">
          <h1 className="hero-title">
            Post more <span className="lightning">⚡</span> Grow faster
          </h1>
          
          <h2 className="main-headline">
            Turn <span className="highlight">Raw Video</span> into <span className="gradient-text">Viral Shorts</span>
          </h2>
          
          <p className="hero-description">
            AI-powered video editing that finds viral moments, adds captions, reframes content, and generates titles automatically.
          </p>

          {/* Video Upload Section, Phone Input Section, or Results Section */}
          {processingStatus === 'completed' && resultFiles.length > 0 ? (
            <div className="upload-section">
              <h3 className="upload-title">🎉 Your Viral Shorts Are Ready!</h3>
              <p className="upload-description">
                We've created {resultFiles.length} viral short{resultFiles.length > 1 ? 's' : ''} from your video.
              </p>
              
              <div className="upload-container">
                <div className="results-grid">
                  {resultFiles.map((file, index) => (
                    <div key={index} className="result-item">
                      <div className="result-icon">🎬</div>
                      <div className="result-info">
                        <h4 className="result-filename" title={file.filename}>
                          {file.filename.length > 30 ? `${file.filename.substring(0, 30)}...` : file.filename}
                        </h4>
                        <p className="result-size">
                          {(file.size / (1024 * 1024)).toFixed(1)} MB
                        </p>
                      </div>
                      <button
                        className={`download-btn ${downloadingFiles.has(file.filename) ? 'loading' : ''}`}
                        onClick={() => downloadFile(file.download_url, file.filename)}
                        disabled={downloadingFiles.has(file.filename)}
                      >
                        {downloadingFiles.has(file.filename) ? (
                          <>
                            <span className="download-spinner">⏳</span>
                            Downloading...
                          </>
                        ) : (
                          'Download'
                        )}
                      </button>
                    </div>
                  ))}
                </div>
                
                <button 
                  onClick={() => {
                    setProcessingStatus(null);
                    setResultFiles([]);
                    setCurrentTask(null);
                    setSelectedFile(null);
                    setShowPhoneInput(false);
                    setPhoneNumber('');
                    setUploadStatus(null);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = '';
                    }
                  }}
                  className="upload-btn"
                  style={{ marginTop: '20px' }}
                >
                  Upload Another Video
                </button>
              </div>
            </div>
          ) : processingStatus === 'PROCESSING' ? (
            <div className="upload-section">
              <h3 className="upload-title">Processing Your Video</h3>
              <p className="upload-description">AI is analyzing your video and creating viral shorts...</p>
              
              <div className="upload-container">
                {/* YouTube Video for entertainment during processing */}
                <div className="youtube-container">
                  <iframe 
                    width="100%" 
                    height="100%" 
                    src="https://www.youtube.com/embed/9CQX9kq4BPM?autoplay=1&mute=0&controls=1&rel=0&modestbranding=1" 
                    title="YouTube video player" 
                    frameBorder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                    allowFullScreen
                    className="youtube-iframe">
                  </iframe>
                </div>
                
                <div className="processing-info">
                  <div className="processing-spinner">🎬</div>
                  
                  {/* Simple Progress Bar */}
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${dummyProgress}%` }}
                      ></div>
                    </div>
                    <div className="progress-text">
                      {dummyProgress < 99 ? `${Math.round(dummyProgress)}%` : 'Almost done...'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : !showPhoneInput ? (
            <div className="upload-section">
              <h3 className="upload-title">Upload Your Raw Video</h3>
              <p className="upload-description">Transform your video into viral shorts with AI</p>
              
              <div className="upload-container">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept="video/*"
                  className="file-input"
                  id="video-upload"
                />
                {!selectedFile ? (
                  <label htmlFor="video-upload" className="file-input-label">
                    Upload Video
                  </label>
                ) : (
                  <div className="file-preview">
                    <div className="file-info">
                      <span className="file-name">{selectedFile.name}</span>
                      <span className="file-size">{(selectedFile.size / (1024 * 1024)).toFixed(1)} MB</span>
                      <button 
                        type="button" 
                        onClick={removeSelectedFile}
                        className="remove-file-btn"
                      >
                        ✕
                      </button>
                    </div>
                    
                    {isUploading && (
                      <div className="upload-progress">
                        <div className="progress-bar">
                          <div 
                            className="progress-fill" 
                            style={{ width: `${uploadProgress}%` }}
                          ></div>
                        </div>
                        <span className="progress-text">{uploadProgress}%</span>
                      </div>
                    )}
                    
                    {!isUploading && (
                      <button 
                        type="button"
                        onClick={handleVideoUpload}
                        className="upload-btn"
                      >
                        Upload & Process
                      </button>
                    )}
                  </div>
                )}
                
                {/* Client Logos Carousel */}
                <div className="clients-carousel">
                  <div className="clients-track">
                    <div className="client-logo">
                      <img src="/c1.png" alt="Client 1" />
                    </div>
                    <div className="client-logo">
                      <img src="/c2.png" alt="Client 2" />
                    </div>
                    <div className="client-logo">
                      <img src="/c3.png" alt="Client 3" />
                    </div>
                    <div className="client-logo">
                      <img src="/c4.png" alt="Client 4" />
                    </div>
                    <div className="client-logo">
                      <img src="/c5.png" alt="Client 5" />
                    </div>
                    <div className="client-logo">
                      <img src="/c6.png" alt="Client 6" />
                    </div>
                    <div className="client-logo">
                      <img src="/c7.png" alt="Client 7" />
                    </div>
                    <div className="client-logo">
                      <img src="/c8.png" alt="Client 8" />
                    </div>
                    <div className="client-logo">
                      <img src="/c9.png" alt="Client 9" />
                    </div>
                    {/* Duplicate for seamless loop */}
                    <div className="client-logo">
                      <img src="/c1.png" alt="Client 1" />
                    </div>
                    <div className="client-logo">
                      <img src="/c2.png" alt="Client 2" />
                    </div>
                    <div className="client-logo">
                      <img src="/c3.png" alt="Client 3" />
                    </div>
                    <div className="client-logo">
                      <img src="/c4.png" alt="Client 4" />
                    </div>
                    <div className="client-logo">
                      <img src="/c5.png" alt="Client 5" />
                    </div>
                    <div className="client-logo">
                      <img src="/c6.png" alt="Client 6" />
                    </div>
                    <div className="client-logo">
                      <img src="/c7.png" alt="Client 7" />
                    </div>
                    <div className="client-logo">
                      <img src="/c8.png" alt="Client 8" />
                    </div>
                    <div className="client-logo">
                      <img src="/c9.png" alt="Client 9" />
                    </div>
                  </div>
                </div>
                
                {uploadStatus && (
                  <div className={`upload-status ${uploadStatus.type}`}>
                    {uploadStatus.type === 'success' ? '✅' : '❌'} {uploadStatus.message}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="upload-section">
              <h3 className="upload-title">Enter Your Phone Number</h3>
                  <p className="upload-description">We'll notify you when your viral shorts are ready!</p>
                  
                  <div className="upload-container">
                    <form onSubmit={handleGetShorts} className="phone-form">
                      <input
                        type="tel"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        placeholder="+91 9876543210"
                        className="phone-input-main"
                        required
                      />
                      <button 
                        type="submit" 
                        className="get-shorts-btn-main"
                        disabled={isLoading}
                      >
                        {isLoading ? 'Starting...' : 'Get My Shorts'}
                      </button>
                    </form>
                    
                    {uploadStatus && (
                      <div className={`upload-status ${uploadStatus.type}`}>
                        {uploadStatus.type === 'success' ? '✅' : '❌'} {uploadStatus.message}
                      </div>
                    )}
                  </div>
            </div>
          )}

          {/* Processing Status - Removed since results now show in main upload area */}
          {false && processingStatus && processingStatus !== 'processing' && (
            <div className="processing-section">
              <h3 className="processing-title">Processing Your Video</h3>
              <div className="processing-status">
                
                {processingStatus === 'completed' && resultFiles.length > 0 && (
                  <div className="results-section">
                    <h3 className="results-title">🎉 Your Viral Shorts Are Ready!</h3>
                    <p className="results-description">
                      We've created {resultFiles.length} viral short{resultFiles.length > 1 ? 's' : ''} from your video.
                    </p>
                    
                    <div className="results-grid">
                      {resultFiles.map((file, index) => (
                        <div key={index} className="result-item">
                          <div className="result-icon">🎬</div>
                          <div className="result-info">
                            <h4 className="result-filename">{file.filename}</h4>
                            <p className="result-size">
                              {(file.size / (1024 * 1024)).toFixed(1)} MB
                            </p>
                          </div>
                    <button
                      className={`download-btn ${downloadingFiles.has(file.filename) ? 'loading' : ''}`}
                      onClick={() => downloadFile(file.download_url, file.filename)}
                      disabled={downloadingFiles.has(file.filename)}
                    >
                      {downloadingFiles.has(file.filename) ? (
                        <>
                          <span className="download-spinner">⏳</span>
                          Downloading...
                        </>
                      ) : (
                        <>
                          📥 Download
                        </>
                      )}
                    </button>
                        </div>
                      ))}
                    </div>
                    
                    <button
                      className="upload-new-btn"
                      onClick={() => {
                        setCurrentTask(null);
                        setProcessingStatus(null);
                        setResultFiles([]);
                        setUploadStatus(null);
                      }}
                    >
                      Upload Another Video
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </main>
      
      {/* Background Video Section */}
      <div className="bg-video-section">
        <video 
          className="bg-video" 
          autoPlay 
          muted 
          loop 
          playsInline
        >
          <source src="/bgshorts.mp4" type="video/mp4" />
        </video>
        <div className="bg-video-fade"></div>
      </div>
      
              {/* Footer */}
              <footer className="footer">
                <div className="footer-content">
                  <p className="footer-text">© 2025 Makereels.live. All rights reserved.</p>
                </div>
              </footer>
            </>
          } />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/pricing" element={<PricingPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

