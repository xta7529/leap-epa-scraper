# EPA LEAP Document Scraper

A Python-based web scraper for extracting and analyzing documents from the EPA LEAP (Licensing & Enforcement Access Portal) website.

## Features

- **Document Link Extraction**: Identifies and extracts document links from EPA license profiles using multiple methods:
  - Regular anchor (`<a>`) tags
  - Embedded iframes (`<iframe>`)
  - Embedded objects (`<embed>`, `<object>`)
- **PDF Download**: Automatically downloads PDFs from extracted links
- **Content Parsing**: Extracts specific phrases from PDFs including:
  - "Name of receiving waters"
  - "receiving waters"
  - "ELV breach"
  - "Emission Limit Value"
- **CSV Export**: Saves parsed results to CSV files for further analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/xta7529/leap-epa-scraper.git
cd leap-epa-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from scraper import EPALeapScraper

# Initialize the scraper
scraper = EPALeapScraper()

# Scrape a license profile
license_number = "P1010-01"
scraper.scrape_license(
    license_number=license_number,
    download_dir='downloads',
    output_csv='results.csv'
)
```

### Advanced Usage

```python
from scraper import EPALeapScraper

scraper = EPALeapScraper()

# Step 1: Fetch a license page
soup = scraper.get_license_page("P1010-01")

# Step 2: Extract document links
documents = scraper.extract_document_links(soup)

# Step 3: Download a specific document
scraper.download_pdf(documents[0], "output.pdf")

# Step 4: Parse the PDF for specific phrases
phrases = ["receiving waters", "ELV breach"]
results = scraper.parse_pdf_for_phrases("output.pdf", phrases)

# Step 5: Save results to CSV
scraper.save_results_to_csv(results, "output.csv")
```

### Running Examples

Run the example script to test the scraper:

```bash
python example.py
```

This will:
1. Download a known document directly
2. Attempt to scrape license profiles
3. Parse PDFs for target phrases
4. Generate CSV output files

## Project Structure

```
leap-epa-scraper/
├── scraper.py          # Main scraper class and logic
├── example.py          # Example usage and test script
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Output

The scraper generates two types of outputs:

1. **Downloaded PDFs**: Saved to the specified download directory
2. **CSV Files**: Contains extracted information with columns:
   - `document`: PDF filename
   - `url`: Original document URL
   - `phrase`: Search phrase that was found
   - `page`: Page number where the phrase appears
   - `context`: Surrounding text context

## EPA LEAP Website

The scraper works with the EPA LEAP portal at https://leap.epa.ie

License profiles follow this URL format:
```
https://leap.epa.ie/Licences/Licence/Details?LicenceNumber=XXXXX
```

Example document URLs:
```
https://leap.epa.ie/docs/c40fdc96-aab7-4e98-b68d-7e67223b422e.pdf
```

## Requirements

- Python 3.7+
- beautifulsoup4 4.12.3
- requests 2.31.0
- PyPDF2 3.0.1
- lxml 5.1.0

## Notes

- The scraper includes rate limiting (1 second delay between requests) to be respectful to the EPA servers
- Some documents may be protected or require authentication
- PDF parsing quality depends on the document structure and text extraction capabilities

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.