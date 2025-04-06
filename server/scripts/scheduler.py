import requests
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from elasticsearch import Elasticsearch
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.article import Article
from config.basic_config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Elasticsearch client
es_client = Elasticsearch([settings.ELASTICSEARCH_URL])


def fetch_news_metadata_from_api():
    """
    Fetch news metadata from the API
    Returns a list of dictionaries with basic news information
    """
    try:
        response = requests.get(
            settings.NEWS_API_URL, headers=settings.NEWS_API_HEADERS
        )
        response.raise_for_status()
        news_data = response.json()
        if "results" in news_data :
            news_data = news_data["results"]
        else :
            news_data = []
        logger.info(f"Fetched {len(news_data)} news items from API")
        return news_data
    except Exception as e:
        logger.error(f"Error fetching news from API: {str(e)}")
        return []


def initialize_selenium_driver():
    """
    Initialize and configure Selenium WebDriver
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Error initializing Selenium driver: {str(e)}")
        return None


def extract_content_with_selenium(url, driver):
    """
    Navigate to the news URL and extract the full content using Selenium
    """
    try:
        driver.get(url)
        # Wait for the content to load - adjust the selector based on the website structure
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "article"))
        )

        # Give a little extra time for JavaScript to load
        time.sleep(2)

        # Get the page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # Extract the article content - adjust these selectors based on the website structure
        article_element = soup.find("article") or soup.find(
            "div", class_="article-content"
        )

        if article_element:
            # Remove unwanted elements like ads, recommended articles, etc.
            for unwanted in article_element.find_all(
                ["aside", "div", "section"],
                class_=["ad", "advertisement", "recommended", "related"],
            ):
                unwanted.decompose()

            content = article_element.get_text(strip=True)
            return content
        else:
            logger.warning(f"Could not find article content for URL: {url}")
            return None
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return None


def process_news_with_langchain(article_data):
    """
    Process the news article with LangChain to extract sentiment and topics
    """
    # This is placeholder code - replace with actual LangChain implementation
    # In a real implementation, you would:
    # 1. Use a language model to analyze the content
    # 2. Extract sentiment (positive, negative, neutral)
    # 3. Identify main topics/categories

    try:
        # Placeholder - replace with actual LangChain implementation
        processed_article = article_data.copy()
        processed_article["sentiment"] = "neutral"  # placeholder
        processed_article["topics"] = ["news", "general"]  # placeholder

        return processed_article
    except Exception as e:
        logger.error(f"Error processing article with LangChain: {str(e)}")
        return article_data


def index_article_in_elasticsearch(article):
    """
    Index the processed article in Elasticsearch
    """
    try:
        # Convert pydantic model to dict for indexing
        article_dict = article.dict()

        # Generate a document ID based on URL or title to avoid duplicates
        doc_id = (
            article_dict["link"]
            .replace("https://", "")
            .replace("http://", "")
            .replace("/", "_")
        )

        # Index the document
        es_client.index(index="articles", id=doc_id, document=article_dict)

        logger.info(f"Indexed article: {article.title}")
        return True
    except Exception as e:
        logger.error(f"Error indexing article in Elasticsearch: {str(e)}")
        return False


def cleanup_old_articles():
    """
    Delete articles older than 7 days from Elasticsearch
    """
    try:
        seven_days_ago = datetime.now().isoformat()

        # Delete old articles
        es_client.delete_by_query(
            index="articles",
            body={"query": {"range": {"publish_date": {"lt": seven_days_ago}}}},
        )

        logger.info("Cleaned up old articles")
    except Exception as e:
        logger.error(f"Error cleaning up old articles: {str(e)}")


def main():
    """
    Main function that orchestrates the news aggregation process
    """
    # Fetch news metadata from API
    news_items = fetch_news_metadata_from_api()
    if not news_items:
        logger.warning("No news items found. Exiting.")
        return

    # Initialize Selenium driver
    driver = initialize_selenium_driver()
    if not driver:
        logger.error("Failed to initialize Selenium driver. Exiting.")
        return

    try:
        # Process each news item
        for item in news_items:
            try:
                # Extract full content using Selenium
                content = extract_content_with_selenium(item["link"], driver)

                if not content:
                    continue

                # Create article object
                article = Article(
                    title=item["title"],
                    description=item.get("description", ""),
                    content=content,
                    publish_date=datetime.fromisoformat(
                        item["pubDate"]
                    ),
                    category=item["category"],
                    link=item["link"],
                )
                print("--------------------------------------------------------------------------------")
                print(article.title)
                print(article.content)
                print("--------------------------------------------------------------------------------")

                # Process with LangChain
            #  processed_article = process_news_with_langchain(article.dict())
            #  article = Article(**processed_article)

            #  # Index in Elasticsearch
            #  index_article_in_elasticsearch(article)

            except Exception as e:
                logger.error(f"Error processing news item: {str(e)}")
                continue

        # Clean up old articles
    #   cleanup_old_articles()

    finally:
        # Close the Selenium driver
        if driver:
            driver.quit()
            logger.info("Selenium driver closed")


if __name__ == "__main__":
    main()
