import React from 'react';
import './PricingPage.css';

const PricingPage = () => {
  return (
    <div className="pricing-page">
      {/* Pricing Section */}
      <main className="pricing-main">
        <div className="pricing-container">
          <div className="pricing-header">
            <h1 className="pricing-title">Choose Your Plan</h1>
            <p className="pricing-subtitle">Start creating viral content today</p>
          </div>

          <div className="pricing-cards">
            {/* Early Creator Plan */}
            <div className="pricing-card early-creator">
              <div className="card-header">
                <div className="plan-icon">
                  <div className="icon-circle">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" fill="white"/>
                      <path d="M12 14C7.58172 14 4 17.5817 4 22H20C20 17.5817 16.4183 14 12 14Z" fill="white"/>
                    </svg>
                  </div>
                </div>
                <h3 className="plan-title">Early Creator</h3>
                <p className="plan-subtitle">For solo creators getting started</p>
              </div>

              <div className="pricing-info">
                <div className="price-container">
                  <span className="original-price">$9/mo</span>
                  <span className="current-price">$0 today</span>
                </div>
                <p className="price-note">Free during beta</p>
              </div>

              <div className="features-list">
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>100 credits/month</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>Auto-detect viral clips</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>99% accurate multilingual subtitles</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>Smart silence & filler removal</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>Viral title + tag generator</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>No watermark (even now)</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>Export or auto-post to Shorts, Reels, TikTok</span>
                </div>
              </div>

              <button className="pricing-btn early-creator-btn">
                Free now
              </button>
              <p className="disclaimer">* No credit card required</p>
            </div>

            {/* Beta Pro Plan */}
            <div className="pricing-card beta-pro">
              <div className="popular-badge">Most Popular</div>
              <div className="card-header">
                <div className="plan-icon">
                  <div className="icon-circle">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L15.09 8.26L22 9L17 14L18.18 21L12 17.77L5.82 21L7 14L2 9L8.91 8.26L12 2Z" fill="white"/>
                    </svg>
                  </div>
                </div>
                <h3 className="plan-title">Beta Pro</h3>
                <p className="plan-subtitle">For power users & small teams</p>
              </div>

              <div className="pricing-info">
                <div className="price-container">
                  <span className="original-price">$57/mo</span>
                  <span className="current-price">$19 today</span>
                </div>
                <p className="price-note">Best in the Class technology</p>
              </div>

              <div className="features-list">
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>250 credits/month</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>Everything in Creator</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>Team access (2 seats)</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>Custom branding & fonts</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>Post scheduling</span>
                </div>
                <div className="feature-item">
                  <div className="check-icon">✓</div>
                  <span>Priority processing</span>
                </div>
              </div>

              <div className="special-offer">
                <div className="rocket-icon">🚀</div>
                <span>Get 2 months free</span>
              </div>

              <button className="pricing-btn beta-pro-btn">
                Pay now
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <p className="footer-text">© 2025 Makereels.live. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default PricingPage;
