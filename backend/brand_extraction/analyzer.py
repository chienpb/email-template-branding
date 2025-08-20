"""
Main Brand Analyzer orchestrator class
Coordinates different extraction methods and provides a unified interface
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import logging
from .base import ExtractionResult
from .method1_dom_naive import DOMNaiveExtractor
from .method4_screenshot_palette import ScreenshotPaletteExtractor
from .method2_css_llm import CSSLLMExtractor
from .method3_screenshot_direct import ScreenshotDirectExtractor

logger = logging.getLogger(__name__)


class ExtractionMethod(str, Enum):
    DOM_NAIVE = "dom_naive"
    SCREENSHOT_PALETTE = "screenshot_palette"
    CSS_LLM = "css_llm"
    SCREENSHOT_DIRECT = "screenshot_direct"


class BrandAnalyzer:
    
    def __init__(self):
        self.extractors = {
            ExtractionMethod.DOM_NAIVE: DOMNaiveExtractor(),
            ExtractionMethod.SCREENSHOT_PALETTE: ScreenshotPaletteExtractor(),
            ExtractionMethod.CSS_LLM: CSSLLMExtractor(),
            ExtractionMethod.SCREENSHOT_DIRECT: ScreenshotDirectExtractor()
        }
    
    async def analyze_website(self, url: str, method: Optional[ExtractionMethod] = None, **kwargs) -> ExtractionResult:
        if method is None:
            method = ExtractionMethod.DOM_NAIVE
            
        try:
            logger.info(f"Analyzing {url} using method: {method}")
            
            if method not in self.extractors:
                raise ValueError(f"Unknown extraction method: {method}")
            
            extractor = self.extractors[method]
            result = await extractor.extract_brand_elements(url, **kwargs)
            
            logger.info(f"Analysis completed for {url} using {method}: success={result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {url} with method {method}: {str(e)}")
            return ExtractionResult(
                fonts=["Arial", "sans-serif"],
                primaryColor="#333333",
                secondaryColor="#666666",
                backgroundColor="#FFFFFF",
                linkColor="#0066CC",
                success=False,
                message=f"Analysis failed: {str(e)}",
                method=method.value if method else "unknown",
                metadata={"error": str(e)}
            )