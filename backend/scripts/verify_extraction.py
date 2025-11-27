import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.scraper import scraper_instance
from bs4 import BeautifulSoup
import os

def test_extraction():
    # Load the test HTML
    with open("test_html.html", "r") as f:
        html_content = f.read()

    # Mock the get_page_content method to return our local HTML
    scraper_instance.get_page_content = lambda url: html_content
    
    # Run the extraction
    print("Testing extraction on Invoice ID 158696...")
    result = scraper_instance.scrape_invoice(158696)
    
    if result:
        print("\nExtraction Successful!")
        print("-" * 30)
        for key, value in result.items():
            print(f"{key}: {value}")
        print("-" * 30)
        
        # Assertions to be sure
        assert result["Invoice #"] == "158696"
        assert result["Date"] == "24-02-2025"
        assert result["Company"] == "JMV Graphix"
        assert result["Name"] == "John"
        assert result["Email"] == "jmvgraphix@mediacombb.net"
        assert "154 N Long St" in result["Address"]
        print("\nAll checks passed!")
    else:
        print("\nExtraction Failed: Returned None")

if __name__ == "__main__":
    test_extraction()
