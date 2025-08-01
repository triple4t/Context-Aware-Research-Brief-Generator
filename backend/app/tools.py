"""
Tools for search and web scraping functionality.
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urljoin, urlparse
import time

from langchain_tavily import TavilySearch
from app.config import settings

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraping utility for fetching content from URLs."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = settings.REQUEST_TIMEOUT
    
    def extract_text_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract text content from HTML.
        
        Args:
            html_content: Raw HTML content
            url: Source URL for context
            
        Returns:
            Dictionary with extracted content and metadata
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract main content
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            
            if main_content:
                text = main_content.get_text()
            else:
                # Fallback to body
                text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit content length
            if len(text) > settings.MAX_CONTENT_LENGTH:
                text = text[:settings.MAX_CONTENT_LENGTH] + "..."
            
            return {
                "title": title,
                "content": text,
                "url": url,
                "word_count": len(text.split()),
                "extracted_at": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                "title": "",
                "content": f"Error extracting content: {str(e)}",
                "url": url,
                "word_count": 0,
                "extracted_at": time.time()
            }
    
    def fetch_url_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary with content and metadata
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return {
                    "title": "",
                    "content": f"Non-HTML content: {content_type}",
                    "url": url,
                    "word_count": 0,
                    "extracted_at": time.time()
                }
            
            return self.extract_text_content(response.text, url)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return {
                "title": "",
                "content": f"Error fetching content: {str(e)}",
                "url": url,
                "word_count": 0,
                "extracted_at": time.time()
            }
    
    async def fetch_url_content_async(self, url: str) -> Dict[str, Any]:
        """
        Async version of fetch_url_content.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary with content and metadata
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status != 200:
                        return {
                            "title": "",
                            "content": f"HTTP {response.status}: {response.reason}",
                            "url": url,
                            "word_count": 0,
                            "extracted_at": time.time()
                        }
                    
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        return {
                            "title": "",
                            "content": f"Non-HTML content: {content_type}",
                            "url": url,
                            "word_count": 0,
                            "extracted_at": time.time()
                        }
                    
                    html_content = await response.text()
                    return self.extract_text_content(html_content, url)
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return {
                "title": "",
                "content": f"Error fetching content: {str(e)}",
                "url": url,
                "word_count": 0,
                "extracted_at": time.time()
            }


class SearchTool:
    """Search tool using Tavily for web search."""
    
    def __init__(self):
        self.search_tool = TavilySearch(
            api_key=settings.TAVILY_API_KEY,
            max_results=settings.MAX_SOURCES_PER_QUERY
        )
        self.scraper = WebScraper()
        logger.info(f"SearchTool initialized with max_results={settings.MAX_SOURCES_PER_QUERY}")
    
    def search_and_fetch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Search for content using Tavily and return search results directly.
        
        Args:
            queries: List of search queries
            
        Returns:
            List of search result dictionaries
        """
        all_results = []
        
        for query in queries:
            try:
                # Search for results
                search_response = self.search_tool.invoke({"query": query})
                
                # Handle different response formats
                search_results = []
                if isinstance(search_response, dict):
                    if 'results' in search_response:
                        search_results = search_response['results']
                    elif 'content' in search_response:
                        # Single result format
                        search_results = [search_response]
                    else:
                        logger.warning(f"Unexpected dict response format for query '{query}': {list(search_response.keys())}")
                        continue
                elif isinstance(search_response, list):
                    search_results = search_response
                elif isinstance(search_response, str):
                    logger.warning(f"Tavily returned string response for query '{query}': {search_response[:100]}...")
                    # Try to extract URLs from the string response
                    import re
                    urls = re.findall(r'https?://[^\s<>"]+', search_response)
                    if urls:
                        search_results = [{"url": url, "title": f"Result from {url}", "content": search_response[:500]} for url in urls[:5]]
                    else:
                        continue
                else:
                    logger.warning(f"Unexpected search response format for query '{query}': {type(search_response)}")
                    continue
                
                # Convert search results to content format (no web scraping)
                for result in search_results:
                    if isinstance(result, dict):
                        url = result.get('url', '')
                        if url and self._is_valid_url(url):
                            content = {
                                "title": result.get('title', 'Unknown Title'),
                                "content": result.get('content', 'Content not available'),
                                "url": url,
                                "word_count": len(result.get('content', '').split()),
                                "extracted_at": time.time()
                            }
                            if content["word_count"] > 20:  # Lower threshold since we're not scraping
                                all_results.append(content)
                    elif isinstance(result, str):
                        # Handle string results
                        content = {
                            "title": f"Search result for {query}",
                            "content": result,
                            "url": f"https://search-result-{len(all_results)}.example.com",
                            "word_count": len(result.split()),
                            "extracted_at": time.time()
                        }
                        if content["word_count"] > 20:
                            all_results.append(content)
                
                # Add delay to be respectful
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                continue
        
        return all_results
    
    async def search_and_fetch_async(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Async version of search_and_fetch.
        
        Args:
            queries: List of search queries
            
        Returns:
            List of search result dictionaries
        """
        all_results = []
        
        for query in queries:
            try:
                # Search for results
                search_response = self.search_tool.invoke({"query": query})
                
                # Handle different response formats
                search_results = []
                if isinstance(search_response, dict):
                    if 'results' in search_response:
                        search_results = search_response['results']
                    elif 'content' in search_response:
                        # Single result format
                        search_results = [search_response]
                    else:
                        logger.warning(f"Unexpected dict response format for query '{query}': {list(search_response.keys())}")
                        continue
                elif isinstance(search_response, list):
                    search_results = search_response
                elif isinstance(search_response, str):
                    logger.warning(f"Tavily returned string response for query '{query}': {search_response[:100]}...")
                    # Try to extract URLs from the string response
                    import re
                    urls = re.findall(r'https?://[^\s<>"]+', search_response)
                    if urls:
                        search_results = [{"url": url, "title": f"Result from {url}", "content": search_response[:500]} for url in urls[:5]]
                    else:
                        continue
                else:
                    logger.warning(f"Unexpected search response format for query '{query}': {type(search_response)}")
                    continue
                
                # Convert search results to content format (no web scraping)
                for result in search_results:
                    if isinstance(result, dict):
                        url = result.get('url', '')
                        if url and self._is_valid_url(url):
                            content = {
                                "title": result.get('title', 'Unknown Title'),
                                "content": result.get('content', 'Content not available'),
                                "url": url,
                                "word_count": len(result.get('content', '').split()),
                                "extracted_at": time.time()
                            }
                            if content["word_count"] > 20:  # Lower threshold since we're not scraping
                                all_results.append(content)
                    elif isinstance(result, str):
                        # Handle string results
                        content = {
                            "title": f"Search result for {query}",
                            "content": result,
                            "url": f"https://search-result-{len(all_results)}.example.com",
                            "word_count": len(result.split()),
                            "extracted_at": time.time()
                        }
                        if content["word_count"] > 20:
                            all_results.append(content)
                
                # Add delay to be respectful
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                continue
        
        return all_results
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and safe to fetch.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and safe
        """
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc and
                not any(blocked in url.lower() for blocked in [
                    'javascript:', 'data:', 'file:', 'ftp:'
                ])
            )
        except Exception:
            return False


# Global instances
search_tool = SearchTool()
web_scraper = WebScraper() 