# Indian Financial Analyzer Setup Guide

This guide will help you set up and run the Indian Financial Analyzer application.

## Prerequisites

1. Python 3.8+ installed
2. MongoDB (optional, but recommended for full functionality)
3. API keys for required services:
   - Groq API key for LLM functionality
   - Tavily API key for news extraction

## Installation

1. Clone the repository or download the source code:

```bash
git clone https://github.com/username/indian-financial-analyzer.git
cd indian-financial-analyzer
```

2. Install the required Python packages:

```bash
pip install flask gitpython markdown motor networkx pandas pymongo requests
```

3. Set up API keys as environment variables:

```bash
# Linux/macOS
export GROQ_API_KEY="your_groq_api_key"
export TAVILY_API_KEY="your_tavily_api_key"

# Windows
set GROQ_API_KEY=your_groq_api_key
set TAVILY_API_KEY=your_tavily_api_key
```

4. (Optional) Configure MongoDB:

```bash
# If using a local MongoDB instance
export MONGODB_URI="mongodb://localhost:27017"
export MONGODB_DB_NAME="indian_financial_analyzer"

# If using MongoDB Atlas or other cloud provider
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net"
export MONGODB_DB_NAME="indian_financial_analyzer"
```

## Running the Application

1. Start the application:

```bash
python app.py
```

2. Open your browser and navigate to:

```
http://localhost:5000
```

## Setting Up Financial Books

The application uses a Retrieval-Augmented Generation (RAG) system to provide insights from financial books. To set up the books:

1. Ensure the `data/books` directory exists (it should be created automatically when the app runs)

2. Add text files of financial books to the `data/books` directory:
   - rich_dad_poor_dad.txt
   - psychology_of_money.txt
   - intelligent_investor.txt
   - let_stocks_do_the_work.txt
   - indian_financial_system.txt

## Configuration Options

You can customize the application by modifying the `config.py` file:

- Change logging level
- Modify file paths
- Update application settings

## Troubleshooting

### API Connection Issues

If you encounter issues connecting to external APIs:

1. Verify that your API keys are set correctly as environment variables
2. Check that the APIs are accessible from your network
3. Look for error messages in the application logs

### Database Connection Issues

If the application can't connect to MongoDB:

1. Verify that MongoDB is running and accessible
2. Check your MongoDB URI and database name
3. Ensure you have the necessary permissions to access the database

Note that the application will still function without MongoDB, but some features (like saving analysis results) will be limited.

### LLM-Related Issues

If AI functionality is not working:

1. Verify your Groq API key is correct
2. Check the application logs for specific error messages
3. Ensure the LLM service is accessible from your network

## Extending the Application

To add new functionality to the application:

1. **New Data Sources**: Add new modules in the `data_sources` directory
2. **Additional AI Features**: Extend the `ai` directory with new modules
3. **UI Enhancements**: Modify the templates and static files in the `templates` and `static` directories

## Running Tests

To run the test suite:

```bash
python -m unittest discover tests
```

## Deployment

For production deployment:

1. Use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn app:app -b 0.0.0.0:5000
```

2. Set up a reverse proxy with Nginx or similar
3. Configure proper security settings for a production environment
4. Use environment variables for all sensitive configuration

## Support

If you encounter any issues or have questions, please:

1. Check the application logs
2. Review this setup guide
3. Search for similar issues in the project repository
4. Contact the development team if the issue persists