/**
 * Indian Financial Analyzer - Client-side JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    setupNavigation();
    setupGenerateAnalysisButtons();
    setupStockSearch();
    loadBookList();
    setupBookInsights();
    setupPortfolioManagement();
});

/**
 * Sets up navigation between sections
 */
function setupNavigation() {
    const navLinks = document.querySelectorAll('.main-nav a');
    const sections = document.querySelectorAll('section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active link
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Show corresponding section
            const targetId = this.getAttribute('href').substring(1);
            sections.forEach(section => {
                section.classList.remove('active-section');
                if (section.id === targetId) {
                    section.classList.add('active-section');
                }
            });
        });
    });
}

/**
 * Sets up buttons for generating analysis
 */
function setupGenerateAnalysisButtons() {
    // Market analysis button
    const marketAnalysisBtn = document.getElementById('generate-market-analysis');
    if (marketAnalysisBtn) {
        marketAnalysisBtn.addEventListener('click', function() {
            generateMarketAnalysis();
        });
    }
    
    // Stock analysis button
    const stockAnalysisBtn = document.getElementById('generate-stock-analysis');
    if (stockAnalysisBtn) {
        stockAnalysisBtn.addEventListener('click', function() {
            generateStockAnalysis();
        });
    }
    
    // Detailed market analysis form
    const marketAnalysisForm = document.getElementById('market-analysis-form');
    if (marketAnalysisForm) {
        marketAnalysisForm.addEventListener('submit', function(e) {
            e.preventDefault();
            generateDetailedMarketAnalysis();
        });
    }
}

/**
 * Generates a market analysis
 */
function generateMarketAnalysis() {
    const resultContainer = document.getElementById('market-analysis-result');
    if (!resultContainer) return;
    
    resultContainer.innerHTML = '<p>Generating market analysis... Please wait.</p>';
    
    // Call the market analysis API
    fetch('/api/analyze/market')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.data) {
                resultContainer.innerHTML = `<p>${data.data.summary}</p>`;
            } else {
                resultContainer.innerHTML = `<p>Error: ${data.message || 'Failed to generate analysis'}</p>`;
            }
        })
        .catch(error => {
            resultContainer.innerHTML = `<p>Error: ${error.message}</p>`;
        });
}

/**
 * Generates a detailed market analysis based on form inputs
 */
function generateDetailedMarketAnalysis() {
    const timeframe = document.getElementById('analysis-timeframe').value;
    const focus = document.getElementById('analysis-focus').value;
    const resultContainer = document.getElementById('detailed-market-analysis');
    
    resultContainer.innerHTML = '<p>Generating detailed market analysis... Please wait.</p>';
    
    // For demonstration, we're using the same API, but in a real implementation
    // you would pass the timeframe and focus parameters to a different endpoint
    fetch('/api/analyze/market')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.data) {
                resultContainer.innerHTML = `
                    <h4>Market Analysis (${timeframe} Timeframe, ${focus} Focus)</h4>
                    <div class="analysis-content">
                        <p>${data.data.summary}</p>
                    </div>
                `;
            } else {
                resultContainer.innerHTML = `<p>Error: ${data.message || 'Failed to generate analysis'}</p>`;
            }
        })
        .catch(error => {
            resultContainer.innerHTML = `<p>Error: ${error.message}</p>`;
        });
}

/**
 * Sets up stock search functionality
 */
function setupStockSearch() {
    const searchButton = document.getElementById('stock-search-button');
    const searchInput = document.getElementById('stock-search-input');
    const resultsContainer = document.getElementById('stock-search-results');
    
    if (!searchButton || !searchInput || !resultsContainer) return;
    
    searchButton.addEventListener('click', function() {
        const query = searchInput.value.trim();
        if (!query) return;
        
        resultsContainer.innerHTML = '<p>Searching stocks...</p>';
        
        // Call the stock search API
        fetch(`/api/stock/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.results) {
                    if (data.results.length > 0) {
                        let html = '<div class="search-results-list">';
                        data.results.forEach(stock => {
                            html += `
                                <div class="search-result-item" data-symbol="${stock.symbol}">
                                    <h4>${stock.name || stock.symbol}</h4>
                                    <p>${stock.symbol} | ${stock.sector || 'N/A'}</p>
                                </div>
                            `;
                        });
                        html += '</div>';
                        resultsContainer.innerHTML = html;
                        
                        // Add click event to results
                        document.querySelectorAll('.search-result-item').forEach(item => {
                            item.addEventListener('click', function() {
                                const symbol = this.getAttribute('data-symbol');
                                loadStockDetails(symbol);
                            });
                        });
                    } else {
                        resultsContainer.innerHTML = '<p>No stocks found matching your query.</p>';
                    }
                } else {
                    resultsContainer.innerHTML = `<p>Error: ${data.message || 'Failed to search stocks'}</p>`;
                }
            })
            .catch(error => {
                resultsContainer.innerHTML = `<p>Error: ${error.message}</p>`;
            });
    });
    
    // Also trigger search on Enter key
    searchInput.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') {
            searchButton.click();
        }
    });
}

/**
 * Loads details for a selected stock
 * 
 * @param {string} symbol - The stock symbol to load
 */
function loadStockDetails(symbol) {
    const detailsContainer = document.getElementById('stock-details-container');
    const analysisButton = document.getElementById('generate-stock-analysis');
    
    if (!detailsContainer || !analysisButton) return;
    
    detailsContainer.innerHTML = '<p>Loading stock details...</p>';
    
    // Call the stock details API
    fetch(`/api/stock/${symbol}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const priceData = data.price_data || {};
                const companyInfo = data.company_info || {};
                
                let html = `
                    <div class="stock-header">
                        <h4>${companyInfo.name || symbol}</h4>
                        <p class="stock-symbol">${symbol}</p>
                    </div>
                    <div class="stock-price">
                        <p class="current-price">₹${(companyInfo.current_price || 0).toFixed(2)}</p>
                `;
                
                if (priceData.change !== undefined) {
                    const changeClass = priceData.change >= 0 ? 'positive' : 'negative';
                    const changeSign = priceData.change >= 0 ? '+' : '';
                    html += `
                        <p class="price-change ${changeClass}">
                            ${changeSign}${priceData.change.toFixed(2)} (${changeSign}${priceData.change_percent.toFixed(2)}%)
                        </p>
                    `;
                }
                
                html += `
                    </div>
                    <div class="stock-info">
                        <p><strong>Exchange:</strong> ${companyInfo.exchange || 'N/A'}</p>
                        <p><strong>Sector:</strong> ${companyInfo.sector || 'N/A'}</p>
                        <p><strong>Industry:</strong> ${companyInfo.industry || 'N/A'}</p>
                        <p><strong>Market Cap:</strong> ₹${((companyInfo.market_cap || 0) / 10000000).toFixed(2)} Cr</p>
                        <p><strong>P/E Ratio:</strong> ${companyInfo.pe_ratio?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Dividend Yield:</strong> ${((companyInfo.dividend_yield || 0) * 100).toFixed(2)}%</p>
                    </div>
                `;
                
                if (companyInfo.summary) {
                    html += `
                        <div class="company-summary">
                            <h5>Company Overview</h5>
                            <p>${companyInfo.summary}</p>
                        </div>
                    `;
                }
                
                detailsContainer.innerHTML = html;
                
                // Enable the analysis button and store the symbol
                analysisButton.disabled = false;
                analysisButton.setAttribute('data-symbol', symbol);
                analysisButton.setAttribute('data-company', companyInfo.name || '');
            } else {
                detailsContainer.innerHTML = `<p>Error: ${data.message || 'Failed to load stock details'}</p>`;
                analysisButton.disabled = true;
            }
        })
        .catch(error => {
            detailsContainer.innerHTML = `<p>Error: ${error.message}</p>`;
            analysisButton.disabled = true;
        });
}

/**
 * Generates an AI analysis of the selected stock
 */
function generateStockAnalysis() {
    const button = document.getElementById('generate-stock-analysis');
    const resultContainer = document.getElementById('stock-analysis-result');
    
    if (!button || !resultContainer) return;
    
    const symbol = button.getAttribute('data-symbol');
    const companyName = button.getAttribute('data-company');
    
    if (!symbol) {
        resultContainer.innerHTML = '<p>Error: No stock selected</p>';
        return;
    }
    
    resultContainer.innerHTML = '<p>Generating stock analysis... Please wait.</p>';
    
    // Call the stock analysis API
    fetch('/api/analyze/stock', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol,
            company_name: companyName
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.data) {
                resultContainer.innerHTML = `
                    <h4>AI Analysis for ${data.data.company_name || symbol}</h4>
                    <div class="analysis-content">
                        <p>${data.data.analysis}</p>
                    </div>
                `;
            } else {
                resultContainer.innerHTML = `<p>Error: ${data.message || 'Failed to generate analysis'}</p>`;
            }
        })
        .catch(error => {
            resultContainer.innerHTML = `<p>Error: ${error.message}</p>`;
        });
}

/**
 * Loads the list of available financial books
 */
function loadBookList() {
    const bookListContainer = document.getElementById('book-list');
    if (!bookListContainer) return;
    
    fetch('/api/books')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.data) {
                if (data.data.length > 0) {
                    let html = '';
                    data.data.forEach(book => {
                        html += `
                            <div class="book-card" data-book-id="${book.id}">
                                <h4>${book.title}</h4>
                                <p>by ${book.author}</p>
                            </div>
                        `;
                    });
                    bookListContainer.innerHTML = html;
                    
                    // Add click event to book cards
                    document.querySelectorAll('.book-card').forEach(card => {
                        card.addEventListener('click', function() {
                            document.querySelectorAll('.book-card').forEach(c => c.classList.remove('selected'));
                            this.classList.add('selected');
                            
                            if (document.getElementById('search-all-books').checked) {
                                document.getElementById('search-all-books').checked = false;
                            }
                        });
                    });
                } else {
                    bookListContainer.innerHTML = '<p>No books available.</p>';
                }
            } else {
                bookListContainer.innerHTML = `<p>Error: ${data.message || 'Failed to load books'}</p>`;
            }
        })
        .catch(error => {
            bookListContainer.innerHTML = `<p>Error: ${error.message}</p>`;
        });
}

/**
 * Sets up book insights functionality
 */
function setupBookInsights() {
    const insightsButton = document.getElementById('get-insights-button');
    const queryInput = document.getElementById('insights-query');
    const searchAllCheckbox = document.getElementById('search-all-books');
    const resultsContainer = document.getElementById('book-insights-result');
    
    if (!insightsButton || !queryInput || !searchAllCheckbox || !resultsContainer) return;
    
    insightsButton.addEventListener('click', function() {
        const query = queryInput.value.trim();
        if (!query) {
            resultsContainer.innerHTML = '<p>Please enter a financial question.</p>';
            return;
        }
        
        let bookId = null;
        if (!searchAllCheckbox.checked) {
            const selectedBook = document.querySelector('.book-card.selected');
            if (selectedBook) {
                bookId = selectedBook.getAttribute('data-book-id');
            } else {
                resultsContainer.innerHTML = '<p>Please select a book or check "Search across all books".</p>';
                return;
            }
        }
        
        resultsContainer.innerHTML = '<p>Generating insights... Please wait.</p>';
        
        // Call the book insights API
        fetch('/api/books/insights', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                book_id: bookId
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.data) {
                    let html = `
                        <div class="insights-content">
                            <p>${data.data.insight}</p>
                        </div>
                    `;
                    
                    if (data.data.sources && data.data.sources.length > 0) {
                        html += '<div class="insights-sources">';
                        html += '<h5>Sources</h5>';
                        html += '<ul>';
                        data.data.sources.forEach(source => {
                            html += `<li><strong>${source.book_title}</strong> by ${source.book_author}: "${source.snippet}"</li>`;
                        });
                        html += '</ul>';
                        html += '</div>';
                    }
                    
                    resultsContainer.innerHTML = html;
                } else {
                    resultsContainer.innerHTML = `<p>Error: ${data.message || 'Failed to generate insights'}</p>`;
                }
            })
            .catch(error => {
                resultsContainer.innerHTML = `<p>Error: ${error.message}</p>`;
            });
    });
    
    // Also trigger on Enter key in textarea
    queryInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            insightsButton.click();
        }
    });
}

/**
 * Sets up portfolio management functionality
 */
function setupPortfolioManagement() {
    const loginButton = document.getElementById('login-button');
    
    if (loginButton) {
        loginButton.addEventListener('click', function() {
            // For demonstration, we'll just show the portfolio form
            document.getElementById('portfolio-stocks').innerHTML = `
                <div class="portfolio-holdings">
                    <p>You don't have any stocks in your portfolio yet.</p>
                </div>
            `;
            document.getElementById('add-stock-form').style.display = 'block';
            loginButton.style.display = 'none';
            
            // Set up add stock functionality
            const addStockButton = document.getElementById('add-stock-button');
            if (addStockButton) {
                addStockButton.addEventListener('click', addStockToPortfolio);
            }
        });
    }
}

/**
 * Adds a stock to the portfolio
 */
function addStockToPortfolio() {
    const symbolInput = document.getElementById('add-stock-symbol');
    const quantityInput = document.getElementById('add-stock-quantity');
    const holdingsContainer = document.querySelector('.portfolio-holdings');
    
    if (!symbolInput || !quantityInput || !holdingsContainer) return;
    
    const symbol = symbolInput.value.trim().toUpperCase();
    const quantity = parseInt(quantityInput.value);
    
    if (!symbol) {
        alert('Please enter a stock symbol');
        return;
    }
    
    if (isNaN(quantity) || quantity <= 0) {
        alert('Please enter a valid quantity');
        return;
    }
    
    // For demonstration, we'll just add the stock to the UI
    if (holdingsContainer.querySelector('p')) {
        holdingsContainer.innerHTML = '';
    }
    
    const stockElement = document.createElement('div');
    stockElement.className = 'portfolio-stock';
    stockElement.innerHTML = `
        <div class="stock-info">
            <h4>${symbol}</h4>
            <p>${quantity} shares</p>
        </div>
        <button class="remove-stock" data-symbol="${symbol}">Remove</button>
    `;
    
    holdingsContainer.appendChild(stockElement);
    
    // Clear inputs
    symbolInput.value = '';
    quantityInput.value = '';
    
    // Add remove functionality
    stockElement.querySelector('.remove-stock').addEventListener('click', function() {
        stockElement.remove();
        if (holdingsContainer.childElementCount === 0) {
            holdingsContainer.innerHTML = '<p>You don\'t have any stocks in your portfolio yet.</p>';
        }
    });
}