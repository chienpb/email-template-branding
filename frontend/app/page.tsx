'use client'

import { useState } from 'react'
import { Globe, Palette, Type, Mail, ExternalLink, Settings } from 'lucide-react'
import EnhancedBrandAnalyzer from './components/EnhancedBrandAnalyzer'
import EmailTemplate from './components/EmailTemplate'
import { BrandAnalysis, ComparisonResult } from './types/brand'



export default function Home() {
  const [activeTab, setActiveTab] = useState<'enhanced'>('enhanced')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [brandData, setBrandData] = useState<BrandAnalysis | null>(null)

  const [error, setError] = useState<string | null>(null)

  const handleAnalysisComplete = (data: BrandAnalysis | null, errorMessage?: string) => {
    setIsAnalyzing(false)
    setBrandData(data)
    setError(errorMessage || null)
  }



  const handleAnalysisStart = () => {
    setIsAnalyzing(true)
    setError(null)
    setBrandData(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg">
                <Mail className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">AI Email Branding</h1>
                <p className="text-sm text-gray-600">Extract brand elements from websites</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Globe className="w-4 h-4" />
              <span>Proof of Concept</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Analysis Tools */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 p-6">


              {/* Enhanced Brand Analyzer */}
              <div className="flex items-center space-x-3 mb-6">
                <div className="flex items-center justify-center w-8 h-8 bg-purple-100 rounded-lg">
                  <Settings className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Enhanced Brand Analyzer</h2>
                  <p className="text-sm text-gray-600">Choose your extraction method and analyze brand elements</p>
                </div>
              </div>

              <EnhancedBrandAnalyzer
                onAnalysisStart={handleAnalysisStart}
                onAnalysisComplete={handleAnalysisComplete}
                isAnalyzing={isAnalyzing}
              />

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <p className="text-sm text-red-700 font-medium">Analysis Failed</p>
                  </div>
                  <p className="text-sm text-red-600 mt-1">{error}</p>
                </div>
              )}

              {/* Enhanced Analysis Results */}

              {brandData && (
                <div className="mt-6 space-y-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <p className="text-sm text-green-700 font-medium">
                      Analysis Complete - {brandData.method}
                    </p>
                  </div>
                  
                  {/* Brand Elements Display */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Fonts */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-3">
                        <Type className="w-4 h-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">Fonts</span>
                      </div>
                      <div className="space-y-2">
                        {brandData.fonts.map((font, index) => (
                          <div key={index} className="text-sm text-gray-900 font-medium">
                            {font}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Colors */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-3">
                        <Palette className="w-4 h-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">Colors</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div className="flex items-center space-x-2">
                          <div 
                            className="w-4 h-4 rounded border border-gray-300"
                            style={{ backgroundColor: brandData.primaryColor }}
                          ></div>
                          <span className="text-xs text-gray-600">Primary</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div 
                            className="w-4 h-4 rounded border border-gray-300"
                            style={{ backgroundColor: brandData.secondaryColor }}
                          ></div>
                          <span className="text-xs text-gray-600">Secondary</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div 
                            className="w-4 h-4 rounded border border-gray-300"
                            style={{ backgroundColor: brandData.backgroundColor }}
                          ></div>
                          <span className="text-xs text-gray-600">Background</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div 
                            className="w-4 h-4 rounded border border-gray-300"
                            style={{ backgroundColor: brandData.linkColor }}
                          ></div>
                          <span className="text-xs text-gray-600">Links</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Instructions */}
            <div className="bg-blue-50 rounded-xl border border-blue-200 p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">How it works</h3>
              <div className="space-y-3 text-sm text-blue-800">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-purple-200 rounded-full flex items-center justify-center text-blue-800 font-semibold text-xs mt-0.5">1</div>
                  <p>Enter any website URL to analyze its brand elements</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-purple-200 rounded-full flex items-center justify-center text-blue-800 font-semibold text-xs mt-0.5">2</div>
                  <p>Choose from multiple extraction methods (DOM, CSS, Screenshot, etc.)</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-purple-200 rounded-full flex items-center justify-center text-blue-800 font-semibold text-xs mt-0.5">3</div>
                  <p>AI analyzes and extracts colors, fonts, and brand elements</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-purple-200 rounded-full flex items-center justify-center text-blue-800 font-semibold text-xs mt-0.5">4</div>
                  <p>See the extracted brand applied to an email template preview</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Email Template Preview */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-purple-100 rounded-lg">
                    <Mail className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Email Template Preview</h2>
                    <p className="text-sm text-gray-600">Brand elements applied in real-time</p>
                  </div>
                </div>
                {brandData && (
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Live Preview</span>
                  </div>
                )}
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <EmailTemplate 
                  brandData={brandData} 
                  isAnalyzing={isAnalyzing} 
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
