"""
RAG (Retrieval-Augmented Generation) System for Financial Books
"""
import os
import json
import logging
import re
import pickle
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import markdown
import chromadb
from chromadb.utils import embedding_functions

from ai.groq_client import GroqClient

logger = logging.getLogger(__name__)

class RAGSystem:
    """RAG system for financial book insights"""
    
    def __init__(self, books_dir="data/books", cache_dir="data/cache", groq_client=None):
        """
        Initialize the RAG system.
        
        Args:
            books_dir: Directory containing financial book text files
            cache_dir: Directory for caching embeddings and search results
            groq_client: Optional pre-configured Groq client
        """
        self.books_dir = Path(books_dir)
        self.cache_dir = Path(cache_dir)
        self.groq_client = groq_client or GroqClient()
        
        # Make sure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Directory for storing embeddings
        self.embeddings_dir = Path(self.cache_dir) / "embeddings"
        os.makedirs(self.embeddings_dir, exist_ok=True)
        
        # Initialize the ChromaDB client
        persist_dir = str(self.embeddings_dir / "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)
        
        # Use a default embedding function that's lightweight but effective
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Load book metadata
        self.books = self._load_books()
        
        # Process books and create embeddings if they don't exist
        self.process_books()
        
    def _load_books(self) -> List[Dict[str, Any]]:
        """
        Load metadata for all available books.
        
        Returns:
            List of book metadata dictionaries
        """
        books = []
        
        # Map filenames to readable titles and authors
        filename_to_metadata = {
            "rich_dad_poor_dad.txt": {
                "id": "rich_dad_poor_dad",
                "title": "Rich Dad Poor Dad",
                "author": "Robert Kiyosaki",
                "year": 1997,
                "description": "Personal finance classic on mindset and financial education"
            },
            "psychology_of_money.txt": {
                "id": "psychology_of_money",
                "title": "The Psychology of Money",
                "author": "Morgan Housel",
                "year": 2020,
                "description": "Insights on how emotions and psychology affect financial decisions"
            },
            "intelligent_investor.txt": {
                "id": "intelligent_investor",
                "title": "The Intelligent Investor",
                "author": "Benjamin Graham",
                "year": 1949,
                "description": "Classic text on value investing strategies and principles"
            },
            "let_stocks_do_the_work.txt": {
                "id": "let_stocks_do_the_work",
                "title": "Let Stocks Do The Work",
                "author": "Ellis Traub",
                "year": 2001,
                "description": "Guide to long-term investing through quality stocks"
            },
            "indian_financial_system.txt": {
                "id": "indian_financial_system",
                "title": "Indian Financial System",
                "author": "Bharati V. Pathak",
                "year": 2014,
                "description": "Comprehensive overview of India's financial system and markets"
            }
        }
        
        # Check which books are actually available in the books directory
        for filename, metadata in filename_to_metadata.items():
            file_path = self.books_dir / filename
            if file_path.exists():
                # Add file path to metadata
                metadata["file_path"] = str(file_path)
                books.append(metadata)
                
        logger.info(f"Loaded metadata for {len(books)} financial books")
        return books

    def get_available_books(self) -> List[Dict[str, Any]]:
        """
        Get a list of available financial books.
        
        Returns:
            List of book metadata dictionaries (without file paths)
        """
        # Return books without exposing file paths
        return [{k: v for k, v in book.items() if k != 'file_path'} for book in self.books]

    def get_book_summary(self, book_id: str) -> Dict[str, Any]:
        """
        Get a summary of a specific book.
        
        Args:
            book_id: Identifier for the book
            
        Returns:
            Dictionary with book summary information
        """
        # Find the book with matching ID
        book = next((b for b in self.books if b["id"] == book_id), None)
        
        if not book:
            return {
                "error": f"Book with ID '{book_id}' not found"
            }
        
        # Check if we have a cached summary
        cache_file = self.cache_dir / f"{book_id}_summary.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading cached summary for {book_id}: {e}")
        
        # If no cached summary, generate one
        file_path = book["file_path"]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read the first part of the book for the summary (limit to avoid token limits)
                text = f.read(20000)  # First ~20k characters
            
            # Get summary from Groq
            prompt = (
                f"You are helping to create a summary for '{book['title']}' by {book['author']}.\n"
                "Based on the text provided, write a concise summary of the book that includes:\n"
                "1. The main thesis or premise of the book\n"
                "2. Key financial concepts covered\n"
                "3. Major takeaways or lessons for readers\n"
                "4. Who would benefit most from reading this book\n\n"
                "Text excerpt:\n"
                f"{text}\n\n"
                "Please provide a well-structured summary in 250-300 words."
            )
            
            summary_text = self.groq_client.generate_text(prompt)
            
            # Create the summary object
            summary = {
                "book_id": book_id,
                "title": book["title"],
                "author": book["author"],
                "year": book["year"],
                "description": book["description"],
                "summary": summary_text,
            }
            
            # Cache the summary
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for {book_id}: {e}")
            return {
                "book_id": book_id,
                "title": book["title"],
                "author": book["author"],
                "error": f"Failed to generate summary: {str(e)}"
            }

    def process_books(self):
        """
        Public method to process all books and create embeddings.
        """
        self._process_books()
        
    def _process_books(self):
        """
        Process all books to create chunk embeddings using ChromaDB.
        These embeddings will be used for faster retrieval later.
        """
        for book in self.books:
            book_id = book["id"]
            collection_name = f"book_{book_id}"
            
            # Check if this collection already exists in ChromaDB
            existing_collections = self.chroma_client.list_collections()
            collection_exists = collection_name in existing_collections
            
            if collection_exists:
                logger.info(f"Collection for {book_id} already exists in ChromaDB, skipping processing")
                continue
                
            logger.info(f"Processing book {book_id} to create embeddings in ChromaDB")
            
            try:
                # Read the book content
                with open(book["file_path"], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split into chunks (paragraphs)
                paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
                
                # Combine short paragraphs to make reasonable-sized chunks
                chunks = []
                chunk_ids = []
                chunk_metadatas = []
                current_chunk = ""
                max_chunk_length = 1000  # characters (ChromaDB can handle larger chunks)
                chunk_index = 0
                
                for p in paragraphs:
                    if len(current_chunk) + len(p) <= max_chunk_length:
                        current_chunk += "\n\n" + p if current_chunk else p
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                            chunk_ids.append(f"{book_id}_{chunk_index}")
                            chunk_metadatas.append({
                                "book_id": book_id,
                                "book_title": book["title"],
                                "book_author": book["author"],
                                "chunk_index": chunk_index,
                                "source": "book"
                            })
                            chunk_index += 1
                        current_chunk = p
                        
                if current_chunk:
                    chunks.append(current_chunk)
                    chunk_ids.append(f"{book_id}_{chunk_index}")
                    chunk_metadatas.append({
                        "book_id": book_id,
                        "book_title": book["title"],
                        "book_author": book["author"],
                        "chunk_index": chunk_index,
                        "source": "book"
                    })
                
                # Create a new collection in ChromaDB for this book
                if chunks:  # Only proceed if we have chunks
                    # Get or create collection
                    collection = self.chroma_client.create_collection(
                        name=collection_name,
                        embedding_function=self.embedding_function,
                        metadata={"book_id": book_id, "title": book["title"], "author": book["author"]}
                    )
                    
                    # Add documents in batches to avoid memory issues
                    batch_size = 100
                    for i in range(0, len(chunks), batch_size):
                        batch_end = min(i + batch_size, len(chunks))
                        collection.add(
                            documents=chunks[i:batch_end],
                            ids=chunk_ids[i:batch_end],
                            metadatas=chunk_metadatas[i:batch_end]
                        )
                        
                    # Persist the changes
                    self.chroma_client.persist()
                    
                    logger.info(f"Created ChromaDB collection with {len(chunks)} chunks for {book_id}")
                else:
                    logger.warning(f"No chunks found for {book_id}")
                    
            except Exception as e:
                logger.error(f"Error processing embeddings for {book_id}: {e}")
    
    def _get_book_collection(self, book_id: str):
        """
        Get the ChromaDB collection for a specific book.
        
        Args:
            book_id: The book ID
            
        Returns:
            ChromaDB collection or None if not found
        """
        collection_name = f"book_{book_id}"
        
        try:
            # Check if this collection exists in ChromaDB
            existing_collections = self.chroma_client.list_collections()
            collection_exists = collection_name in existing_collections
            
            if not collection_exists:
                logger.warning(f"Collection for {book_id} not found in ChromaDB, processing book")
                self._process_books()
                
                # Check again after processing
                existing_collections = self.chroma_client.list_collections()
                collection_exists = any(collection.name == collection_name for collection in existing_collections)
                
                if not collection_exists:
                    logger.error(f"Failed to create collection for {book_id}")
                    return None
            
            # Get the collection
            collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            return collection
        except Exception as e:
            logger.error(f"Error getting ChromaDB collection for {book_id}: {e}")
            return None
    
    def _extract_relevant_passages(self, book_id: str, query: str, max_passages: int = 3) -> List[Dict[str, Any]]:
        """
        Extract passages from a book that are relevant to a query using ChromaDB.
        
        Args:
            book_id: ID of the book to search
            query: Query to search for
            max_passages: Maximum number of passages to return
            
        Returns:
            List of relevant passages with metadata
        """
        book = next((b for b in self.books if b["id"] == book_id), None)
        
        if not book or "file_path" not in book:
            logger.error(f"Book with ID '{book_id}' not found or has no file path")
            return []
        
        # Check if we have a cached result for this query and book
        cache_key = f"{book_id}_{hash(query)}"
        cache_file = self.cache_dir / f"{cache_key}_passages.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading cached passages for {cache_key}: {e}")
        
        # Try using ChromaDB approach
        try:
            # Get the collection for this book
            collection = self._get_book_collection(book_id)
            
            if collection:
                # Query the collection for similar passages
                results = collection.query(
                    query_texts=[query],
                    n_results=max_passages,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results and len(results["documents"]) > 0 and len(results["documents"][0]) > 0:
                    # Prepare the passages with the book metadata
                    passages = []
                    for i, (text, metadata, distance) in enumerate(zip(
                        results["documents"][0], 
                        results["metadatas"][0], 
                        results["distances"][0]
                    )):
                        # Convert distance to similarity score (ChromaDB returns distance, lower is better)
                        # Simple conversion: similarity = 1 - normalized_distance
                        similarity = 1.0 - min(distance, 1.0)
                        
                        passage = {
                            "book_id": book_id,
                            "book_title": book["title"],
                            "book_author": book["author"],
                            "text": text,
                            "relevance": f"Semantic similarity: {similarity:.4f}",
                            "similarity_score": float(similarity)
                        }
                        passages.append(passage)
                    
                    # Cache the results
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(passages, f, indent=2)
                    
                    return passages
                
            # If collection is empty or doesn't exist, fall back to the original approach
            logger.warning(f"ChromaDB collection for {book_id} returned no results, falling back to LLM approach")
            
        except Exception as e:
            logger.error(f"Error in ChromaDB retrieval for {book_id}: {e}")
            # Fall back to the original approach
        
        # Fall back to the original approach if embeddings don't work
        # This is our backup approach using keyword matching and LLM
        
        try:
            # Read the book content
            with open(book["file_path"], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into chunks (paragraphs)
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
            
            # If there are too many paragraphs, combine some to reduce the number
            chunks = []
            current_chunk = ""
            max_chunk_length = 500  # characters
            
            for p in paragraphs:
                if len(current_chunk) + len(p) <= max_chunk_length:
                    current_chunk += "\n\n" + p if current_chunk else p
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = p
                    
            if current_chunk:
                chunks.append(current_chunk)
            
            # Use a cache to avoid reprocessing the same query for the same book
            cache_key = f"{book_id}_{hash(query)}"
            cache_file = self.cache_dir / f"{cache_key}_passages.json"
            
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Error loading cached passages for {cache_key}: {e}")
            
            # Approach 1: For small books, we can ask the LLM to find relevant passages directly
            if len(chunks) < 50:  # Arbitrary threshold
                prompt = (
                    f"You are helping to find passages from '{book['title']}' by {book['author']} "
                    f"that are relevant to the query: '{query}'\n\n"
                    "Book content is provided below. Identify the {max_passages} most relevant passages "
                    "and return them in JSON format with the following structure:\n"
                    "[\n"
                    "  {\n"
                    "    \"text\": \"The passage text...\",\n"
                    "    \"relevance\": \"Brief explanation of how this passage relates to the query\"\n"
                    "  },\n"
                    "  ...\n"
                    "]\n\n"
                    "Book Content:\n"
                    f"{content[:50000]}"  # Limit content to avoid token limits
                )
                
                response = self.groq_client.generate_text(prompt)
                
                # Try to extract JSON from the response
                try:
                    # Look for JSON in the response
                    match = re.search(r'(\[\s*\{.*\}\s*\])', response, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        passages = json.loads(json_str)
                    else:
                        # Try to parse the entire response as JSON
                        passages = json.loads(response)
                        
                    # Add book metadata to each passage
                    for passage in passages:
                        passage["book_id"] = book_id
                        passage["book_title"] = book["title"]
                        passage["book_author"] = book["author"]
                    
                    # Cache the results
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(passages, f, indent=2)
                    
                    return passages[:max_passages]
                        
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.error(f"Error parsing LLM response as JSON: {e}")
                    # Fall back to approach 2
            
            # Approach 2: For longer books, we need to be more selective
            # This is a simple keyword matching approach for demo purposes
            # In a real implementation, this would use embeddings and semantic search
            query_keywords = set(re.findall(r'\w+', query.lower()))
            
            scored_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_text = chunk.lower()
                score = sum(1 for kw in query_keywords if kw in chunk_text)
                scored_chunks.append((score, i, chunk))
            
            # Sort by score (descending)
            scored_chunks.sort(reverse=True)
            
            # Take the top chunks
            top_chunks = scored_chunks[:min(max_passages*2, len(scored_chunks))]
            
            # Ask the LLM to evaluate and rank these chunks
            chunks_with_index = [f"[{i+1}] {chunk}" for _, i, chunk in top_chunks]
            chunks_text = "\n\n".join(chunks_with_index)
            
            prompt = (
                f"You are helping to find passages from '{book['title']}' by {book['author']} "
                f"that are relevant to the query: '{query}'\n\n"
                "Below are some candidate passages. Rank the top {max_passages} most relevant passages "
                "and return them in JSON format with the following structure:\n"
                "[\n"
                "  {\n"
                "    \"passage_number\": 1,  // The index number in brackets\n"
                "    \"text\": \"The passage text...\",\n"
                "    \"relevance\": \"Brief explanation of how this passage relates to the query\"\n"
                "  },\n"
                "  ...\n"
                "]\n\n"
                "Candidate Passages:\n"
                f"{chunks_text}"
            )
            
            response = self.groq_client.generate_text(prompt)
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                match = re.search(r'(\[\s*\{.*\}\s*\])', response, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    ranked_passages = json.loads(json_str)
                else:
                    # Try to parse the entire response as JSON
                    ranked_passages = json.loads(response)
                
                # Process the ranked passages to get the actual chunks
                passages = []
                for ranked in ranked_passages[:max_passages]:
                    if "passage_number" in ranked:
                        idx = int(ranked["passage_number"]) - 1
                        if 0 <= idx < len(chunks_with_index):
                            # Extract the original text (remove the index prefix)
                            original_text = re.sub(r'^\[\d+\]\s*', '', chunks_with_index[idx])
                            passage = {
                                "book_id": book_id,
                                "book_title": book["title"],
                                "book_author": book["author"],
                                "text": original_text,
                                "relevance": ranked.get("relevance", "")
                            }
                            passages.append(passage)
                
                # Cache the results
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(passages, f, indent=2)
                
                return passages
                
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Error parsing LLM response as JSON: {e}")
                
                # Fallback: Just return the top chunks with minimal processing
                passages = []
                for _, i, chunk in top_chunks[:max_passages]:
                    passage = {
                        "book_id": book_id,
                        "book_title": book["title"],
                        "book_author": book["author"],
                        "text": chunk,
                        "relevance": "Matched query keywords"
                    }
                    passages.append(passage)
                
                return passages
            
        except Exception as e:
            logger.error(f"Error extracting passages from {book_id}: {e}")
            return []

    def generate_book_insight(self, query: str, book_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate insights from books based on a query.
        
        Args:
            query: The user's query about financial concepts
            book_id: Optional specific book to search in (if None, search all books)
            
        Returns:
            Dictionary with generated insight and source references
        """
        # Check if we have a cached response for this query
        cache_key = f"{hash(query)}_{book_id or 'all'}"
        cache_file = self.cache_dir / f"{cache_key}_insight.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading cached insight for {cache_key}: {e}")
        
        # Get relevant passages from the specified book or all books
        all_passages = []
        
        if book_id:
            # Search in the specific book
            all_passages = self._extract_relevant_passages(book_id, query)
        else:
            # Search across all books
            for book in self.books:
                passages = self._extract_relevant_passages(book["id"], query, max_passages=2)
                all_passages.extend(passages)
            
            # Sort by relevance (assuming more detailed relevance scoring in a real implementation)
            # For now, we'll just take the top 5
            all_passages = all_passages[:5]
        
        if not all_passages:
            return {
                "query": query,
                "insight": f"No relevant insights found for query: '{query}'",
                "sources": []
            }
        
        # Build context from passages
        context = ""
        for i, passage in enumerate(all_passages):
            context += f"[Passage {i+1}] From '{passage['book_title']}' by {passage['book_author']}:\n"
            context += f"\"{passage['text']}\"\n\n"
        
        # Generate insight using LLM
        prompt = (
            "You are a financial advisor specializing in Indian markets and personal finance. "
            f"A user has asked: \"{query}\"\n\n"
            "Based on the following passages from financial books, provide a thoughtful, "
            "accurate response that synthesizes the insights from these sources while "
            "focusing on relevance to Indian investors and markets where applicable.\n\n"
            f"{context}\n"
            "Please provide a well-structured response that answers the query, incorporating "
            "the wisdom from these financial texts, and makes it relevant to the Indian financial context."
        )
        
        insight = self.groq_client.generate_text(prompt)
        
        # Format sources from passages
        sources = []
        for passage in all_passages:
            source = {
                "book_id": passage["book_id"],
                "book_title": passage["book_title"],
                "book_author": passage["book_author"],
                "snippet": passage["text"][:150] + "..." if len(passage["text"]) > 150 else passage["text"]
            }
            sources.append(source)
        
        result = {
            "query": query,
            "insight": insight,
            "sources": sources
        }
        
        # Cache the result
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        return result

    def answer_financial_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a financial question using book knowledge and LLM.
        
        Args:
            question: The financial question to answer
            
        Returns:
            Dictionary with answer and source references
        """
        # This is similar to generate_book_insight but focuses on direct answers
        
        # First, get book insights
        book_insight = self.generate_book_insight(question)
        
        # Then, use the LLM to refine into a direct answer
        prompt = (
            "You are a financial advisor specializing in Indian markets and personal finance. "
            f"A user has asked: \"{question}\"\n\n"
            "Based on the following information derived from financial books, provide a clear, "
            "direct answer to the question. Focus on accuracy and relevance to Indian markets "
            "where applicable.\n\n"
            f"Information from financial books:\n{book_insight['insight']}\n\n"
            "Please provide a concise, factual answer to the user's question."
        )
        
        answer = self.groq_client.generate_text(prompt)
        
        return {
            "question": question,
            "answer": answer,
            "sources": book_insight["sources"]
        }


# Initialize global instance
rag_system = None

# We'll initialize this properly in app.py or when imported
def initialize_rag_system():
    global rag_system
    if rag_system is None:
        rag_system = RAGSystem()
    return rag_system