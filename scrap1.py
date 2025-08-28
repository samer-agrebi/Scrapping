import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from urllib.parse import urljoin
import time

# Configure the page
st.set_page_config(
    page_title="Web Scraper Tool",
    page_icon="🕷️",
    layout="wide"
)

class StreamlitWebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_page(self, url, custom_selectors=None):
        """Scrape a single web page"""
        try:
            with st.spinner(f"Scraping {url}..."):
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                data = {
                    'url': url,
                    'title': soup.title.string.strip() if soup.title else 'No title',
                    'status_code': response.status_code
                }
                
                if custom_selectors:
                    for key, selector in custom_selectors.items():
                        elements = soup.select(selector)
                        if elements:
                            if len(elements) == 1:
                                data[key] = elements[0].get_text(strip=True)
                            else:
                                data[key] = [elem.get_text(strip=True) for elem in elements]
                        else:
                            data[key] = None
                else:
                    # Default extraction
                    data.update({
                        'headings': [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])],
                        'paragraphs': [p.get_text(strip=True) for p in soup.find_all('p')],
                        'links': [{'text': a.get_text(strip=True), 'href': urljoin(url, a.get('href', ''))} 
                                 for a in soup.find_all('a', href=True)],
                        'images': [{'alt': img.get('alt', ''), 'src': urljoin(url, img.get('src', ''))} 
                                  for img in soup.find_all('img', src=True)]
                    })
                
                return data, None
                
        except requests.RequestException as e:
            return None, f"Request error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"

def main():
    # Header
    st.title("🕷️ Web Scraper Tool")
    st.markdown("Enter a URL below to scrape and analyze web content")
    
    # Initialize scraper
    if 'scraper' not in st.session_state:
        st.session_state.scraper = StreamlitWebScraper()
    
    # Sidebar for options
    with st.sidebar:
        st.header("⚙️ Options")
        
        # Custom selectors
        use_custom_selectors = st.checkbox("Use Custom CSS Selectors")
        custom_selectors = {}
        
        if use_custom_selectors:
            st.subheader("CSS Selectors")
            st.markdown("Define what content to extract:")
            
            selector_name = st.text_input("Selector Name", placeholder="e.g., main_title")
            selector_css = st.text_input("CSS Selector", placeholder="e.g., h1")
            
            if st.button("Add Selector"):
                if selector_name and selector_css:
                    if 'custom_selectors' not in st.session_state:
                        st.session_state.custom_selectors = {}
                    st.session_state.custom_selectors[selector_name] = selector_css
                    st.success(f"Added selector: {selector_name}")
            
            # Display current selectors
            if 'custom_selectors' in st.session_state and st.session_state.custom_selectors:
                st.subheader("Current Selectors:")
                for name, css in st.session_state.custom_selectors.items():
                    col1, col2 = st.columns([3, 1])
                    col1.code(f"{name}: {css}")
                    if col2.button("❌", key=f"del_{name}"):
                        del st.session_state.custom_selectors[name]
                        st.rerun()
                
                custom_selectors = st.session_state.custom_selectors
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        url = st.text_input(
            "🌐 Enter URL to scrape:",
            placeholder="https://example.com",
            help="Enter a valid URL starting with http:// or https://"
        )
    # Example URLs
    st.markdown("**Try these example URLs:**")
    example_urls = [
        "https://www.binarhandling.com/en/products/end-effectors/",
        "https://www.binarhandling.com/en/products/manipulator-arms/",
        "https://www.binarhandling.com/en/products/rail-systems/"
    ]
    with col2:
        st.write("")  # Add spacing
        scrape_button = st.button("🚀 Scrape Website", type="primary")
    
    
    
    cols = st.columns(len(example_urls))
    for i, example_url in enumerate(example_urls):
        if cols[i].button(f"📄 {example_url.split('//')[1]}", key=f"example_{i}"):
            st.session_state.example_url = example_url
            st.rerun()
    
    # Use example URL if selected
    if 'example_url' in st.session_state:
        url = st.session_state.example_url
        del st.session_state.example_url
    
    # Scraping logic
    if scrape_button and url:
        if not url.startswith(('http://', 'https://')):
            st.error("❌ Please enter a valid URL starting with http:// or https://")
        else:
            # Perform scraping
            data, error = st.session_state.scraper.scrape_page(
                url, 
                custom_selectors if custom_selectors else None
            )
            
            if error:
                st.error(f"❌ Error scraping website: {error}")
            else:
                st.success("✅ Website scraped successfully!")
                
                # Display results
                st.header("📊 Scraping Results")
                
                # Basic info
                col1, col2, col3 = st.columns(3)
                col1.metric("Status Code", data['status_code'])
                col2.metric("Page Title", len(data['title']) if data['title'] else 0, data['title'][:50] + "..." if len(data['title']) > 50 else data['title'])
                col3.metric("URL", "✅ Valid")
                
                # Tabs for different content types
                if custom_selectors:
                    # Custom selector results
                    st.subheader("🎯 Custom Selector Results")
                    for key, value in data.items():
                        if key not in ['url', 'title', 'status_code']:
                            st.write(f"**{key}:**")
                            if isinstance(value, list):
                                if value:
                                    for i, item in enumerate(value[:10]):  # Show max 10 items
                                        st.write(f"{i+1}. {item}")
                                    if len(value) > 10:
                                        st.info(f"... and {len(value) - 10} more items")
                                else:
                                    st.write("No content found")
                            else:
                                st.write(value if value else "No content found")
                            st.write("---")
                else:
                    # Default results with tabs
                    tab1, tab2, tab3, tab4 = st.tabs(["📝 Headings", "📄 Paragraphs", "🔗 Links", "🖼️ Images"])
                    
                    with tab1:
                        st.subheader("Page Headings")
                        if data.get('headings'):
                            for i, heading in enumerate(data['headings'][:20]):
                                st.write(f"{i+1}. {heading}")
                            if len(data['headings']) > 20:
                                st.info(f"... and {len(data['headings']) - 20} more headings")
                        else:
                            st.info("No headings found")
                    
                    with tab2:
                        st.subheader("Paragraphs")
                        if data.get('paragraphs'):
                            for i, paragraph in enumerate(data['paragraphs'][:10]):
                                if paragraph.strip():
                                    with st.expander(f"Paragraph {i+1} ({len(paragraph)} chars)"):
                                        st.write(paragraph)
                            if len(data['paragraphs']) > 10:
                                st.info(f"... and {len(data['paragraphs']) - 10} more paragraphs")
                        else:
                            st.info("No paragraphs found")
                    
                    with tab3:
                        st.subheader("Links")
                        if data.get('links'):
                            df_links = pd.DataFrame(data['links'][:50])  # Show max 50 links
                            st.dataframe(df_links, use_container_width=True)
                            if len(data['links']) > 50:
                                st.info(f"... and {len(data['links']) - 50} more links")
                        else:
                            st.info("No links found")
                    
                    with tab4:
                        st.subheader("Images")
                        if data.get('images'):
                            for i, img in enumerate(data['images'][:20]):
                                col1, col2 = st.columns([1, 3])
                                col1.write(f"**Image {i+1}:**")
                                col2.write(f"**Alt:** {img['alt']}")
                                col2.write(f"**Source:** {img['src']}")
                                col2.write("---")
                            if len(data['images']) > 20:
                                st.info(f"... and {len(data['images']) - 20} more images")
                        else:
                            st.info("No images found")
                
                # Download options
                st.header("💾 Download Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    json_data = json.dumps(data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📄 Download as JSON",
                        data=json_data,
                        file_name=f"scraped_data_{int(time.time())}.json",
                        mime="application/json"
                    )
                
                with col2:
                    # Convert to CSV format
                    if custom_selectors:
                        csv_data = pd.DataFrame([data]).to_csv(index=False)
                    else:
                        # Flatten complex data for CSV
                        flat_data = {
                            'url': data['url'],
                            'title': data['title'],
                            'status_code': data['status_code'],
                            'headings_count': len(data.get('headings', [])),
                            'paragraphs_count': len(data.get('paragraphs', [])),
                            'links_count': len(data.get('links', [])),
                            'images_count': len(data.get('images', []))
                        }
                        csv_data = pd.DataFrame([flat_data]).to_csv(index=False)
                    
                    st.download_button(
                        label="📊 Download as CSV",
                        data=csv_data,
                        file_name=f"scraped_data_{int(time.time())}.csv",
                        mime="text/csv"
                    )

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>🕷️ Web Scraper Tool | Built with Streamlit</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()