import React, { useState, useEffect } from 'react';
import './FeaturesPage.css';

const FeaturesPage = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isAutoPlaying] = useState(true);

  const slides = [
    {
      id: 1,
      title: "AI Captioning",
      description: "Automatically generate engaging captions for your videos using advanced AI technology.",
      gif: "/ai captioning.gif"
    },
    {
      id: 2,
      title: "AI Clipping",
      description: "Intelligently identify and extract the most engaging moments from your content.",
      gif: "/ai clipping.gif"
    },
    {
      id: 3,
      title: "AI Reframe",
      description: "Automatically reframe your videos to perfect aspect ratios for different platforms.",
      gif: "/ai reframe.gif"
    },
    {
      id: 4,
      title: "AI Titles",
      description: "Generate compelling titles and thumbnails that maximize engagement and click-through rates.",
      gif: "/ai titles.jpg"
    },
    {
      id: 5,
      title: "Trim Silence",
      description: "Automatically detect and remove silent segments to create more dynamic, engaging content.",
      gif: "/trim silence.jpg"
    }
  ];

  // Auto-play functionality
  useEffect(() => {
    if (!isAutoPlaying) return;

    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 4000);

    return () => clearInterval(interval);
  }, [isAutoPlaying, slides.length]);

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

  const goToPrevious = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const goToNext = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length);
  };

  return (
    <div className="features-page">
      <div className="features-container">
        {/* Header */}
        <div className="features-header">
          <h1 className="features-title">AI-Powered Features</h1>
          <p className="features-subtitle">Discover how our AI transforms your content creation process</p>
        </div>

        {/* Slideshow */}
        <div className="slideshow-container">
          <div className="slideshow-wrapper">
            <div className="slide-content">
              <div className="slide-media">
                <img 
                  src={slides[currentSlide].gif} 
                  alt={slides[currentSlide].title}
                  className="slide-gif"
                />
              </div>
              <div className="slide-info">
                <h2 className="slide-title">{slides[currentSlide].title}</h2>
                <p className="slide-description">{slides[currentSlide].description}</p>
              </div>
            </div>

            {/* Navigation Controls */}
            <div className="slideshow-controls">
              <button 
                className="nav-button prev-button" 
                onClick={goToPrevious}
                aria-label="Previous slide"
              >
                ‹
              </button>
              <button 
                className="nav-button next-button" 
                onClick={goToNext}
                aria-label="Next slide"
              >
                ›
              </button>
            </div>

            {/* Slide Indicators */}
            <div className="slide-indicators">
              {slides.map((_, index) => (
                <button
                  key={index}
                  className={`indicator ${index === currentSlide ? 'active' : ''}`}
                  onClick={() => goToSlide(index)}
                  aria-label={`Go to slide ${index + 1}`}
                />
              ))}
            </div>

          </div>
        </div>

        {/* Additional Features Section */}
        <div className="additional-features">
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3 className="feature-card-title">Smart Analytics</h3>
              <p className="feature-card-description">Get insights into your content performance with AI-powered analytics.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3 className="feature-card-title">Lightning Fast</h3>
              <p className="feature-card-description">Process your videos in minutes, not hours, with our optimized AI engine.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3 className="feature-card-title">Secure & Private</h3>
              <p className="feature-card-description">Your content is protected with enterprise-grade security and privacy.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📱</div>
              <h3 className="feature-card-title">Multi-Platform</h3>
              <p className="feature-card-description">Optimize for YouTube, TikTok, Instagram, and more social platforms.</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <p className="footer-text">© 2025 Makereels.live. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default FeaturesPage;
