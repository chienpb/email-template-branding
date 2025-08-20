from typing import Dict, List, Any, Optional
from openai import OpenAI
from .base import BaseBrandExtractor, BrandColors, ExtractionResult, PlaywrightMixin


class CSSLLMExtractor(BaseBrandExtractor, PlaywrightMixin):
    """Extract brand elements using CSS/HTML analysis + LLM"""
    
    def __init__(self):
        super().__init__("CSS_LLM")
    
    async def extract_brand_elements(self, url: str, **kwargs) -> ExtractionResult:
        """Extract brand elements using CSS/HTML + LLM analysis"""
        page = None
        
        try:
            # Setup browser and navigate
            page = await self._setup_browser()
            await page.set_viewport_size({'width': 1920, 'height': 1080})
            
            self.logger.info(f"Analyzing CSS/HTML for {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=7000)
            
            # Extract fonts
            fonts = await self._extract_fonts(page)
            processed_fonts = self._process_fonts(fonts)
            
            # Extract CSS and HTML content with color information
            css_content = await self._extract_css_content(page)
            html_color_content = await self._extract_html_color_content(page)
            computed_styles = await self._extract_computed_styles(page)
            
            # Combine all color information
            color_data = {
                "css_rules": css_content,
                "html_colors": html_color_content,
                "computed_styles": computed_styles,
                "url": url
            }
            
            # Analyze with LLM
            brand_colors = await self._analyze_colors_with_llm(color_data)
            
            metadata = {
                "css_rules_count": len(css_content),
                "html_color_elements_count": len(html_color_content),
                "computed_styles_count": len(computed_styles),
                "color_data": color_data  
            }
            
            return self._create_success_result(brand_colors, processed_fonts["fonts"], metadata)
            
        except Exception as e:
            self.logger.error(f"Error during CSS LLM extraction: {str(e)}")
            return self._create_error_result(str(e))
        
        finally:
            await self._cleanup_browser()
    
    async def _extract_fonts(self, page) -> List[str]:
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
    
    async def _extract_css_content(self, page) -> List[Dict[str, str]]:
        """Extract CSS rules that contain color properties"""
        try:
            css_extraction_script = """
            () => {
                const colorRules = [];
                const sheets = Array.from(document.styleSheets);
                
                for (let sheet of sheets) {
                    try {
                        const rules = Array.from(sheet.cssRules || sheet.rules || []);
                        
                        for (let rule of rules) {
                            if (rule.style) {
                                const cssText = rule.cssText;
                                const selector = rule.selectorText;
                                
                                // Check if rule contains color properties
                                const colorProps = ['color', 'background-color', 'background', 'border-color', 'fill', 'stroke'];
                                let hasColor = false;
                                
                                for (let prop of colorProps) {
                                    if (rule.style[prop] || cssText.includes(prop + ':')) {
                                        hasColor = true;
                                        break;
                                    }
                                }
                                
                                if (hasColor && selector) {
                                    colorRules.push({
                                        selector: selector,
                                        cssText: cssText,
                                        color: rule.style.color || '',
                                        backgroundColor: rule.style.backgroundColor || '',
                                        borderColor: rule.style.borderColor || ''
                                    });
                                }
                            }
                        }
                    } catch (e) {
                        // Skip sheets that can't be accessed (CORS)
                        continue;
                    }
                }
                
                return colorRules;
            }
            """
            
            css_rules = await page.evaluate(css_extraction_script)
            self.logger.info(f"Extracted {len(css_rules)} CSS color rules")
            return css_rules
            
        except Exception as e:
            self.logger.error(f"Error extracting CSS content: {str(e)}")
            return []
    
    async def _extract_html_color_content(self, page) -> List[Dict[str, str]]:
        """Extract HTML elements with inline color styles or color-related attributes"""
        try:
            html_extraction_script = """
            () => {
                const colorElements = [];
                const elements = document.querySelectorAll('*[style], *[color], *[bgcolor]');
                
                for (let element of elements) {
                    const style = element.getAttribute('style') || '';
                    const color = element.getAttribute('color') || '';
                    const bgcolor = element.getAttribute('bgcolor') || '';
                    const tagName = element.tagName.toLowerCase();
                    const className = element.className || '';
                    const id = element.id || '';
                    
                    // Check if element has color-related attributes or styles
                    if (style.includes('color') || color || bgcolor) {
                        colorElements.push({
                            tagName: tagName,
                            className: className,
                            id: id,
                            style: style,
                            color: color,
                            bgcolor: bgcolor,
                            text: element.textContent ? element.textContent.substring(0, 100) : ''
                        });
                    }
                }
                
                return colorElements;
            }
            """
            
            html_elements = await page.evaluate(html_extraction_script)
            self.logger.info(f"Extracted {len(html_elements)} HTML elements with color attributes")
            return html_elements
            
        except Exception as e:
            self.logger.error(f"Error extracting HTML color content: {str(e)}")
            return []
    
    async def _extract_computed_styles(self, page) -> List[Dict[str, str]]:
        """Extract computed styles for key elements (headers, buttons, links, etc.)"""
        try:
            computed_styles_script = """
            () => {
                const computedStyles = [];
                const selectors = [
                    'h1, h2, h3, h4, h5, h6',
                    'a',
                    'button',
                    '.btn, [class*="button"]',
                    '[class*="primary"], [class*="secondary"]',
                    'nav',
                    'header',
                    'footer',
                    '.logo, [class*="logo"]',
                    '[class*="brand"]'
                ];
                
                for (let selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    
                    for (let i = 0; i < Math.min(elements.length, 10); i++) { // Limit to 10 per selector
                        const element = elements[i];
                        const computedStyle = window.getComputedStyle(element);
                        
                        computedStyles.push({
                            selector: selector,
                            tagName: element.tagName.toLowerCase(),
                            className: element.className || '',
                            id: element.id || '',
                            color: computedStyle.color,
                            backgroundColor: computedStyle.backgroundColor,
                            borderColor: computedStyle.borderColor,
                            fontFamily: computedStyle.fontFamily,
                            text: element.textContent ? element.textContent.substring(0, 50) : ''
                        });
                    }
                }
                
                return computedStyles;
            }
            """
            
            computed_styles = await page.evaluate(computed_styles_script)
            self.logger.info(f"Extracted {len(computed_styles)} computed styles")
            return computed_styles
            
        except Exception as e:
            self.logger.error(f"Error extracting computed styles: {str(e)}")
            return []
    
    async def _analyze_colors_with_llm(self, color_data: Dict[str, Any]) -> BrandColors:
        try:
            CSS_LLM_PROMPT = self._create_css_analysis_prompt(color_data)
            
            client = OpenAI()

            response = client.responses.parse(
                model="gpt-4.1",
                temperature=0.7,
                input=[
                {
                    "role": "user",
                    "content": [
                        { "type": "input_text", "text": CSS_LLM_PROMPT },
                    ],
                },
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
    
    def _create_css_analysis_prompt(self, color_data: Dict[str, Any]) -> str:
        
        # Summarize the data for the prompt
        css_rules_summary = []
        for rule in color_data["css_rules"][:20]:  # Limit to top 20 rules
            css_rules_summary.append(f"Selector: {rule['selector']}, Colors: {rule['color']}, BG: {rule['backgroundColor']}")
        
        html_elements_summary = []
        for element in color_data["html_colors"][:20]:  # Limit to top 20 elements
            html_elements_summary.append(f"Tag: {element['tagName']}, Style: {element['style']}, Color: {element['color']}")
        
        computed_styles_summary = []
        for style in color_data["computed_styles"][:30]:  # Limit to top 30 styles
            computed_styles_summary.append(f"Element: {style['tagName']}.{style['className']}, Color: {style['color']}, BG: {style['backgroundColor']}")
        
        prompt = f"""
You are a brand color expert analyzing a website's CSS and HTML to extract brand colors.

## CSS Rules with Colors:
{chr(10).join(css_rules_summary)}

## HTML Elements with Color Attributes:
{chr(10).join(html_elements_summary)}

## Computed Styles for Key Elements:
{chr(10).join(computed_styles_summary)}

Based on this CSS and HTML analysis, determine the brand colors:

1. **primaryColor**: The main brand accent color
   - Look for the most prominent brand color in logos, headers, primary buttons
   - This should be the color that represents the brand most strongly
   - Often used in call-to-action buttons, primary navigation, or logo elements

2. **secondaryColor**: Main text color
   - Look for a secondary accent color used throughout the design
   - Often complementary to the primary color

3. **backgroundColor**: The main page background color
   - Identify the dominant background color behind the main content
   - Usually the lightest (or darkest in dark mode) large-area color
   - Must have a high contrast ratio with the secondaryColor, since secondaryColor is used for text.
   - Should be the color that covers the most area in the layout

4. **linkColor**: The color used for hyperlinks
   - Look for the color used in navigation links, text links, or interactive elements
   - Often blue, but can be any color that indicates clickable text
   - If unclear, use the color most commonly applied to inline text links

Guidelines:
- Focus on colors that appear in multiple important UI elements
- Prioritize colors from branding elements (logos, headers, navigation)
- Avoid generic colors unless they're clearly intentional brand choices
- Ensure colors have good contrast with the background
- Return all colors in uppercase HEX format (e.g., #FF5733)

Return your analysis as a JSON object with exactly these keys: primaryColor, secondaryColor, backgroundColor, linkColor
"""
        
        return prompt
