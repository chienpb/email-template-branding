export interface BrandAnalysis {
  fonts: string[]
  primaryColor: string
  secondaryColor: string
  backgroundColor: string
  linkColor: string
  success: boolean
  message: string
  method: string
  metadata?: Record<string, any>
}

export interface ExtractionMethod {
  id: string
  name: string
  description: string
  pros: string
  cons: string
}

export interface ComparisonResult {
  results: Record<string, BrandAnalysis>
  url: string
}
