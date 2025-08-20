from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import logging
from brand_extraction.analyzer import BrandAnalyzer, ExtractionMethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Email Template Branding API",
    description="Extract brand colors and fonts from websites",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: HttpUrl
    method: Optional[ExtractionMethod] = ExtractionMethod.DOM_NAIVE

class ScreenshotWithPaletteRequest(BaseModel):
    url: HttpUrl
    viewport_width: Optional[int] = 1920
    viewport_height: Optional[int] = 1080
    full_page: Optional[bool] = True
    quality: Optional[int] = 90
    wait_for_selector: Optional[str] = None
    wait_timeout: Optional[int] = 30000
    num_colors: Optional[int] = 10

class BrandAnalysisResponse(BaseModel):
    fonts: List[str]
    primaryColor: str
    secondaryColor: str
    backgroundColor: str
    linkColor: str
    success: bool
    message: str
    method: str
    metadata: Optional[Dict[str, Any]] = None

class ScreenshotWithPaletteResponse(BaseModel):
    combined_image_base64: Optional[str]
    original_screenshot_base64: Optional[str]
    extracted_colors: List[str]
    combined_image_size_bytes: int
    original_screenshot_size_bytes: int
    viewport: Dict[str, int]
    page_dimensions: Optional[Dict[str, int]]
    full_page: bool
    quality: int
    num_colors: int
    url: str
    timing: Dict[str, float]
    success: bool
    message: str

@app.get("/")
async def root():
    return {"message": "AI Email Template Branding API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "brand-analyzer"}

@app.post("/analyze", response_model=BrandAnalysisResponse)
async def analyze_brand(request: AnalyzeRequest):
    """
    Analyze a website's brand elements using the specified method
    """
    try:
        logger.info(f"Analyzing brand for URL: {request.url} using method: {request.method}")
        
        analyzer = BrandAnalyzer()
        result = await analyzer.analyze_website(str(request.url), request.method)
        
        if result.success:
            logger.info(f"Successfully analyzed {request.url} using {request.method}")
            return BrandAnalysisResponse(
                fonts=result.fonts,
                primaryColor=result.primaryColor,
                secondaryColor=result.secondaryColor,
                backgroundColor=result.backgroundColor,
                linkColor=result.linkColor,
                success=result.success,
                message=result.message,
                method=result.method,
                metadata=result.metadata
            )
        else:
            logger.error(f"Failed to analyze {request.url}: {result.message}")
            raise HTTPException(
                status_code=400,
                detail=result.message
            )
            
    except Exception as e:
        logger.error(f"Error analyzing {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/screenshot-with-palette", response_model=ScreenshotWithPaletteResponse)
async def take_screenshot_with_palette(request: ScreenshotWithPaletteRequest):
    """
    Take a screenshot and add a color palette extracted from the image (Legacy endpoint)
    """
    try:
        logger.info(f"Taking screenshot with palette for URL: {request.url}")
        
        analyzer = BrandAnalyzer()
        result = await analyzer.take_screenshot_with_palette_legacy(
            url=str(request.url),
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            full_page=request.full_page,
            quality=request.quality,
            wait_for_selector=request.wait_for_selector,
            wait_timeout=request.wait_timeout,
            num_colors=request.num_colors
        )
        
        if result["success"]:
            logger.info(f"Successfully took screenshot with palette for {request.url}")
            logger.info(f"Extracted colors: {result.get('extracted_colors', [])}")
            return ScreenshotWithPaletteResponse(**result)
        else:
            logger.error(f"Failed to take screenshot with palette for {request.url}: {result.get('message', 'Unknown error')}")
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Failed to take screenshot with palette")
            )
            
    except Exception as e:
        logger.error(f"Error taking screenshot with palette for {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
