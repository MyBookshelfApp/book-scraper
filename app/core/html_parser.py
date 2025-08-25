"""
High-performance HTML parsing for book scraping
"""
import re
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser as SelectolaxParser
import lxml.html


class HTMLParser:
    """High-performance HTML parser with multiple parsing engines"""
    
    def __init__(self, html: str, url: Optional[str] = None):
        self.html = html
        self.url = url
        
        # Initialize multiple parsers for fallback
        self._bs4_soup: Optional[BeautifulSoup] = None
        self._selectolax_parser: Optional[SelectolaxParser] = None
        self._lxml_parser: Optional[lxml.html.HtmlElement] = None
        
        # Parse with all engines
        self._parse_all()
    
    def _parse_all(self):
        """Parse HTML with all available engines"""
        try:
            self._bs4_soup = BeautifulSoup(self.html, 'lxml')
        except Exception as e:
            print(f"Failed to initialize BeautifulSoup parser: {e}")
            self._bs4_soup = None
        
        try:
            self._selectolax_parser = SelectolaxParser(self.html)
        except Exception as e:
            print(f"Failed to initialize Selectolax parser: {e}")
            self._selectolax_parser = None
        
        try:
            self._lxml_parser = lxml.html.fromstring(self.html)
        except Exception as e:
            print(f"Failed to initialize lxml parser: {e}")
            self._lxml_parser = None
    
    def select(self, selector: str, engine: str = "auto") -> List[Any]:
        """Select elements using CSS selector"""
        if engine == "auto":
            # Try selectolax first (fastest), then fallback
            if self._selectolax_parser:
                try:
                    elements = self._selectolax_parser.css(selector)
                    # Ensure we return a list
                    if elements is None:
                        elements = []
                    # Convert to list if it's not already
                    if not isinstance(elements, list):
                        try:
                            elements = list(elements)
                        except Exception:
                            elements = []
                    if elements:
                        return elements
                except Exception as e:
                    print(f"Selectolax auto-selector failed: {e}")
                    pass
            
            if self._bs4_soup:
                try:
                    elements = self._bs4_soup.select(selector)
                    if elements:
                        return elements
                except Exception:
                    pass
            
            if self._lxml_parser:
                try:
                    elements = self._lxml_parser.cssselect(selector)
                    if elements:
                        return elements
                except Exception:
                    pass
        
        elif engine == "selectolax" and self._selectolax_parser:
            try:
                elements = self._selectolax_parser.css(selector)
                # Ensure we return a list
                if elements is None:
                    return []
                # Convert to list if it's not already
                if not isinstance(elements, list):
                    try:
                        elements = list(elements)
                    except Exception:
                        return []
                return elements
            except Exception as e:
                print(f"Selectolax CSS selector failed: {e}")
                return []
        elif engine == "bs4" and self._bs4_soup:
            try:
                return self._bs4_soup.select(selector)
            except Exception:
                return []
        elif engine == "lxml" and self._lxml_parser:
            try:
                return self._lxml_parser.cssselect(selector)
            except Exception:
                return []
        
        return []
    
    def find(self, tag: str, attrs: Optional[Dict[str, str]] = None, **kwargs) -> Optional[Any]:
        """Find first element matching criteria"""
        if self._bs4_soup:
            try:
                return self._bs4_soup.find(tag, attrs, **kwargs)
            except Exception:
                pass
        
        if self._selectolax_parser:
            try:
                # Convert bs4-style find to selectolax
                selector = tag
                if attrs:
                    for key, value in attrs.items():
                        selector += f'[{key}="{value}"]'
                elements = self._selectolax_parser.css(selector)
                return elements[0] if elements else None
            except Exception:
                pass
        
        return None
    
    def find_all(self, tag: str, attrs: Optional[Dict[str, str]] = None, **kwargs) -> List[Any]:
        """Find all elements matching criteria"""
        if self._bs4_soup:
            try:
                return self._bs4_soup.find_all(tag, attrs, **kwargs)
            except Exception:
                pass
        
        if self._selectolax_parser:
            try:
                selector = tag
                if attrs:
                    for key, value in attrs.items():
                        selector += f'[{key}="{value}"]'
                return self._selectolax_parser.css(selector)
            except Exception:
                pass
        
        return []
    
    def get_text(self, element: Any, strip: bool = True) -> str:
        """Extract text from element"""
        text = ""
        
        try:
            # Special handling for Selectolax elements
            if hasattr(element, '__class__') and 'selectolax' in str(element.__class__).lower():
                try:
                    # Try to get text content directly
                    if hasattr(element, 'text'):
                        text = element.text
                        if callable(text):
                            text = text()
                    elif hasattr(element, 'text_content'):
                        text = element.text_content()
                        if callable(text):
                            text = text()
                    else:
                        # Fallback to string representation
                        text = str(element)
                except Exception as e:
                    print(f"Selectolax text extraction failed: {e}")
                    text = str(element)
            else:
                # Standard handling for other parser types
                if hasattr(element, 'text'):
                    text = element.text
                    # Handle case where text is a callable (like in Selectolax)
                    if callable(text):
                        text = text()
                elif hasattr(element, 'get_text'):
                    text = element.get_text()
                    # Handle case where get_text is a callable
                    if callable(text):
                        text = text()
                elif hasattr(element, 'text_content'):
                    text = element.text_content()
                    # Handle case where text_content is a callable
                    if callable(text):
                        text = text()
                else:
                    text = str(element)
        except Exception as e:
            # Fallback to string representation
            print(f"Text extraction failed: {e}")
            text = str(element)
        
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
        
        if strip:
            text = text.strip()
        
        return text
    
    def get_attribute(self, element: Any, attr: str) -> Optional[str]:
        """Get attribute value from element"""
        try:
            # Special handling for Selectolax elements
            if hasattr(element, '__class__') and 'selectolax' in str(element.__class__).lower():
                try:
                    if hasattr(element, 'attributes'):
                        attrs = element.attributes
                        if callable(attrs):
                            attrs = attrs()
                        value = attrs.get(attr)
                    else:
                        value = None
                except Exception as e:
                    print(f"Selectolax attribute extraction failed: {e}")
                    value = None
            else:
                # Standard handling for other parser types
                if hasattr(element, 'get'):
                    value = element.get(attr)
                    # Handle case where get is a callable
                    if callable(value):
                        value = value()
                elif hasattr(element, 'attributes'):
                    attrs = element.attributes
                    # Handle case where attributes is a callable
                    if callable(attrs):
                        attrs = attrs()
                    value = attrs.get(attr)
                elif hasattr(element, 'get_attribute'):
                    value = element.get_attribute(attr)
                    # Handle case where get_attribute is a callable
                    if callable(value):
                        value = value()
                else:
                    value = None
            
            # Ensure value is a string or None
            if value is not None and not isinstance(value, str):
                value = str(value)
            
            return value
        except Exception as e:
            print(f"Attribute extraction failed: {e}")
            return None
    
    def normalize_url(self, url: str) -> str:
        """Normalize relative URLs to absolute URLs"""
        if not self.url:
            return url
        
        return urljoin(self.url, url)
    
    def extract_links(self, base_selector: str = "a") -> List[Dict[str, str]]:
        """Extract all links from the page"""
        links = []
        
        for element in self.select(base_selector):
            href = self.get_attribute(element, "href")
            if href:
                text = self.get_text(element)
                links.append({
                    "url": self.normalize_url(href),
                    "text": text,
                    "title": self.get_attribute(element, "title") or ""
                })
        
        return links
    
    def extract_images(self, base_selector: str = "img") -> List[Dict[str, str]]:
        """Extract all images from the page"""
        images = []
        
        for element in self.select(base_selector):
            src = self.get_attribute(element, "src")
            if src:
                images.append({
                    "url": self.normalize_url(src),
                    "alt": self.get_attribute(element, "alt") or "",
                    "title": self.get_attribute(element, "title") or ""
                })
        
        return images
    
    def extract_metadata(self) -> Dict[str, str]:
        """Extract metadata from HTML head"""
        metadata = {}
        
        # Meta tags
        for meta in self.select("meta"):
            name = self.get_attribute(meta, "name") or self.get_attribute(meta, "property")
            content = self.get_attribute(meta, "content")
            
            if name and content:
                metadata[name.lower()] = content
        
        # Title
        title_elem = self.find("title")
        if title_elem:
            metadata["title"] = self.get_text(title_elem)
        
        # Canonical URL
        canonical = self.find("link", attrs={"rel": "canonical"})
        if canonical:
            href = self.get_attribute(canonical, "href")
            if href:
                metadata["canonical_url"] = self.normalize_url(href)
        
        return metadata
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def extract_structured_data(self) -> List[Dict[str, Any]]:
        """Extract structured data (JSON-LD, Microdata, RDFa)"""
        structured_data = []
        
        # JSON-LD
        for script in self.select('script[type="application/ld+json"]'):
            try:
                import json
                content = self.get_text(script, strip=False)
                data = json.loads(content)
                if isinstance(data, list):
                    structured_data.extend(data)
                else:
                    structured_data.append(data)
            except Exception:
                continue
        
        # Microdata
        for item in self.select('[itemtype]'):
            item_data = {}
            item_data['@type'] = self.get_attribute(item, 'itemtype')
            item_data['@context'] = 'http://schema.org'
            
            for prop in item.select('[itemprop]'):
                prop_name = self.get_attribute(prop, 'itemprop')
                prop_value = self.get_text(prop) or self.get_attribute(prop, 'content')
                
                if prop_name and prop_value:
                    item_data[prop_name] = prop_value
            
            if len(item_data) > 2:  # More than just @type and @context
                structured_data.append(item_data)
        
        return structured_data
    
    def get_parser_stats(self) -> Dict[str, Any]:
        """Get statistics about available parsers"""
        return {
            "bs4_available": self._bs4_soup is not None,
            "selectolax_available": self._selectolax_parser is not None,
            "lxml_available": self._lxml_parser is not None,
            "html_length": len(self.html),
            "url": self.url
        } 