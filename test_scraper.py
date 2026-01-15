#!/usr/bin/env python3
"""
Unit tests for EPA LEAP scraper - tests functionality without network access.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
from bs4 import BeautifulSoup
from scraper import EPALeapScraper
import os
import tempfile


class TestEPALeapScraper(unittest.TestCase):
    """Unit tests for EPALeapScraper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = EPALeapScraper()
    
    def test_scraper_initialization(self):
        """Test that scraper initializes correctly."""
        self.assertEqual(self.scraper.base_url, "https://leap.epa.ie")
        self.assertIsNotNone(self.scraper.session)
        self.assertIn('User-Agent', self.scraper.session.headers)
    
    def test_extract_document_links_from_anchor_tags(self):
        """Test extraction of document links from anchor tags."""
        html = """
        <html>
            <body>
                <a href="/docs/test-document.pdf">Document 1</a>
                <a href="https://leap.epa.ie/docs/another-doc.pdf">Document 2</a>
                <a href="/other/page.html">Not a document</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        documents = self.scraper.extract_document_links(soup)
        
        self.assertEqual(len(documents), 2)
        self.assertTrue(any('test-document.pdf' in doc for doc in documents))
        self.assertTrue(any('another-doc.pdf' in doc for doc in documents))
    
    def test_extract_document_links_from_iframes(self):
        """Test extraction of document links from iframe elements."""
        html = """
        <html>
            <body>
                <iframe src="/docs/embedded-document.pdf"></iframe>
                <iframe src="/other/page.html"></iframe>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        documents = self.scraper.extract_document_links(soup)
        
        self.assertEqual(len(documents), 1)
        self.assertTrue(any('embedded-document.pdf' in doc for doc in documents))
    
    def test_extract_document_links_from_embeds(self):
        """Test extraction of document links from embed elements."""
        html = """
        <html>
            <body>
                <embed src="/docs/embed-document.pdf" type="application/pdf">
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        documents = self.scraper.extract_document_links(soup)
        
        self.assertEqual(len(documents), 1)
        self.assertTrue(any('embed-document.pdf' in doc for doc in documents))
    
    def test_extract_document_links_from_objects(self):
        """Test extraction of document links from object elements."""
        html = """
        <html>
            <body>
                <object data="/docs/object-document.pdf" type="application/pdf"></object>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        documents = self.scraper.extract_document_links(soup)
        
        self.assertEqual(len(documents), 1)
        self.assertTrue(any('object-document.pdf' in doc for doc in documents))
    
    def test_extract_document_links_removes_duplicates(self):
        """Test that duplicate document links are removed."""
        html = """
        <html>
            <body>
                <a href="/docs/test-document.pdf">Document 1</a>
                <a href="/docs/test-document.pdf">Document 1 Again</a>
                <iframe src="/docs/test-document.pdf"></iframe>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        documents = self.scraper.extract_document_links(soup)
        
        self.assertEqual(len(documents), 1)
    
    def test_extract_document_links_with_mixed_elements(self):
        """Test extraction from multiple element types."""
        html = """
        <html>
            <body>
                <a href="/docs/doc1.pdf">Document 1</a>
                <iframe src="/docs/doc2.pdf"></iframe>
                <embed src="/docs/doc3.pdf">
                <object data="/docs/doc4.pdf"></object>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        documents = self.scraper.extract_document_links(soup)
        
        self.assertEqual(len(documents), 4)
    
    def test_extract_document_links_with_no_documents(self):
        """Test extraction when no documents are present."""
        html = """
        <html>
            <body>
                <a href="/other/page.html">Not a document</a>
                <p>Some text</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        documents = self.scraper.extract_document_links(soup)
        
        self.assertEqual(len(documents), 0)
    
    def test_extract_document_links_with_none_soup(self):
        """Test extraction with None soup object."""
        documents = self.scraper.extract_document_links(None)
        self.assertEqual(len(documents), 0)
    
    def test_save_results_to_csv(self):
        """Test saving results to CSV."""
        results = {
            'receiving waters': [
                {'page': 1, 'text': 'Name of receiving waters: River Liffey'},
                {'page': 2, 'text': 'Discharge to receiving waters approved'}
            ],
            'ELV breach': []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_file = f.name
        
        try:
            self.scraper.save_results_to_csv(results, output_file)
            
            # Verify file was created and has content
            self.assertTrue(os.path.exists(output_file))
            
            with open(output_file, 'r') as f:
                content = f.read()
                self.assertIn('Phrase', content)
                self.assertIn('Page', content)
                self.assertIn('Context', content)
                self.assertIn('receiving waters', content)
                self.assertIn('River Liffey', content)
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    @patch('scraper.PdfReader')
    def test_parse_pdf_for_phrases(self, mock_pdf_reader):
        """Test parsing PDF for specific phrases."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        Sample Document
        Name of receiving waters: River Liffey
        ELV breach detected on 2024-01-15
        Emission Limit Value exceeded
        """
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        phrases = ["Name of receiving waters", "ELV breach"]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            pdf_path = f.name
        
        try:
            results = self.scraper.parse_pdf_for_phrases(pdf_path, phrases)
            
            # Check that both phrases were found
            self.assertIn("Name of receiving waters", results)
            self.assertIn("ELV breach", results)
            
            # Check that results contain matches
            self.assertTrue(len(results["Name of receiving waters"]) > 0)
            self.assertTrue(len(results["ELV breach"]) > 0)
            
            # Check match structure
            match = results["Name of receiving waters"][0]
            self.assertIn('page', match)
            self.assertIn('text', match)
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)


class TestDocumentLinkExtraction(unittest.TestCase):
    """Additional tests for document link extraction edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = EPALeapScraper()
    
    def test_relative_urls_converted_to_absolute(self):
        """Test that relative URLs are converted to absolute URLs."""
        html = """
        <html>
            <body>
                <a href="/docs/relative-doc.pdf">Document</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        documents = self.scraper.extract_document_links(soup)
        
        self.assertEqual(len(documents), 1)
        self.assertTrue(documents[0].startswith('https://leap.epa.ie'))
    
    def test_guid_based_document_urls(self):
        """Test extraction of GUID-based document URLs like the example."""
        html = """
        <html>
            <body>
                <a href="/docs/c40fdc96-aab7-4e98-b68d-7e67223b422e.pdf">Document</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        documents = self.scraper.extract_document_links(soup)
        
        self.assertEqual(len(documents), 1)
        self.assertIn('c40fdc96-aab7-4e98-b68d-7e67223b422e.pdf', documents[0])


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEPALeapScraper))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentLinkExtraction))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
