'use client'

import { BrandAnalysis } from '../types/brand'
import { Loader2 } from 'lucide-react'

interface EmailTemplateProps {
  brandData: BrandAnalysis | null
  isAnalyzing: boolean
}

export default function EmailTemplate({ brandData, isAnalyzing }: EmailTemplateProps) {
  // Default styling when no brand data is available
  const defaultStyles = {
    primaryColor: '#1f2937',
    secondaryColor: '#6b7280',
    backgroundColor: '#ffffff',
    linkColor: '#3b82f6'
  }

  // Apply brand data if available
  const styles = brandData ? {
    primaryColor: brandData.primaryColor || defaultStyles.primaryColor,
    secondaryColor: brandData.secondaryColor || defaultStyles.secondaryColor,
    backgroundColor: brandData.backgroundColor || defaultStyles.backgroundColor,
    linkColor: brandData.linkColor || defaultStyles.linkColor
  } : defaultStyles

  if (isAnalyzing) {
    return (
      <div className="email-template relative">
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-600">Applying brand styling...</p>
          </div>
        </div>
        
        {/* Placeholder template with shimmer effect */}
        <div className="p-8 space-y-6">
          <div className="shimmer h-8 rounded"></div>
          <div className="shimmer h-4 rounded w-3/4"></div>
          <div className="shimmer h-4 rounded w-1/2"></div>
          <div className="shimmer h-32 rounded"></div>
          <div className="shimmer h-10 rounded w-1/3"></div>
        </div>
      </div>
    )
  }

  return (
    <div 
      className="email-template transition-all duration-500 ease-in-out"
      style={{ 
        backgroundColor: styles.backgroundColor
      }}
    >
      {/* Email Header */}
      <div 
        className="px-8 py-6 border-b"
        style={{ 
          backgroundColor: styles.primaryColor,
          borderBottomColor: styles.secondaryColor + '20'
        }}
      >
        <h1 
          className="text-2xl font-bold text-white"
          style={{ 
            color: styles.backgroundColor === '#ffffff' ? styles.backgroundColor : '#ffffff'
          }}
        >
          Your Brand Newsletter
        </h1>
        <p 
          className="text-sm mt-1 opacity-90"
          style={{ 
            color: styles.backgroundColor === '#ffffff' ? styles.backgroundColor : '#ffffff'
          }}
        >
          Weekly insights and updates
        </p>
      </div>

      {/* Email Body */}
      <div className="p-8 space-y-6">
        {/* Welcome Section */}
        <div>
          <h2 
            className="text-xl font-semibold mb-3"
            style={{ 
              color: styles.primaryColor
            }}
          >
            Welcome to Our Newsletter!
          </h2>
          <p 
            className="text-base leading-relaxed"
            style={{ 
              color: styles.secondaryColor
            }}
          >
            Thank you for subscribing to our newsletter. We're excited to share the latest updates, 
            insights, and exclusive content with you. This email template automatically adapts to 
            match the brand colors from your website.
          </p>
        </div>

        {/* Content Card */}
        <div 
          className="rounded-lg p-6 border"
          style={{ 
            backgroundColor: styles.primaryColor + '05',
            borderColor: styles.primaryColor + '20'
          }}
        >
          <h3 
            className="text-lg font-semibold mb-2"
            style={{ 
              color: styles.primaryColor
            }}
          >
            Featured Article
          </h3>
          <p 
            className="text-sm mb-4"
            style={{ 
              color: styles.secondaryColor
            }}
          >
            Discover how AI-powered brand analysis can transform your email marketing campaigns 
            by automatically extracting and applying consistent brand elements.
          </p>
          <a 
            href="#"
            className="inline-flex items-center text-sm font-medium hover:underline transition-colors"
            style={{ 
              color: styles.linkColor
            }}
          >
            Read More →
          </a>
        </div>

        {/* Call to Action */}
        <div className="text-center">
          <button 
            className="px-6 py-3 rounded-lg font-semibold text-white transition-all duration-200 hover:opacity-90 hover:scale-105"
            style={{ 
              backgroundColor: styles.linkColor
            }}
          >
            Explore Our Platform
          </button>
        </div>

        {/* Footer Links */}
        <div className="pt-6 border-t" style={{ borderTopColor: styles.secondaryColor + '20' }}>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            {['About Us', 'Contact', 'Unsubscribe', 'Privacy Policy'].map((link, index) => (
              <a 
                key={index}
                href="#"
                className="hover:underline transition-colors"
                style={{ 
                  color: styles.linkColor
                }}
              >
                {link}
              </a>
            ))}
          </div>
          
          <div className="text-center mt-4">
            <p 
              className="text-xs"
              style={{ 
                color: styles.secondaryColor
              }}
            >
              © 2024 Your Company. All rights reserved.
            </p>
          </div>
        </div>
      </div>

      {/* Brand Analysis Indicator */}
      {brandData && (
        <div className="px-8 py-3 bg-green-50 border-t border-green-200">
          <div className="flex items-center justify-between text-xs">
            <span className="text-green-700 font-medium">✓ Brand styling applied</span>
            <div className="flex items-center space-x-2">
              <span className="text-green-600">Fonts:</span>
              <span className="text-green-800 font-medium">
                {brandData.fonts.slice(0, 2).join(', ')}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
