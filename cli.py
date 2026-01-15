#!/usr/bin/env python3
"""
Command-line interface for EPA LEAP document scraper.
Usage: python cli.py <license_number> [options]
"""

import argparse
import sys
import os
from scraper import EPALeapScraper


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='EPA LEAP Document Scraper - Extract and analyze environmental compliance documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape license P1010-01 with default settings
  python cli.py P1010-01
  
  # Scrape with custom output directory and CSV file
  python cli.py P1010-01 --download-dir my_pdfs --output results.csv
  
  # Download a specific document directly
  python cli.py --url https://leap.epa.ie/docs/c40fdc96-aab7-4e98-b68d-7e67223b422e.pdf
        """
    )
    
    parser.add_argument(
        'license_number',
        nargs='?',
        help='EPA license number (e.g., P1010-01, W0001-01)'
    )
    
    parser.add_argument(
        '--url',
        help='Direct URL to a document to download and parse'
    )
    
    parser.add_argument(
        '--download-dir',
        default='downloads',
        help='Directory to save downloaded PDFs (default: downloads)'
    )
    
    parser.add_argument(
        '--output',
        default='results.csv',
        help='Output CSV file path (default: results.csv)'
    )
    
    parser.add_argument(
        '--base-url',
        default='https://leap.epa.ie',
        help='Base URL for EPA LEAP website (default: https://leap.epa.ie)'
    )
    
    parser.add_argument(
        '--phrases',
        nargs='+',
        default=['Name of receiving waters', 'receiving waters', 'ELV breach', 'Emission Limit Value'],
        help='Phrases to search for in PDFs'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.license_number and not args.url:
        parser.error('Either license_number or --url must be provided')
    
    # Initialize scraper
    scraper = EPALeapScraper(base_url=args.base_url)
    
    if not args.verbose:
        import logging
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        if args.url:
            # Direct URL mode
            print(f"Downloading document from: {args.url}")
            
            os.makedirs(args.download_dir, exist_ok=True)
            filename = os.path.basename(args.url)
            if not filename:
                filename = "document.pdf"
            
            pdf_path = os.path.join(args.download_dir, filename)
            
            if scraper.download_pdf(args.url, pdf_path):
                print(f"✓ Downloaded to: {pdf_path}")
                
                print(f"Parsing for phrases: {', '.join(args.phrases)}")
                results = scraper.parse_pdf_for_phrases(pdf_path, args.phrases)
                
                # Create detailed results
                detailed_results = []
                for phrase, matches in results.items():
                    for match in matches:
                        detailed_results.append({
                            'document': filename,
                            'url': args.url,
                            'phrase': phrase,
                            'page': match['page'],
                            'context': match['text']
                        })
                
                if detailed_results:
                    scraper._save_detailed_results_to_csv(detailed_results, args.output)
                    print(f"✓ Results saved to: {args.output}")
                    print(f"Found {len(detailed_results)} matching phrase(s)")
                else:
                    print("No matching phrases found in document")
            else:
                print("✗ Failed to download document", file=sys.stderr)
                return 1
        else:
            # License scraping mode
            print(f"Scraping license: {args.license_number}")
            print(f"Download directory: {args.download_dir}")
            print(f"Output file: {args.output}")
            
            scraper.scrape_license(
                license_number=args.license_number,
                download_dir=args.download_dir,
                output_csv=args.output
            )
            
            if os.path.exists(args.output):
                print(f"\n✓ Scraping complete!")
                print(f"✓ Results saved to: {args.output}")
                
                # Count results
                with open(args.output, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        print(f"✓ Found {len(lines) - 1} result(s)")
            else:
                print("\n⚠ No documents or matches found", file=sys.stderr)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
