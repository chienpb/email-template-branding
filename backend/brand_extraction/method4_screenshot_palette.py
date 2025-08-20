import time
import base64
import io
from typing import Dict, List
from PIL import Image, ImageDraw, ImageFont
from colorthief import ColorThief
from openai import OpenAI
from utils import IMAGE_PALETTE_PROMPT

from .base import BaseBrandExtractor, BrandColors, ExtractionResult, PlaywrightMixin
class ScreenshotPaletteExtractor(BaseBrandExtractor, PlaywrightMixin):
    """Extract brand elements using screenshot + color palette + LLM analysis"""
    
    def __init__(self):
        super().__init__("Screenshot_Palette")
    
    async def extract_brand_elements(self, url: str, **kwargs) -> ExtractionResult:
        """Extract brand elements using screenshot and palette analysis"""

        viewport_width = kwargs.get('viewport_width', 1920)
        viewport_height = kwargs.get('viewport_height', 1080)
        quality = kwargs.get('quality', 90)
        wait_for_selector = kwargs.get('wait_for_selector')
        wait_timeout = 15000
        num_colors = kwargs.get('num_colors', 10)
        
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
            
            nav_start = time.time()
            self.logger.info(f"Taking screenshot with palette for {url}")
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=wait_timeout)
            except Exception as e:
                self.logger.warning(f"Timeout navigating to {url}: {str(e)}")
            nav_time = time.time() - nav_start
            timing_info['page_navigation_seconds'] = round(nav_time, 3)

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
                full_page=False
            )
            screenshot_time = time.time() - screenshot_start
            timing_info['screenshot_capture_seconds'] = round(screenshot_time, 3)
            
            # Extract fonts (reuse DOM method for font extraction)
            fonts = await self._extract_fonts(page)
            processed_fonts = self._process_fonts(fonts)
            
            # Extract colors from screenshot
            color_start = time.time()
            extracted_colors = self._extract_colors_from_screenshot(screenshot_bytes, num_colors)
            color_time = time.time() - color_start
            timing_info['color_extraction_seconds'] = round(color_time, 3)
            
            # Create palette image
            palette_start = time.time()
            combined_image_bytes = self._create_palette_image(screenshot_bytes, extracted_colors)
            palette_time = time.time() - palette_start
            timing_info['palette_creation_seconds'] = round(palette_time, 3)
            
            # LLM analysis
            llm_start = time.time()
            brand_colors = await self._analyze_with_llm(combined_image_bytes)
            llm_time = time.time() - llm_start
            timing_info['llm_analysis_seconds'] = round(llm_time, 3)
            
            # Create metadata
            total_time = time.time() - start_time
            timing_info['total_process_seconds'] = round(total_time, 3)
            
            metadata = {
                "extracted_colors": extracted_colors,
                "combined_image_size_bytes": len(combined_image_bytes),
                "original_screenshot_size_bytes": len(screenshot_bytes),
                "timing": timing_info,
                "num_colors": num_colors,
                "screenshot_options": {
                    "viewport_width": viewport_width,
                    "viewport_height": viewport_height,
                    "full_page": False,
                    "quality": quality
                }
            }
            
            return self._create_success_result(brand_colors, processed_fonts["fonts"], metadata)
            
        except Exception as e:
            total_time = time.time() - start_time
            timing_info['total_process_seconds'] = round(total_time, 3)
            self.logger.error(f"Error during screenshot palette extraction: {str(e)}")
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
    
    def _extract_colors_from_screenshot(self, screenshot_bytes: bytes, num_colors: int = 10) -> List[str]:
        """Extract top colors from screenshot using ColorThief"""
        try:
            # Create a BytesIO object from the screenshot bytes
            image_stream = io.BytesIO(screenshot_bytes)
            
            # Use ColorThief to extract colors
            color_thief = ColorThief(image_stream)
            
            # Get the dominant colors as RGB tuples
            dominant_colors = color_thief.get_palette(color_count=num_colors, quality=1)
            
            # Convert RGB tuples to hex codes
            hex_colors = []
            for rgb in dominant_colors:
                hex_color = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
                hex_colors.append(hex_color)
            
            self.logger.info(f"Extracted {len(hex_colors)} colors: {hex_colors}")
            return hex_colors
            
        except Exception as e:
            self.logger.error(f"Error extracting colors from screenshot: {str(e)}")
            # Return some default colors if extraction fails
            return ["#FF5733", "#33FF57", "#3357FF", "#FFD700", "#800080", 
                   "#FF1493", "#00CED1", "#32CD32", "#FF6347", "#9370DB"]
    
    def _create_palette_image(self, screenshot_bytes: bytes, colors: List[str]) -> bytes:
        """Create a palette strip and combine it with the original screenshot"""
        try:
            image_stream = io.BytesIO(screenshot_bytes)
            img = Image.open(image_stream).convert("RGB")
            width = img.width
            palette_height = int(img.height * 0.2) 
            
            palette = Image.new("RGB", (width, palette_height), "white")
            draw = ImageDraw.Draw(palette)
            
            font = ImageFont.load_default(size=palette_height // 6)
            
            block_width = width // len(colors)
            
            for i, hex_color in enumerate(colors):
                x0 = i * block_width
                x1 = (i + 1) * block_width
                
                # Draw color block
                draw.rectangle([x0, 0, x1, palette_height], fill=hex_color)
                
                # Add text in middle
                try:
                    bbox = draw.textbbox((0, 0), hex_color, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                except AttributeError:
                    text_w, text_h = draw.textsize(hex_color, font=font)
                
                text_x = x0 + (block_width - text_w) // 2
                text_y = (palette_height - text_h) // 2
                
                # Choose text color based on background brightness
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
                brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000
                text_color = "white" if brightness < 128 else "black"
                
                draw.text((text_x, text_y), hex_color, fill=text_color, font=font)
            
            combined = Image.new("RGB", (width, img.height + palette_height))
            combined.paste(img, (0, 0))
            combined.paste(palette, (0, img.height))
            
            output_stream = io.BytesIO()
            combined.save(output_stream, format='JPEG', quality=90)
            combined_bytes = output_stream.getvalue()
            
            self.logger.info(f"Created combined image with palette. Size: {len(combined_bytes)} bytes")
            return combined_bytes
            
        except Exception as e:
            self.logger.error(f"Error creating palette image: {str(e)}")
            return screenshot_bytes
    
    async def _analyze_with_llm(self, combined_image_bytes: bytes) -> BrandColors:
        """Analyze the combined image using GPT-4.1"""
        try:
            client = OpenAI()

            response = client.responses.parse(
                model="gpt-4.1",
                temperature=0.4,
                input=[
                {
                    "role": "user",
                    "content": [
                        { "type": "input_text", "text": IMAGE_PALETTE_PROMPT },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{base64.b64encode(combined_image_bytes).decode('utf-8')}",
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
