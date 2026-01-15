#!/usr/bin/env python3
"""
EPA LEAP Document Scraper
Scrapes document links from EPA license profiles and parses specific information from PDFs.
"""

import os
import re
import csv
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from urllib.parse import urljoin, urlparse
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EPALeapScraper:
    """Scraper for EPA LEAP license profiles."""
    
    def __init__(self, base_url="https://leap.epa.ie"):
        """
        Initialize the scraper.
        
        Args:
            base_url: Base URL for the EPA LEAP website
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_license_page(self, license_number):
        """
        Fetch the license profile page.
        
        Args:
            license_number: EPA license number (e.g., P1010-01)
            
        Returns:
            BeautifulSoup object of the page or None if error
        """
        url = f"{self.base_url}/Licences/Licence/Details?LicenceNumber={license_number}"
        logger.info(f"Fetching license page: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            logger.error(f"Error fetching license page: {e}")
            return None
    
    def extract_document_links(self, soup):
        """
        Extract document links from the license profile page.
        Supports multiple HTML structures including regular links, iframes, and embeds.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of document URLs
        """
        documents = []
        
        if not soup:
            return documents
        
        # Method 1: Find all anchor tags with href containing /docs/
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/docs/' in href or href.endswith('.pdf'):
                full_url = urljoin(self.base_url, href)
                documents.append(full_url)
                logger.info(f"Found document link: {full_url}")
        
        # Method 2: Find iframes with document sources
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            if '/docs/' in src or src.endswith('.pdf'):
                full_url = urljoin(self.base_url, src)
                documents.append(full_url)
                logger.info(f"Found document in iframe: {full_url}")
        
        # Method 3: Find embed tags with document sources
        for embed in soup.find_all('embed', src=True):
            src = embed['src']
            if '/docs/' in src or src.endswith('.pdf'):
                full_url = urljoin(self.base_url, src)
                documents.append(full_url)
                logger.info(f"Found document in embed: {full_url}")
        
        # Method 4: Find object tags with data attribute
        for obj in soup.find_all('object', data=True):
            data = obj['data']
            if '/docs/' in data or data.endswith('.pdf'):
                full_url = urljoin(self.base_url, data)
                documents.append(full_url)
                logger.info(f"Found document in object: {full_url}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_documents = []
        for doc in documents:
            if doc not in seen:
                seen.add(doc)
                unique_documents.append(doc)
        
        logger.info(f"Total unique documents found: {len(unique_documents)}")
        return unique_documents
    
    def download_pdf(self, url, output_path):
        """
        Download a PDF file from the given URL.
        
        Args:
            url: URL of the PDF
            output_path: Path to save the PDF
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Downloading PDF: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"PDF saved to: {output_path}")
            return True
        except requests.RequestException as e:
            logger.error(f"Error downloading PDF: {e}")
            return False
    
    def parse_pdf_for_phrases(self, pdf_path, phrases):
        """
        Parse a PDF file and extract text containing specific phrases.
        
        Args:
            pdf_path: Path to the PDF file
            phrases: List of phrases to search for (case-insensitive)
            
        Returns:
            Dictionary mapping phrases to lists of matching text snippets
        """
        logger.info(f"Parsing PDF: {pdf_path}")
        results = {phrase: [] for phrase in phrases}
        
        try:
            reader = PdfReader(pdf_path)
            
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Split into lines for better context
                lines = text.split('\n')
                
                for phrase in phrases:
                    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                    
                    for i, line in enumerate(lines):
                        if pattern.search(line):
                            # Get context: current line and next 2 lines
                            context_lines = lines[i:min(i+3, len(lines))]
                            context = ' '.join(context_lines).strip()
                            
                            # Clean up whitespace
                            context = re.sub(r'\s+', ' ', context)
                            
                            results[phrase].append({
                                'page': page_num,
                                'text': context
                            })
                            logger.info(f"Found '{phrase}' on page {page_num}")
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
        
        return results
    
    def save_results_to_csv(self, results, output_file):
        """
        Save parsing results to a CSV file.
        
        Args:
            results: Dictionary of results from parse_pdf_for_phrases
            output_file: Path to the output CSV file
        """
        logger.info(f"Saving results to CSV: {output_file}")
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Phrase', 'Page', 'Context'])
                
                for phrase, matches in results.items():
                    if matches:
                        for match in matches:
                            writer.writerow([phrase, match['page'], match['text']])
                    else:
                        writer.writerow([phrase, 'N/A', 'Not found'])
            
            logger.info(f"Results saved successfully")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
    
    def scrape_license(self, license_number, download_dir='downloads', output_csv='results.csv'):
        """
        Complete workflow: scrape a license, download PDFs, and parse for phrases.
        
        Args:
            license_number: EPA license number
            download_dir: Directory to save downloaded PDFs
            output_csv: Path to output CSV file
        """
        # Create download directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)
        
        # Fetch the license page
        soup = self.get_license_page(license_number)
        
        if not soup:
            logger.error("Failed to fetch license page")
            return
        
        # Extract document links
        documents = self.extract_document_links(soup)
        
        if not documents:
            logger.warning("No documents found on the page")
            return
        
        # Phrases to search for in PDFs
        phrases = [
            "Name of receiving waters",
            "receiving waters",
            "ELV breach",
            "Emission Limit Value"
        ]
        
        all_results = []
        
        # Download and parse each PDF
        for i, doc_url in enumerate(documents, 1):
            # Extract filename from URL
            parsed_url = urlparse(doc_url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename:
                filename = f"document_{i}.pdf"
            
            pdf_path = os.path.join(download_dir, filename)
            
            # Download the PDF
            if self.download_pdf(doc_url, pdf_path):
                # Parse the PDF for phrases
                results = self.parse_pdf_for_phrases(pdf_path, phrases)
                
                # Add document info to results
                for phrase, matches in results.items():
                    for match in matches:
                        all_results.append({
                            'document': filename,
                            'url': doc_url,
                            'phrase': phrase,
                            'page': match['page'],
                            'context': match['text']
                        })
            
            # Be respectful with rate limiting
            time.sleep(1)
        
        # Save all results to CSV
        if all_results:
            self._save_detailed_results_to_csv(all_results, output_csv)
        else:
            logger.warning("No matching phrases found in any documents")
    
    def _save_detailed_results_to_csv(self, results, output_file):
        """
        Save detailed results including document info to CSV.
        
        Args:
            results: List of result dictionaries
            output_file: Path to output CSV file
        """
        logger.info(f"Saving detailed results to CSV: {output_file}")
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=['document', 'url', 'phrase', 'page', 'context'])
                    writer.writeheader()
                    writer.writerows(results)
                else:
                    writer = csv.writer(f)
                    writer.writerow(['document', 'url', 'phrase', 'page', 'context'])
                    writer.writerow(['N/A', 'N/A', 'No results', 'N/A', 'N/A'])
            
            logger.info(f"Results saved successfully with {len(results)} entries")
        except Exception as e:
            logger.error(f"Error saving detailed CSV: {e}")


def main():
    """Main entry point for the scraper."""
    # Example usage
    scraper = EPALeapScraper()
    
    # Example license number - replace with actual license number
    license_number = "P1010-01"
    
    print(f"Starting EPA LEAP scraper for license: {license_number}")
    scraper.scrape_license(license_number)
    print("Scraping complete!")


if __name__ == "__main__":
    main()
