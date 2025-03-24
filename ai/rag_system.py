"""
RAG (Retrieval-Augmented Generation) System for Financial Book Insights
"""
import os
import logging
import json
import re
from pathlib import Path
import config
from ai.groq_client import groq_client

logger = logging.getLogger(__name__)

class RAGFinancialBooks:
    """
    RAG system for extracting insights from financial books
    
    This system loads financial self-help books, creates embeddings of the content,
    and retrieves relevant passages to augment LLM responses with book insights.
    """
    
    def __init__(self, books_config=None, data_dir="data/books"):
        """
        Initialize the RAG system for financial books
        
        Args:
            books_config (list): List of book configurations with id, title, author, path
            data_dir (str): Directory containing book text files
        """
        self.books_config = books_config or config.FINANCIAL_BOOKS
        self.data_dir = data_dir
        self.books_content = {}
        self.chunks = {}
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load book contents
        self._load_books()
    
    def _load_books(self):
        """Load book contents from files"""
        for book in self.books_config:
            book_id = book["id"]
            book_path = book.get("path")
            
            if not book_path or not os.path.exists(book_path):
                # For demo/development, create placeholder content if file doesn't exist
                logger.warning(f"Book file not found: {book_path}. Creating placeholder content.")
                self._create_placeholder_content(book)
                book_path = book["path"]  # Update path after creating placeholder
            
            try:
                with open(book_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.books_content[book_id] = content
                    # Create chunks from the content
                    self.chunks[book_id] = self._create_chunks(content)
                    logger.info(f"Loaded book: {book['title']} with {len(self.chunks[book_id])} chunks")
            except Exception as e:
                logger.error(f"Error loading book {book_id}: {str(e)}")
    
    def _create_placeholder_content(self, book):
        """Create placeholder content for development/demo purposes"""
        os.makedirs(os.path.dirname(book["path"]), exist_ok=True)
        
        placeholder_content = f"""# {book['title']} by {book['author']}

## About This Book
This is a placeholder for the full content of {book['title']} by {book['author']}.

## Sample Concepts
Here are some key financial concepts from the book:

### Financial Independence
Building wealth is about creating assets that generate passive income.

### Investing Principles
Invest in assets that appreciate in value and generate cash flow.

### Money Management
Proper budgeting and expense management are essential for building wealth.

### Risk Management
Diversification is key to managing investment risks.

### Tax Planning
Understanding tax implications is crucial for preserving wealth.

### Indian Market Specifics
The Indian market offers unique opportunities and challenges for investors.

### Long-term Planning
Patience and long-term thinking are essential for financial success.
"""
        try:
            with open(book["path"], 'w', encoding='utf-8') as f:
                f.write(placeholder_content)
            logger.info(f"Created placeholder content for: {book['title']}")
        except Exception as e:
            logger.error(f"Error creating placeholder for {book['id']}: {str(e)}")
    
    def _create_chunks(self, text, chunk_size=500, overlap=50):
        """
        Split text into overlapping chunks for better retrieval
        
        Args:
            text (str): Text to split into chunks
            chunk_size (int): Size of each chunk in characters
            overlap (int): Overlap between chunks in characters
            
        Returns:
            list: List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # Try to find a good break point (newline or period followed by space)
            if end < text_length:
                # Look for paragraph break
                next_para = text.find('\n\n', end - 100, end + 100)
                if next_para != -1 and next_para - end < 100:
                    end = next_para
                else:
                    # Look for sentence break
                    next_period = text.find('. ', end - 50, end + 50)
                    if next_period != -1 and next_period - end < 50:
                        end = next_period + 1  # Include the period
            
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Move start position, with overlap
            start = end - overlap if end < text_length else text_length
        
        return chunks
    
    def semantic_search(self, query, book_id=None, top_k=3):
        """
        Perform semantic search on book content
        
        This is a simplified version that uses the Groq LLM for both embedding and retrieval
        In a production implementation, you would use dedicated embedding models and vector search
        
        Args:
            query (str): Search query
            book_id (str): Specific book ID to search within, or None for all books
            top_k (int): Number of top results to return
            
        Returns:
            list: Top matching passages
        """
        results = []
        
        # Define which books to search
        book_ids = [book_id] if book_id else self.chunks.keys()
        
        for current_book_id in book_ids:
            if current_book_id not in self.chunks:
                continue
                
            book_info = next((b for b in self.books_config if b["id"] == current_book_id), None)
            if not book_info:
                continue
                
            for chunk in self.chunks[current_book_id]:
                # Calculate relevance score using simple keyword matching
                # In a production system, this would use proper embeddings and similarity scores
                query_terms = set(re.findall(r'\w+', query.lower()))
                chunk_terms = set(re.findall(r'\w+', chunk.lower()))
                overlap = len(query_terms.intersection(chunk_terms))
                score = overlap / max(len(query_terms), 1)
                
                results.append({
                    "book_id": current_book_id,
                    "book_title": book_info["title"],
                    "book_author": book_info["author"],
                    "content": chunk,
                    "score": score
                })
        
        # Sort by score and take top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def generate_book_insight(self, query, book_id=None):
        """
        Generate insights from financial books based on a query
        
        Args:
            query (str): User query about financial concepts
            book_id (str): Specific book ID to search within, or None for all books
            
        Returns:
            dict: Generated insight with source information
        """
        # Retrieve relevant passages
        retrieved_passages = self.semantic_search(query, book_id)
        
        if not retrieved_passages:
            return {
                "insight": "No relevant insights found in the available financial books.",
                "sources": []
            }
        
        # Format context from retrieved passages
        context = "\n\n".join([
            f"From '{p['book_title']}' by {p['book_author']}:\n{p['content']}"
            for p in retrieved_passages
        ])
        
        # Generate insight using Groq LLM
        prompt = f"""You are a financial advisor specializing in Indian markets. Your task is to answer a question using insights from financial books.

Question: {query}

Here are relevant passages from financial books:
{context}

Based ONLY on the information provided in these passages, provide a comprehensive answer to the question.
Focus particularly on how these concepts apply in the Indian financial context.
Cite specific books when referencing particular ideas.
If the passages don't contain relevant information, acknowledge the limitations of your answer.
"""
        
        response = groq_client.generate_response(prompt, temperature=0.3)
        
        return {
            "insight": response.get("text", "Failed to generate insight"),
            "sources": [
                {
                    "book_title": p["book_title"],
                    "book_author": p["book_author"],
                    "snippet": p["content"][:150] + "..." if len(p["content"]) > 150 else p["content"]
                }
                for p in retrieved_passages
            ]
        }
    
    def get_book_summary(self, book_id):
        """
        Generate a summary of a financial book
        
        Args:
            book_id (str): Book ID to summarize
            
        Returns:
            dict: Book summary and key concepts
        """
        if book_id not in self.books_content:
            return {
                "error": f"Book with ID '{book_id}' not found",
                "summary": "",
                "key_concepts": []
            }
        
        book_info = next((b for b in self.books_config if b["id"] == book_id), None)
        if not book_info:
            return {
                "error": f"Book configuration for ID '{book_id}' not found",
                "summary": "",
                "key_concepts": []
            }
        
        # Take a sample of the book content for summarization
        content_sample = self.books_content[book_id][:5000]  # First 5000 chars for summary
        
        prompt = f"""You are a financial literature expert. Summarize the key ideas from this excerpt of '{book_info['title']}' by {book_info['author']}.

Excerpt:
{content_sample}

Provide:
1. A concise 2-paragraph summary of the book's main ideas
2. A list of 5-7 key financial concepts covered in the book
3. How these concepts apply specifically to the Indian financial market

Your response should be structured in JSON format with fields: 'summary', 'key_concepts', 'indian_market_relevance'."""
        
        response = groq_client.generate_response(prompt, temperature=0.3)
        
        try:
            # Try to parse JSON from the response
            result = json.loads(response.get("text", "{}"))
            return {
                "summary": result.get("summary", ""),
                "key_concepts": result.get("key_concepts", []),
                "indian_market_relevance": result.get("indian_market_relevance", "")
            }
        except json.JSONDecodeError:
            # Fallback if response is not in JSON format
            return {
                "summary": response.get("text", "Failed to generate summary"),
                "key_concepts": [],
                "indian_market_relevance": ""
            }
    
    def get_available_books(self):
        """
        Get list of available financial books
        
        Returns:
            list: List of book information dictionaries
        """
        return [
            {
                "id": book["id"],
                "title": book["title"],
                "author": book["author"]
            }
            for book in self.books_config
        ]

# Create RAG system instance
rag_system = RAGFinancialBooks()