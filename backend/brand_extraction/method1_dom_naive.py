from typing import Dict, List, Any
from collections import Counter
import re
import webcolors
from .base import BaseBrandExtractor, BrandColors, ExtractionResult, PlaywrightMixin


class DOMNaiveExtractor(BaseBrandExtractor, PlaywrightMixin):
    """Extract brand elements directly from DOM using JavaScript"""
    
    def __init__(self):
        super().__init__("DOM_Naive")
    
    async def extract_brand_elements(self, url: str, **kwargs) -> ExtractionResult:
        """Extract brand elements using DOM analysis"""
        page = None
        
        try:
            # Setup browser and navigate
            page = await self._setup_browser()
            await page.set_viewport_size({'width': 1920, 'height': 1080})
            
            self.logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=10000)
            
            # Extract fonts and colors
            fonts = await self._extract_fonts(page)
            colors = await self._extract_colors(page)
            
            # Process extracted data
            processed_fonts = self._process_fonts(fonts)
            processed_colors = self._process_colors(colors)
            
            # Create brand colors object
            brand_colors = BrandColors(
                primaryColor=processed_colors["primaryColor"],
                secondaryColor=processed_colors["secondaryColor"],
                backgroundColor=processed_colors["backgroundColor"],
                linkColor=processed_colors["linkColor"]
            )
            
            metadata = {
                "raw_fonts": fonts,
                "raw_colors": colors,
                "processing_stats": {
                    "total_fonts_found": len(fonts),
                    "total_colors_found": sum(len(color_list) for color_list in colors.values())
                }
            }
            
            return self._create_success_result(brand_colors, processed_fonts["fonts"], metadata)
            
        except Exception as e:
            self.logger.error(f"Error during DOM extraction: {str(e)}")
            return self._create_error_result(str(e))
        
        finally:
            await self._cleanup_browser()
    
    async def _extract_fonts(self, page) -> List[str]:
        """Extract font families from the page using JavaScript"""
        try:
            font_extraction_script = """
            () => {
                const fontFamilies = new Set();
                const elements = document.querySelectorAll('*');
                
                for (let element of elements) {
                    const computedStyle = window.getComputedStyle(element);
                    const fontFamily = computedStyle.fontFamily;
                    
                    if (fontFamily && fontFamily !== 'inherit') {
                        // Clean up font family names
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
            self.logger.info(f"Extracted {len(fonts)} font families")
            return fonts
            
        except Exception as e:
            self.logger.error(f"Error extracting fonts: {str(e)}")
            return ["Arial", "sans-serif"]
    
    async def _extract_colors(self, page) -> Dict[str, List[str]]:
        """Extract colors from the page using JavaScript"""
        try:
            color_extraction_script = """
            () => {
                const colors = {
                    textColors: [],
                    backgroundColors: [],
                    borderColors: [],
                    linkColors: []
                };
                
                const elements = document.querySelectorAll('*');
                
                for (let element of elements) {
                    const computedStyle = window.getComputedStyle(element);
                    
                    // Extract text colors
                    const color = computedStyle.color;
                    if (color && color !== 'rgba(0, 0, 0, 0)' && color !== 'transparent') {
                        colors.textColors.push(color);
                    }
                    
                    // Extract background colors
                    const backgroundColor = computedStyle.backgroundColor;
                    if (backgroundColor && backgroundColor !== 'rgba(0, 0, 0, 0)' && backgroundColor !== 'transparent') {
                        colors.backgroundColors.push(backgroundColor);
                    }
                    
                    // Extract border colors
                    const borderColor = computedStyle.borderColor;
                    if (borderColor && borderColor !== 'rgba(0, 0, 0, 0)' && borderColor !== 'transparent') {
                        colors.borderColors.push(borderColor);
                    }
                    
                    // Extract link colors specifically
                    if (element.tagName === 'A') {
                        colors.linkColors.push(color);
                    }
                }
                
                return colors;
            }
            """
            
            colors = await page.evaluate(color_extraction_script)
            self.logger.info(f"Extracted colors: {len(colors['textColors'])} text, "
                           f"{len(colors['backgroundColors'])} background, "
                           f"{len(colors['linkColors'])} link")
            return colors
            
        except Exception as e:
            self.logger.error(f"Error extracting colors: {str(e)}")
            return {
                "textColors": ["rgb(51, 51, 51)"],
                "backgroundColors": ["rgb(255, 255, 255)"],
                "borderColors": [],
                "linkColors": ["rgb(0, 102, 204)"]
            }
    
    def _process_fonts(self, fonts: List[str]) -> Dict[str, List[str]]:
        """Process and rank extracted fonts"""
        try:
            # Filter out generic font families and system fonts
            generic_fonts = {'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui'}
            system_fonts = {
                'Arial', 'Helvetica', 'Times', 'Courier', 'Verdana', 'Georgia', 
                'Palatino', 'Garamond', 'Bookman', 'Comic Sans MS', 'Trebuchet MS', 
                'Arial Black', 'Impact'
            }
            
            # Prioritize custom/web fonts over system fonts
            custom_fonts = []
            fallback_fonts = []
            
            for font in fonts:
                if font.lower() not in generic_fonts:
                    if font in system_fonts:
                        fallback_fonts.append(font)
                    else:
                        custom_fonts.append(font)
            
            # Use custom fonts first, then fallback to system fonts
            final_fonts = custom_fonts[:2] if custom_fonts else fallback_fonts[:2]
            
            # Ensure we always have at least 2 fonts
            if len(final_fonts) < 2:
                final_fonts.extend(['Helvetica', 'Arial', 'sans-serif'])
                final_fonts = final_fonts[:2]
            
            return {"fonts": final_fonts}
            
        except Exception as e:
            self.logger.error(f"Error processing fonts: {str(e)}")
            return {"fonts": ["Arial", "sans-serif"]}
    
    def _process_colors(self, colors: Dict[str, List[str]]) -> Dict[str, str]:
        """Process and rank extracted colors to determine brand colors"""
        try:
            # Convert all colors to hex format
            all_colors = []
            
            for color_type, color_list in colors.items():
                for color in color_list:
                    hex_color = self._convert_to_hex(color)
                    if hex_color:
                        all_colors.append(hex_color)
            
            color_counts = Counter(all_colors)
            
            # Remove very common colors (white, black, transparent)
            excluded_colors = {'#FFFFFF', '#000000', '#TRANSPARENT'}
            filtered_colors = {color: count for color, count in color_counts.items() 
                             if color not in excluded_colors}
            
            # Get most common colors
            most_common = list(filtered_colors.keys())[:10] if filtered_colors else ['#333333']
            
            # Determine specific color roles
            background_colors = [self._convert_to_hex(c) for c in colors.get('backgroundColors', [])]
            link_colors = [self._convert_to_hex(c) for c in colors.get('linkColors', [])]
            
            bg_color = self._get_most_common_color(background_colors, '#FFFFFF')
            link_color = self._get_most_common_color(link_colors, '#0066CC')
            
            primary_color = most_common[0] if most_common else '#333333'
            secondary_color = most_common[1] if len(most_common) > 1 else '#666666'
            if self._get_contrast_ratio(secondary_color, bg_color) < 3:
                secondary_color = '#333333' if bg_color != '#333333' else '#FFFFFF'
            
            return {
                "primaryColor": primary_color,
                "secondaryColor": secondary_color,
                "backgroundColor": bg_color,
                "linkColor": link_color
            }
            
        except Exception as e:
            self.logger.error(f"Error processing colors: {str(e)}")
            return {
                "primaryColor": "#333333",
                "secondaryColor": "#666666",
                "backgroundColor": "#FFFFFF",
                "linkColor": "#0066CC"
            }
    
    def _convert_to_hex(self, color: str) -> str:
        """Convert various color formats to hex"""
        try:
            color = color.strip()
            
            # Already hex
            if color.startswith('#'):
                return color.upper()
            
            # RGB format
            if color.startswith('rgb'):
                # Extract numbers from rgb(r, g, b) or rgba(r, g, b, a)
                numbers = re.findall(r'\d+', color)
                if len(numbers) >= 3:
                    r, g, b = int(numbers[0]), int(numbers[1]), int(numbers[2])
                    return f"#{r:02X}{g:02X}{b:02X}"
            
            # Named colors
            try:
                hex_color = webcolors.name_to_hex(color)
                return hex_color.upper()
            except ValueError:
                pass
            
            return None
            
        except Exception:
            return None
    
    def _get_most_common_color(self, color_list: List[str], default: str) -> str:
        """Get the most common color from a list"""
        filtered_colors = [c for c in color_list if c and c != '#FFFFFF' and c != '#000000']
        if not filtered_colors:
            return default
        
        color_counts = Counter(filtered_colors)
        return color_counts.most_common(1)[0][0] if color_counts else default
    
    def _get_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors"""
        try:
            def luminance(hex_color):
                # Convert hex to RGB
                hex_color = hex_color.lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                
                # Convert to relative luminance
                rgb_norm = [c / 255.0 for c in rgb]
                rgb_linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb_norm]
                return 0.2126 * rgb_linear[0] + 0.7152 * rgb_linear[1] + 0.0722 * rgb_linear[2]
            
            lum1 = luminance(color1)
            lum2 = luminance(color2)
            
            lighter = max(lum1, lum2)
            darker = min(lum1, lum2)
            
            return (lighter + 0.05) / (darker + 0.05)
            
        except Exception:
            return 1.0
            
