import time
from typing import Dict, List
from google import genai
from google.genai import types
import base64
from openai import OpenAI
from utils import IMAGE_PROMPT
from .base import BaseBrandExtractor, BrandColors, ExtractionResult, PlaywrightMixin


class ScreenshotDirectExtractor(BaseBrandExtractor, PlaywrightMixin):
    """Extract brand elements by feeding screenshot directly to LLM"""
    
    def __init__(self):
        super().__init__("Screenshot_Direct")
    
    async def extract_brand_elements(self, url: str, **kwargs) -> ExtractionResult:
        """Extract brand elements using direct screenshot analysis"""

        viewport_width = kwargs.get('viewport_width', 1920)
        viewport_height = kwargs.get('viewport_height', 1080)
        full_page = kwargs.get('full_page', True)
        quality = kwargs.get('quality', 90)
        wait_for_selector = kwargs.get('wait_for_selector')
        wait_timeout = 7000
        
        page = None
        start_time = time.time()
        timing_info = {}
        
        try:
            # Setup browser
            setup_start = time.time()
            page = await self._setup_browser()
            await page.set_viewport_size({'width': viewport_width, 'height': viewport_height})
            setup_time = time.time() - setup_start
            timing_info['browser_setup_seconds'] = round(setup_time, 3)
            
            # Navigate to page
            nav_start = time.time()
            self.logger.info(f"Taking screenshot for direct analysis of {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=wait_timeout)
            nav_time = time.time() - nav_start
            timing_info['page_navigation_seconds'] = round(nav_time, 3)
            
            # Optional selector wait
            if wait_for_selector:
                wait_start = time.time()
                try:
                    await page.wait_for_selector(wait_for_selector, timeout=wait_timeout)
                    wait_time = time.time() - wait_start
                    timing_info['selector_wait_seconds'] = round(wait_time, 3)
                except Exception as e:
                    wait_time = time.time() - wait_start
                    timing_info['selector_wait_seconds'] = round(wait_time, 3)
                    self.logger.warning(f"Timeout waiting for selector '{wait_for_selector}': {str(e)}")
            
            # Take screenshot
            screenshot_start = time.time()
            screenshot_bytes = await page.screenshot(
                type='jpeg',
                quality=quality,
                full_page=full_page
            )
            screenshot_time = time.time() - screenshot_start
            timing_info['screenshot_capture_seconds'] = round(screenshot_time, 3)
            
            # Extract fonts (reuse DOM method for font extraction)
            fonts = await self._extract_fonts(page)
            processed_fonts = self._process_fonts(fonts)
            
            # LLM analysis of raw screenshot
            llm_start = time.time()
            brand_colors = await self._analyze_screenshot_with_llm(screenshot_bytes, url)
            llm_time = time.time() - llm_start
            timing_info['llm_analysis_seconds'] = round(llm_time, 3)
            
            # Create metadata
            total_time = time.time() - start_time
            timing_info['total_process_seconds'] = round(total_time, 3)
            
            metadata = {
                "screenshot_size_bytes": len(screenshot_bytes),
                "timing": timing_info,
                "screenshot_options": {
                    "viewport_width": viewport_width,
                    "viewport_height": viewport_height,
                    "full_page": full_page,
                    "quality": quality
                }
            }
            
            return self._create_success_result(brand_colors, processed_fonts["fonts"], metadata)
            
        except Exception as e:
            total_time = time.time() - start_time
            timing_info['total_process_seconds'] = round(total_time, 3)
            self.logger.error(f"Error during screenshot direct extraction: {str(e)}")
            return self._create_error_result(str(e), {"timing": timing_info})
        
        finally:
            await self._cleanup_browser()
    
    async def _extract_fonts(self, page) -> List[str]:
        """Extract font families from the page using JavaScript (reused from Method 1)"""
        try:
            font_extraction_script = """
            () => {
                const fontFamilies = new Set();
                const elements = document.querySelectorAll('*');
                
                for (let element of elements) {
                    const computedStyle = window.getComputedStyle(element);
                    const fontFamily = computedStyle.fontFamily;
                    
                    if (fontFamily && fontFamily !== 'inherit') {
                        const fonts = fontFamily.split(',').map(font => 
                            font.trim().replace(/['"]/g, '')
                        );
                        fonts.forEach(font => {
                            if (font && !font.includes('inherit') && !font.includes('initial')) {
                                fontFamilies.add(font);
                            }
                        });
                    }
                }
                
                return Array.from(fontFamilies);
            }
            """
            
            fonts = await page.evaluate(font_extraction_script)
            return fonts
            
        except Exception as e:
            self.logger.error(f"Error extracting fonts: {str(e)}")
            return ["Arial", "sans-serif"]
    
    def _process_fonts(self, fonts: List[str]) -> Dict[str, List[str]]:
        """Process and rank extracted fonts (reused from Method 1)"""
        try:
            generic_fonts = {'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui'}
            system_fonts = {
                'Arial', 'Helvetica', 'Times', 'Courier', 'Verdana', 'Georgia', 
                'Palatino', 'Garamond', 'Bookman', 'Comic Sans MS', 'Trebuchet MS', 
                'Arial Black', 'Impact'
            }
            
            custom_fonts = []
            fallback_fonts = []
            
            for font in fonts:
                if font.lower() not in generic_fonts:
                    if font in system_fonts:
                        fallback_fonts.append(font)
                    else:
                        custom_fonts.append(font)
            
            final_fonts = custom_fonts[:2] if custom_fonts else fallback_fonts[:2]
            
            if len(final_fonts) < 2:
                final_fonts.extend(['Helvetica', 'Arial', 'sans-serif'])
                final_fonts = final_fonts[:2]
            
            return {"fonts": final_fonts}
            
        except Exception as e:
            self.logger.error(f"Error processing fonts: {str(e)}")
            return {"fonts": ["Arial", "sans-serif"]}
    
    async def _analyze_screenshot_with_llm(self, screenshot_bytes: bytes, url: str) -> BrandColors:
        """Analyze the screenshot directly using GPT-4.1"""
        try:
            client = OpenAI()

            response = client.responses.parse(
                model="gpt-4.1",
                temperature=0.7,
                input=[
                {
                    "role": "user",
                    "content": [
                        { "type": "input_text", "text": IMAGE_PROMPT },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{base64.b64encode(screenshot_bytes).decode('utf-8')}",
                        },
                    ],
                }
            ],
                text_format=BrandColors,
            )

            self.logger.info(f"LLM Usage: {response.usage}")

            return response.output_parsed
            
        except Exception as e:
            self.logger.error(f"Error in LLM analysis: {str(e)}")

            return BrandColors(
                primaryColor="#333333",
                secondaryColor="#666666",
                backgroundColor="#FFFFFF",
                linkColor="#0066CC"
            )