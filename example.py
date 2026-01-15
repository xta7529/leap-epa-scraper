#!/usr/bin/env python3
"""
Example script demonstrating EPA LEAP document scraper usage.
Tests the scraper with known document URLs and license profiles.
"""

import os
import sys
from scraper import EPALeapScraper
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_direct_document_download():
    """Test downloading a known document URL directly."""
    print("\n" + "="*60)
    print("Test 1: Direct Document Download")
    print("="*60)
    
    scraper = EPALeapScraper()
    
    # Known example document URL from problem statement
    doc_url = "https://leap.epa.ie/docs/c40fdc96-aab7-4e98-b68d-7e67223b422e.pdf"
    
    # Create test directory
    test_dir = "test_downloads"
    os.makedirs(test_dir, exist_ok=True)
    
    # Download the document
    output_path = os.path.join(test_dir, "example_document.pdf")
    success = scraper.download_pdf(doc_url, output_path)
    
    if success and os.path.exists(output_path):
        print(f"✓ Successfully downloaded document to: {output_path}")
        
        # Parse the PDF for target phrases
        phrases = [
            "Name of receiving waters",
            "receiving waters",
            "ELV breach",
            "Emission Limit Value"
        ]
        
        results = scraper.parse_pdf_for_phrases(output_path, phrases)
        
        print("\nParsing Results:")
        print("-" * 60)
        for phrase, matches in results.items():
            if matches:
                print(f"\n'{phrase}' found {len(matches)} time(s):")
                for match in matches[:3]:  # Show first 3 matches
                    print(f"  - Page {match['page']}: {match['text'][:100]}...")
            else:
                print(f"\n'{phrase}': Not found")
        
        # Save results to CSV
        csv_file = "test_results.csv"
        scraper.save_results_to_csv(results, csv_file)
        print(f"\n✓ Results saved to: {csv_file}")
        
        return True
    else:
        print("✗ Failed to download document")
        return False


def test_license_scraping():
    """Test scraping a complete license profile."""
    print("\n" + "="*60)
    print("Test 2: License Profile Scraping")
    print("="*60)
    
    scraper = EPALeapScraper()
    
    # Example license numbers to try
    license_numbers = ["P1010-01", "W0001-01"]
    
    for license_number in license_numbers:
        print(f"\nAttempting to scrape license: {license_number}")
        
        # Fetch the page
        soup = scraper.get_license_page(license_number)
        
        if soup:
            print(f"✓ Successfully fetched page for {license_number}")
            
            # Extract document links
            documents = scraper.extract_document_links(soup)
            
            if documents:
                print(f"✓ Found {len(documents)} document(s):")
                for i, doc in enumerate(documents[:5], 1):  # Show first 5
                    print(f"  {i}. {doc}")
                if len(documents) > 5:
                    print(f"  ... and {len(documents) - 5} more")
                
                return True
            else:
                print(f"✗ No documents found for {license_number}")
        else:
            print(f"✗ Failed to fetch page for {license_number}")
    
    return False


def test_full_workflow():
    """Test the complete workflow with a real license."""
    print("\n" + "="*60)
    print("Test 3: Complete Workflow")
    print("="*60)
    
    scraper = EPALeapScraper()
    
    # Use example license number
    license_number = "P1010-01"
    download_dir = "full_test_downloads"
    output_csv = "full_test_results.csv"
    
    print(f"\nRunning complete scraping workflow for license: {license_number}")
    
    try:
        scraper.scrape_license(
            license_number=license_number,
            download_dir=download_dir,
            output_csv=output_csv
        )
        
        # Check if output was created
        if os.path.exists(output_csv):
            print(f"\n✓ Complete workflow finished successfully!")
            print(f"✓ Results saved to: {output_csv}")
            print(f"✓ Documents saved to: {download_dir}/")
            return True
        else:
            print("\n✗ Workflow completed but no results file created")
            return False
            
    except Exception as e:
        print(f"\n✗ Workflow failed with error: {e}")
        logger.exception("Full workflow error")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("EPA LEAP Document Scraper - Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Direct document download
    try:
        results.append(("Direct Document Download", test_direct_document_download()))
    except Exception as e:
        logger.exception("Test 1 failed")
        results.append(("Direct Document Download", False))
    
    # Test 2: License page scraping
    try:
        results.append(("License Profile Scraping", test_license_scraping()))
    except Exception as e:
        logger.exception("Test 2 failed")
        results.append(("License Profile Scraping", False))
    
    # Test 3: Full workflow (commented out by default to avoid lengthy execution)
    # Uncomment to run full workflow test
    # try:
    #     results.append(("Complete Workflow", test_full_workflow()))
    # except Exception as e:
    #     logger.exception("Test 3 failed")
    #     results.append(("Complete Workflow", False))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
