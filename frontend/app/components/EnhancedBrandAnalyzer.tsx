'use client'

import { useState } from 'react'
import { Loader2, Search, AlertCircle, Settings } from 'lucide-react'
import { BrandAnalysis, ExtractionMethod } from '../types/brand'

interface EnhancedBrandAnalyzerProps {
  onAnalysisStart: () => void
  onAnalysisComplete: (data: BrandAnalysis | null, errorMessage?: string) => void
  isAnalyzing: boolean
}

export default function EnhancedBrandAnalyzer({
  onAnalysisStart,
  onAnalysisComplete,
  isAnalyzing
}: EnhancedBrandAnalyzerProps) {
  const [url, setUrl] = useState('')
  const [selectedMethod, setSelectedMethod] = useState('dom_naive')

  // Fallback list of methods, already ordered 4 -> 3 -> 2 -> 1
  const defaultMethods: ExtractionMethod[] = [
    {
      id: 'screenshot_palette',
      name: 'Method 4: Screenshot Palette',
      description: 'Takes a screenshot and extracts a color palette to infer brand colors.',
      pros: 'Robust against obfuscated CSS; good visual approximation of brand colors.',
      cons: 'Requires headless browser; slower; may be affected by animations or modals.'
    },
    {
      id: 'screenshot_direct',
      name: 'Method 3: Screenshot Direct',
      description: 'Screenshots and directly samples color regions from rendered page.',
      pros: 'Captures final rendered state; resilient to dynamic styling.',
      cons: 'May pick non-brand imagery; needs careful sampling; slower than DOM.'
    },
    {
      id: 'css_llm',
      name: 'Method 2: CSS + LLM',
      description: 'Parses CSS and uses an LLM to infer primary/secondary/brand colors.',
      pros: 'More intelligent color inference than naive parsing; context-aware.',
      cons: 'Depends on LLM quality; may incur API costs; slower than naive.'
    },
    {
      id: 'dom_naive',
      name: 'Method 1: DOM Naive',
      description: 'Heuristically inspects DOM and CSS for common brand color patterns.',
      pros: 'Fast; no external dependencies; simple and lightweight.',
      cons: 'Less accurate; brittle to complex sites; may miss dynamic styles.'
    }
  ]

  const rankById: Record<string, number> = {
    screenshot_palette: 4,
    screenshot_direct: 3,
    css_llm: 2,
    dom_naive: 1
  }

  const sortMethods = (methods: ExtractionMethod[]) =>
    methods.slice().sort((a, b) => (rankById[b.id] ?? 0) - (rankById[a.id] ?? 0))

  const [availableMethods, setAvailableMethods] = useState<ExtractionMethod[]>(sortMethods(defaultMethods))

  const [validationError, setValidationError] = useState<string | null>(null)

  // Hardcoded methods for PoC (no network fetch)

  const validateUrl = (inputUrl: string): boolean => {
    try {
      const urlObj = new URL(inputUrl)
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:'
    } catch {
      return false
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!url.trim()) {
      setValidationError('Please enter a URL')
      return
    }

    if (!validateUrl(url)) {
      setValidationError('Please enter a valid URL (including http:// or https://)')
      return
    }

    setValidationError(null)
    onAnalysisStart()

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url, 
          method: selectedMethod 
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data: BrandAnalysis = await response.json()
      onAnalysisComplete(data)
    } catch (error) {
      console.error('Analysis error:', error)
      onAnalysisComplete(null, error instanceof Error ? error.message : 'An unexpected error occurred')
    }
  }



  const selectedMethodInfo = availableMethods.find(m => m.id === selectedMethod)

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* URL Input */}
        <div className="space-y-2">
          <label htmlFor="url" className="block text-sm font-medium text-gray-700">
            Website URL
          </label>
          <div className="relative">
            <input
              id="url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isAnalyzing}
            />
            <Search className="absolute left-3 top-3.5 h-4 w-4 text-gray-400" />
          </div>
          {validationError && (
            <div className="flex items-center space-x-2 text-red-600 text-sm">
              <AlertCircle className="h-4 w-4" />
              <span>{validationError}</span>
            </div>
          )}
        </div>

        {/* Method Selection */}
        <div className="space-y-2">
          <div>
            <label htmlFor="method" className="block text-sm font-medium text-gray-700">
              Extraction Method
            </label>
          </div>
          <select
            id="method"
            value={selectedMethod}
            onChange={(e) => setSelectedMethod(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isAnalyzing}
          >
            {availableMethods.map((method) => (
              <option key={method.id} value={method.id}>
                {method.name}
              </option>
            ))}
          </select>
        </div>

        {/* Action Button */}
        <div>
          <button
            type="submit"
            disabled={isAnalyzing || !url.trim()}
            className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Settings className="h-4 w-4" />
                <span>Analyze with {selectedMethodInfo?.name || 'Selected Method'}</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
