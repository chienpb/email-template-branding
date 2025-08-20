from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
class BrandColors(BaseModel):
    primaryColor: str
    secondaryColor: str
    backgroundColor: str
    linkColor: str
    

class ExtractionResult(BaseModel):
    fonts: List[str]
    primaryColor: str
    secondaryColor: str
    backgroundColor: str
    linkColor: str
    success: bool
    message: str
    method: str
    metadata: Optional[Dict[str, Any]] = None

class BaseBrandExtractor(ABC):
    
    def __init__(self, method_name: str):
        self.method_name = method_name
        self.logger = logging.getLogger(f"{__name__}.{method_name}")
    
    @abstractmethod
    async def extract_brand_elements(self, url: str, **kwargs) -> ExtractionResult:
        """
        Extract brand elements from a website URL
        
        Args:
            url: The website URL to analyze
            **kwargs: Method-specific parameters
            
        Returns:
            ExtractionResult with standardized brand data
        """
        pass
    
    def _create_success_result(self, colors: BrandColors, fonts: List[str], 
                              metadata: Optional[Dict[str, Any]] = None) -> ExtractionResult:
        return ExtractionResult(
            fonts=fonts,
            primaryColor=colors.primaryColor,
            secondaryColor=colors.secondaryColor,
            backgroundColor=colors.backgroundColor,
            linkColor=colors.linkColor,
            success=True,
            message=f"Brand extraction completed successfully using {self.method_name}",
            method=self.method_name,
            metadata=metadata
        )
    
    def _create_error_result(self, error_message: str, 
                            metadata: Optional[Dict[str, Any]] = None) -> ExtractionResult:
        return ExtractionResult(
            fonts=["Arial", "sans-serif"],
            primaryColor="#333333",
            secondaryColor="#666666",
            backgroundColor="#FFFFFF",
            linkColor="#0066CC",
            success=False,
            message=f"{self.method_name} failed: {error_message}",
            method=self.method_name,
            metadata=metadata
        )


class PlaywrightMixin:
    async def _setup_browser(self):
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        launch_options = {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        }
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        return await self.browser.new_page()
    
    async def _cleanup_browser(self):
        if hasattr(self, 'browser') and self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()
