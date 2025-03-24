/**
 * Financial Analyzer - Report JavaScript
 * 
 * This file contains the client-side functionality for the Financial Analyzer
 * report dashboard, handling UI interactions, API calls, and data visualization.
 */

// Initialize the application when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();

    // Setup navigation
    setupNavigation();

    // Setup repository analysis
    setupRepoAnalysis();

    // Setup report generation
    setupReportGeneration();

    // Check if we should automatically start analysis
    checkAutoAnalysis();
});

/**
 * Sets up the sidebar navigation functionality
 */
function setupNavigation() {
    // Get all navigation links
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    // Add click event listeners to each link
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Hide all content sections
            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Show the target section
            const targetSection = this.getAttribute('data-section');
            document.getElementById(targetSection).classList.add('active');
        });
    });
}

/**
 * Sets up the repository analysis functionality
 */
function setupRepoAnalysis() {
    // Get the analyze button and modal elements
    const analyzeBtn = document.getElementById('analyze-repo-btn');
    const startAnalysisBtn = document.getElementById('start-analysis-btn');
    
    // Create bootstrap modal instance
    const analysisModal = new bootstrap.Modal(document.getElementById('repo-analysis-modal'));
    
    // Add click event to the analyze button
    analyzeBtn.addEventListener('click', function() {
        analysisModal.show();
    });
    
    // Add click event to start analysis button
    startAnalysisBtn.addEventListener('click', function() {
        // Get the repository URL from the input
        const repoUrl = document.getElementById('repo-url').value.trim();
        
        if (repoUrl) {
            // Hide the modal
            analysisModal.hide();
            
            // Show loading indicator
            showLoading(true);
            
            // Start the analysis
            analyzeRepository(repoUrl);
        }
    });
}

/**
 * Analyzes the repository with the given URL
 * 
 * @param {string} repoUrl - The URL of the repository to analyze
 */
function analyzeRepository(repoUrl) {
    // Create form data for the POST request
    const formData = new FormData();
    formData.append('repo_url', repoUrl);
    
    // Send the analysis request
    fetch('/analyze', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Analysis request failed');
        }
        return response.json();
    })
    .then(data => {
        console.log('Analysis completed:', data);
        
        // Hide loading indicator
        showLoading(false);
        
        // Render the analysis results
        renderAnalysisResults(data);
    })
    .catch(error => {
        console.error('Error during analysis:', error);
        
        // Hide loading indicator
        showLoading(false);
        
        // Show error message
        showError('Failed to analyze repository: ' + error.message);
    });
}

/**
 * Checks if analysis should start automatically
 */
function checkAutoAnalysis() {
    // Get analysis results from server to see if they already exist
    fetch('/analysis_results')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'error') {
                // No existing analysis, do nothing
                console.log('No existing analysis found');
            } else {
                // Render the existing analysis results
                console.log('Found existing analysis results');
                renderAnalysisResults(data);
            }
        })
        .catch(error => {
            console.error('Error checking analysis status:', error);
        });
}

/**
 * Sets up report generation functionality
 */
function setupReportGeneration() {
    // Enhancement report button
    const enhancementReportBtn = document.getElementById('generate-enhancement-report-btn');
    enhancementReportBtn.addEventListener('click', function() {
        generateReport('enhancement_plan');
    });
    
    // Setup guide button
    const setupGuideBtn = document.getElementById('generate-setup-guide-btn');
    setupGuideBtn.addEventListener('click', function() {
        generateReport('setup_guide');
    });
}

/**
 * Generates a report of the specified type
 * 
 * @param {string} reportType - The type of report to generate
 */
function generateReport(reportType) {
    // Create form data for the POST request
    const formData = new FormData();
    formData.append('report_type', reportType);
    
    // Show loading in the appropriate container
    let contentContainer;
    if (reportType === 'enhancement_plan') {
        contentContainer = document.getElementById('enhancement-report-content');
    } else if (reportType === 'setup_guide') {
        contentContainer = document.getElementById('setup-guide-content');
    } else if (reportType === 'code_analysis') {
        contentContainer = document.getElementById('code-analysis-content');
    } else if (reportType === 'architecture') {
        contentContainer = document.getElementById('architecture-content');
    }
    
    if (contentContainer) {
        contentContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Generating report...</p></div>';
    }
    
    // Send the report generation request
    fetch('/generate_report', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Report generation failed');
        }
        return response.json();
    })
    .then(data => {
        console.log('Report generated:', data);
        
        // Display the report content
        if (data.status === 'success' && contentContainer) {
            contentContainer.innerHTML = data.content;
        } else {
            throw new Error(data.message || 'Failed to generate report');
        }
    })
    .catch(error => {
        console.error('Error generating report:', error);
        
        // Show error message in the content container
        if (contentContainer) {
            contentContainer.innerHTML = `<div class="alert alert-danger">Error generating report: ${error.message}</div>`;
        }
    });
}

/**
 * Shows or hides the loading indicator
 * 
 * @param {boolean} show - Whether to show or hide the loading indicator
 */
function showLoading(show) {
    const loadingIndicator = document.getElementById('loading-indicator');
    
    if (show) {
        loadingIndicator.style.display = 'block';
    } else {
        loadingIndicator.style.display = 'none';
    }
}

/**
 * Shows an error message
 * 
 * @param {string} message - The error message to display
 */
function showError(message) {
    // Create error alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at the top of the active content section
    const activeSection = document.querySelector('.content-section.active');
    activeSection.insertBefore(alertDiv, activeSection.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

/**
 * Renders the analysis results on the dashboard
 * 
 * @param {Object} data - The analysis results data
 */
function renderAnalysisResults(data) {
    // Render repository info
    renderRepositoryInfo(data.repository?.repo_info);
    
    // Render technology stack
    renderTechnologyStack(data.repository?.technologies);
    
    // Render code metrics
    renderCodeMetrics(data.repository?.code_metrics);
    
    // Render financial components overview
    renderFinancialComponentsOverview(data.repository?.financial_components);
    
    // Render directory structure
    renderDirectoryStructure(data.repository?.file_structure);
    
    // Render file distribution
    renderFileDistribution(data.repository?.file_structure);
    
    // Render module breakdown
    renderModuleBreakdown(data.repository?.modules);
    
    // Render code complexity
    renderCodeComplexity(data.repository?.code_metrics?.complexity);
    
    // Render architecture diagrams
    renderArchitectureDiagrams(data.architecture);
    
    // Render financial component details
    renderFinancialComponentDetails(data.repository?.financial_components);
    
    // Render financial flow diagram
    renderFinancialFlowDiagram(data.architecture?.financial_flow_diagram);
    
    // Render dependencies
    renderDependencies(data.repository?.dependencies);
    
    // Render dependency chart
    renderDependencyChart(data.dependencies);
    
    // Render execution flow
    renderExecutionFlow(data.code_flow?.execution_flow);
}

/**
 * Renders the repository information
 * 
 * @param {Object} repoInfo - The repository information object
 */
function renderRepositoryInfo(repoInfo) {
    if (!repoInfo) return;
    
    const repoInfoContainer = document.getElementById('repo-info-content');
    
    repoInfoContainer.innerHTML = `
        <div class="repo-info-item">
            <div class="repo-info-label">Repository:</div>
            <div class="repo-info-value"><a href="${repoInfo.url}" target="_blank">${repoInfo.name}</a></div>
        </div>
        <div class="repo-info-item">
            <div class="repo-info-label">Last Commit:</div>
            <div class="repo-info-value">${repoInfo.last_commit?.substring(0, 8)}</div>
        </div>
        <div class="repo-info-item">
            <div class="repo-info-label">Commit Date:</div>
            <div class="repo-info-value">${new Date(repoInfo.commit_date).toLocaleString()}</div>
        </div>
        <div class="repo-info-item">
            <div class="repo-info-label">Branches:</div>
            <div class="repo-info-value">${repoInfo.branches?.join(', ')}</div>
        </div>
    `;
}

/**
 * Renders the technology stack chart
 * 
 * @param {Object} technologies - The technologies object
 */
function renderTechnologyStack(technologies) {
    if (!technologies) return;
    
    const container = document.getElementById('tech-stack-chart-container');
    
    // Clear existing content
    container.innerHTML = '';
    
    // Create a canvas for the chart
    const canvas = document.createElement('canvas');
    canvas.id = 'tech-stack-chart';
    container.appendChild(canvas);
    
    // Prepare data for the chart
    const languages = technologies.languages || {};
    const languageNames = Object.keys(languages);
    const languageCounts = Object.values(languages);
    
    // Create the chart
    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: languageNames,
            datasets: [{
                data: languageCounts,
                backgroundColor: [
                    '#4e73df',
                    '#1cc88a',
                    '#36b9cc',
                    '#f6c23e',
                    '#e74a3b',
                    '#858796',
                    '#5a5c69'
                ],
                hoverBorderColor: "rgba(234, 236, 244, 1)",
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: 'Programming Languages'
                }
            },
            cutout: '60%'
        }
    });
    
    // Add frameworks and technologies section
    const techSection = document.createElement('div');
    techSection.className = 'mt-4';
    techSection.innerHTML = `
        <h6 class="font-weight-bold">Frameworks & Technologies</h6>
        <div class="d-flex flex-wrap mt-2">
            ${renderTechBadges(technologies.frontend || [], 'frontend')}
            ${renderTechBadges(technologies.backend || [], 'backend')}
            ${renderTechBadges(technologies.databases || [], 'database')}
        </div>
    `;
    container.appendChild(techSection);
}

/**
 * Creates HTML for technology badges
 * 
 * @param {Array} techs - Array of technology names
 * @param {string} type - Type of technology (frontend, backend, database)
 * @returns {string} HTML string of technology badges
 */
function renderTechBadges(techs, type) {
    return techs.map(tech => 
        `<span class="technology-badge ${type}">${tech}</span>`
    ).join('');
}

/**
 * Renders the code metrics visualization
 * 
 * @param {Object} metrics - The code metrics object
 */
function renderCodeMetrics(metrics) {
    if (!metrics) return;
    
    const container = document.getElementById('code-metrics-container');
    
    // Create metrics overview
    container.innerHTML = `
        <div class="row text-center">
            <div class="col-md-3">
                <div class="metric-card">
                    <h3>${metrics.total_files}</h3>
                    <p>Total Files</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <h3>${metrics.total_lines.toLocaleString()}</h3>
                    <p>Total Lines</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <h3>${metrics.code_lines.toLocaleString()}</h3>
                    <p>Code Lines</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <h3>${metrics.comment_lines.toLocaleString()}</h3>
                    <p>Comment Lines</p>
                </div>
            </div>
        </div>
        <div class="mt-4">
            <canvas id="code-composition-chart"></canvas>
        </div>
    `;
    
    // Create the code composition chart
    const ctx = document.getElementById('code-composition-chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Code', 'Comments', 'Blank'],
            datasets: [{
                label: 'Lines',
                data: [metrics.code_lines, metrics.comment_lines, metrics.blank_lines],
                backgroundColor: [
                    'rgba(78, 115, 223, 0.8)',
                    'rgba(28, 200, 138, 0.8)',
                    'rgba(54, 185, 204, 0.8)'
                ],
                borderColor: [
                    'rgb(78, 115, 223)',
                    'rgb(28, 200, 138)',
                    'rgb(54, 185, 204)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Lines'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Code Composition'
                }
            }
        }
    });
}

/**
 * Renders an overview of the financial components
 * 
 * @param {Array} components - The financial components array
 */
function renderFinancialComponentsOverview(components) {
    if (!components || !components.length) {
        document.getElementById('financial-components-overview').innerHTML = 
            '<div class="alert alert-info">No financial components detected in the repository.</div>';
        return;
    }
    
    const container = document.getElementById('financial-components-overview');
    
    // Group components by purpose
    const purposeGroups = {};
    components.forEach(component => {
        const purpose = component.purpose || 'unknown';
        if (!purposeGroups[purpose]) {
            purposeGroups[purpose] = [];
        }
        purposeGroups[purpose].push(component);
    });
    
    // Create summary
    container.innerHTML = `
        <div class="mb-4">
            <h6>Found ${components.length} financial components in the codebase</h6>
            <p>These components are categorized by their primary purpose:</p>
        </div>
        <div class="row">
            ${Object.entries(purposeGroups).map(([purpose, comps]) => `
                <div class="col-md-4 mb-3">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">${purpose.charAt(0).toUpperCase() + purpose.slice(1)}</h6>
                            <p class="card-text">${comps.length} components</p>
                            <ul class="list-unstyled">
                                ${comps.slice(0, 3).map(comp => `
                                    <li class="small text-truncate">
                                        <i data-feather="file" class="feather-small"></i>
                                        ${comp.file}
                                    </li>
                                `).join('')}
                                ${comps.length > 3 ? `<li class="small text-muted">And ${comps.length - 3} more...</li>` : ''}
                            </ul>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    // Re-initialize Feather icons
    feather.replace();
}

/**
 * Renders the directory structure
 * 
 * @param {Array} fileStructure - The file structure array
 */
function renderDirectoryStructure(fileStructure) {
    if (!fileStructure || !fileStructure.length) return;
    
    const container = document.getElementById('directory-structure-container');
    
    // Build a tree structure
    const tree = {};
    fileStructure.forEach(item => {
        if (item.type === 'directory') {
            const path = item.path;
            const parts = path.split('/').filter(p => p);
            
            let current = tree;
            parts.forEach(part => {
                if (!current[part]) {
                    current[part] = {};
                }
                current = current[part];
            });
        }
    });
    
    // Function to recursively build the HTML
    function buildTreeHtml(node, path = '') {
        let html = '<ul>';
        
        // Add directories
        Object.keys(node).forEach(dir => {
            const dirPath = path ? `${path}/${dir}` : dir;
            html += `
                <li>
                    <i data-feather="folder" class="feather-small folder-icon"></i>
                    ${dir}
                    ${buildTreeHtml(node[dir], dirPath)}
                </li>
            `;
        });
        
        // Add files for this level
        fileStructure
            .filter(item => item.type === 'file' && path === item.path.substring(0, item.path.lastIndexOf('/')))
            .forEach(file => {
                const fileName = file.path.split('/').pop();
                const sizeStr = formatFileSize(file.size);
                html += `
                    <li>
                        <i data-feather="file-text" class="feather-small file-icon"></i>
                        ${fileName}
                        <span class="file-size">${sizeStr}</span>
                    </li>
                `;
            });
        
        html += '</ul>';
        return html;
    }
    
    // Render the tree
    container.innerHTML = `
        <div class="directory-tree">
            <div class="mb-3">
                <i data-feather="folder" class="feather-small folder-icon"></i>
                <strong>Repository Root</strong>
            </div>
            ${buildTreeHtml(tree)}
        </div>
    `;
    
    // Re-initialize Feather icons
    feather.replace();
}

/**
 * Formats a file size in bytes to a human-readable string
 * 
 * @param {number} bytes - The size in bytes
 * @returns {string} Human-readable size string
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

/**
 * Renders file distribution chart
 * 
 * @param {Array} fileStructure - The file structure array
 */
function renderFileDistribution(fileStructure) {
    if (!fileStructure || !fileStructure.length) return;
    
    const container = document.getElementById('file-distribution-chart-container');
    
    // Count files by extension
    const filesByExt = {};
    fileStructure.forEach(item => {
        if (item.type === 'file') {
            const ext = item.extension || 'no extension';
            if (!filesByExt[ext]) {
                filesByExt[ext] = 0;
            }
            filesByExt[ext]++;
        }
    });
    
    // Sort by count (descending)
    const sortedExts = Object.entries(filesByExt)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10); // Top 10 extensions
    
    // Prepare canvas
    container.innerHTML = '<canvas id="file-distribution-chart"></canvas>';
    
    // Create the chart
    const ctx = document.getElementById('file-distribution-chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedExts.map(([ext]) => ext),
            datasets: [{
                label: 'Number of Files',
                data: sortedExts.map(([, count]) => count),
                backgroundColor: 'rgba(78, 115, 223, 0.8)',
                borderColor: 'rgb(78, 115, 223)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Files'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'File Distribution by Extension'
                }
            }
        }
    });
}

/**
 * Renders module breakdown
 * 
 * @param {Array} modules - The modules array
 */
function renderModuleBreakdown(modules) {
    if (!modules || !modules.length) return;
    
    const container = document.getElementById('module-breakdown-container');
    
    // Group modules by purpose
    const purposeGroups = {};
    modules.forEach(module => {
        const purpose = module.potential_purpose || 'unknown';
        if (!purposeGroups[purpose]) {
            purposeGroups[purpose] = [];
        }
        purposeGroups[purpose].push(module);
    });
    
    // Prepare data for chart
    const purposes = Object.keys(purposeGroups);
    const counts = purposes.map(purpose => purposeGroups[purpose].length);
    
    // Prepare canvas
    container.innerHTML = '<canvas id="module-purpose-chart"></canvas>';
    
    // Create the chart
    const ctx = document.getElementById('module-purpose-chart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: purposes.map(p => p.charAt(0).toUpperCase() + p.slice(1)),
            datasets: [{
                data: counts,
                backgroundColor: [
                    '#4e73df',
                    '#1cc88a',
                    '#36b9cc',
                    '#f6c23e',
                    '#e74a3b',
                    '#858796',
                    '#5a5c69',
                    '#4e4e4e',
                    '#1c1c1c',
                    '#36363b'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Modules by Purpose'
                }
            }
        }
    });
}

/**
 * Renders code complexity information
 * 
 * @param {Object} complexity - The code complexity object
 */
function renderCodeComplexity(complexity) {
    if (!complexity) return;
    
    const container = document.getElementById('code-complexity-container');
    
    // Render complexity overview
    container.innerHTML = `
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="metric-card">
                    <h4>${complexity.average.toFixed(1)}</h4>
                    <p>Average Lines per File</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="metric-card">
                    <h4>${complexity.max}</h4>
                    <p>Maximum Lines in a File</p>
                </div>
            </div>
        </div>
        <div class="mt-4">
            <canvas id="complexity-distribution-chart"></canvas>
        </div>
    `;
    
    // Create the complexity distribution chart
    if (complexity.distribution) {
        const labels = Object.keys(complexity.distribution);
        const data = Object.values(complexity.distribution);
        
        const ctx = document.getElementById('complexity-distribution-chart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Number of Files',
                    data: data,
                    backgroundColor: 'rgba(78, 115, 223, 0.8)',
                    borderColor: 'rgb(78, 115, 223)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Files'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Lines of Code Range'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'File Complexity Distribution'
                    }
                }
            }
        });
    }
}

/**
 * Renders the architecture diagrams
 * 
 * @param {Object} architecture - The architecture object
 */
function renderArchitectureDiagrams(architecture) {
    if (!architecture) return;
    
    // Render system overview
    renderSystemOverview(architecture.system_overview);
    
    // Render component diagram
    renderComponentDiagram(architecture.component_diagram);
    
    // Render layer diagram
    renderLayerDiagram(architecture.layer_diagram);
}

/**
 * Renders the system overview diagram
 * 
 * @param {Object} overview - The system overview object
 */
function renderSystemOverview(overview) {
    if (!overview) return;
    
    const container = document.getElementById('system-overview-container');
    
    // Create SVG container
    container.innerHTML = `
        <div class="architecture-diagram" id="system-overview-diagram"></div>
    `;
    
    // Use D3 to create the diagram
    const width = 800;
    const height = 600;
    
    const svg = d3.select('#system-overview-diagram')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('class', 'architecture-svg');
    
    // Create a title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', 40)
        .attr('text-anchor', 'middle')
        .style('font-size', '20px')
        .style('font-weight', 'bold')
        .text(overview.title);
    
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', 65)
        .attr('text-anchor', 'middle')
        .style('font-size', '14px')
        .text(overview.description);
    
    // Calculate positions for components
    const components = overview.components || [];
    const numComponents = components.length;
    const padding = 50;
    const boxWidth = 180;
    const boxHeight = 120;
    
    const positions = {};
    
    // Position components in a circle or grid
    if (numComponents <= 6) {
        // In a circle
        const radius = Math.min(width, height) / 3;
        const centerX = width / 2;
        const centerY = height / 2;
        
        components.forEach((component, i) => {
            const angle = (i / numComponents) * 2 * Math.PI;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            positions[component.id] = { x, y };
        });
    } else {
        // In a grid
        const cols = Math.ceil(Math.sqrt(numComponents));
        const rows = Math.ceil(numComponents / cols);
        
        const gridWidth = (width - 2 * padding) / cols;
        const gridHeight = (height - 2 * padding - 100) / rows;
        
        components.forEach((component, i) => {
            const row = Math.floor(i / cols);
            const col = i % cols;
            
            const x = padding + col * gridWidth + gridWidth / 2;
            const y = 100 + padding + row * gridHeight + gridHeight / 2;
            
            positions[component.id] = { x, y };
        });
    }
    
    // Draw the connections first (so they're behind components)
    const connections = overview.connections || [];
    
    connections.forEach(connection => {
        const source = positions[connection.source];
        const target = positions[connection.target];
        
        if (source && target) {
            // Draw the line
            svg.append('line')
                .attr('x1', source.x)
                .attr('y1', source.y)
                .attr('x2', target.x)
                .attr('y2', target.y)
                .style('stroke', '#aaa')
                .style('stroke-width', 2);
            
            // Add arrowhead
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            
            svg.append('path')
                .attr('d', 'M 0,-5 L 10,0 L 0,5')
                .attr('transform', `translate(${target.x},${target.y}) rotate(${angle})`)
                .style('fill', '#aaa');
            
            // Add connection label
            const midX = (source.x + target.x) / 2;
            const midY = (source.y + target.y) / 2;
            
            svg.append('text')
                .attr('x', midX)
                .attr('y', midY - 10)
                .attr('text-anchor', 'middle')
                .style('font-size', '12px')
                .style('background', 'white')
                .text(connection.description);
        }
    });
    
    // Draw the components
    components.forEach(component => {
        const pos = positions[component.id];
        
        if (pos) {
            // Draw component box
            const group = svg.append('g')
                .attr('transform', `translate(${pos.x - boxWidth/2}, ${pos.y - boxHeight/2})`);
            
            // Background rounded rectangle
            group.append('rect')
                .attr('width', boxWidth)
                .attr('height', boxHeight)
                .attr('rx', 10)
                .attr('ry', 10)
                .style('fill', '#fff')
                .style('stroke', '#4e73df')
                .style('stroke-width', 2);
            
            // Component title
            group.append('text')
                .attr('x', boxWidth / 2)
                .attr('y', 25)
                .attr('text-anchor', 'middle')
                .style('font-weight', 'bold')
                .style('font-size', '14px')
                .text(component.name);
            
            // Component description
            if (component.description) {
                group.append('text')
                    .attr('x', boxWidth / 2)
                    .attr('y', 45)
                    .attr('text-anchor', 'middle')
                    .style('font-size', '12px')
                    .text(component.description);
            }
            
            // Component technologies or functions
            if (component.technologies || component.functions) {
                const items = component.technologies || component.functions || [];
                
                items.slice(0, 3).forEach((item, i) => {
                    group.append('text')
                        .attr('x', 15)
                        .attr('y', 70 + i * 15)
                        .style('font-size', '11px')
                        .text(`• ${item}`);
                });
                
                if (items.length > 3) {
                    group.append('text')
                        .attr('x', 15)
                        .attr('y', 70 + 3 * 15)
                        .style('font-size', '11px')
                        .text(`• ...${items.length - 3} more`);
                }
            }
        }
    });
}

/**
 * Renders the component diagram
 * 
 * @param {Object} diagram - The component diagram object
 */
function renderComponentDiagram(diagram) {
    if (!diagram) return;
    
    const container = document.getElementById('component-diagram-container');
    
    // Create SVG container
    container.innerHTML = `
        <div class="architecture-diagram" id="component-relationship-diagram"></div>
    `;
    
    // Use D3 to create a force-directed graph
    const width = 800;
    const height = 600;
    
    const svg = d3.select('#component-relationship-diagram')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('class', 'architecture-svg');
    
    // Create a title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', 30)
        .attr('text-anchor', 'middle')
        .style('font-size', '20px')
        .style('font-weight', 'bold')
        .text(diagram.title);
    
    // Convert data to the format D3 force layout expects
    const nodes = diagram.components.map(component => ({
        id: component.id,
        name: component.name,
        purpose: component.purpose,
        files: component.files
    }));
    
    const links = diagram.connections.map(connection => ({
        source: connection.source,
        target: connection.target,
        value: connection.weight || 1,
        description: connection.description
    }));
    
    // Create a force simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(60));
    
    // Draw the links
    const link = svg.append('g')
        .selectAll('line')
        .data(links)
        .enter().append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.value));
    
    // Add link labels
    const linkLabels = svg.append('g')
        .selectAll('text')
        .data(links)
        .enter().append('text')
        .attr('font-size', '10px')
        .attr('text-anchor', 'middle')
        .attr('dy', '-5px')
        .text(d => d.description);
    
    // Draw the nodes
    const node = svg.append('g')
        .selectAll('g')
        .data(nodes)
        .enter().append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add circles for the nodes
    node.append('circle')
        .attr('r', d => Math.max(30, Math.min(50, 20 + d.files / 2)))
        .attr('fill', d => {
            // Color based on purpose
            const purposeColors = {
                'ui': '#4e73df',
                'api': '#1cc88a',
                'database': '#36b9cc',
                'util': '#f6c23e',
                'auth': '#e74a3b',
                'config': '#858796',
                'financial': '#4e4e4e'
            };
            
            return purposeColors[d.purpose] || '#4e73df';
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5);
    
    // Add labels to the nodes
    node.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '.3em')
        .text(d => d.name.substring(0, 10));
    
    // Add tooltips with more details
    node.append('title')
        .text(d => `${d.name}\nPurpose: ${d.purpose}\nFiles: ${d.files}`);
    
    // Update positions on each tick of the simulation
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        linkLabels
            .attr('x', d => (d.source.x + d.target.x) / 2)
            .attr('y', d => (d.source.y + d.target.y) / 2);
        
        node
            .attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

/**
 * Renders the layer diagram
 * 
 * @param {Object} diagram - The layer diagram object
 */
function renderLayerDiagram(diagram) {
    if (!diagram) return;
    
    const container = document.getElementById('layer-diagram-container');
    
    // Create SVG container
    container.innerHTML = `
        <div class="architecture-diagram" id="layer-diagram-svg"></div>
    `;
    
    // Use D3 to create the diagram
    const width = 800;
    const height = 600;
    
    const svg = d3.select('#layer-diagram-svg')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('class', 'architecture-svg');
    
    // Create a title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', 30)
        .attr('text-anchor', 'middle')
        .style('font-size', '20px')
        .style('font-weight', 'bold')
        .text(diagram.title);
    
    // Get layers
    const layers = diagram.layers || [];
    const layerHeight = 100;
    const layerSpacing = 40;
    const totalLayersHeight = layers.length * layerHeight + (layers.length - 1) * layerSpacing;
    const startY = (height - totalLayersHeight) / 2;
    
    // Draw layers
    layers.forEach((layer, i) => {
        const layerY = startY + i * (layerHeight + layerSpacing);
        
        // Layer container
        const layerGroup = svg.append('g')
            .attr('transform', `translate(0, ${layerY})`)
            .attr('class', 'layer');
        
        // Layer background
        layerGroup.append('rect')
            .attr('x', 50)
            .attr('y', 0)
            .attr('width', width - 100)
            .attr('height', layerHeight)
            .attr('rx', 5)
            .attr('ry', 5)
            .attr('fill', '#f8f9fa')
            .attr('stroke', '#4e73df')
            .attr('stroke-width', 2);
        
        // Layer name
        layerGroup.append('text')
            .attr('x', width / 2)
            .attr('y', 25)
            .attr('text-anchor', 'middle')
            .style('font-weight', 'bold')
            .style('font-size', '16px')
            .text(layer.name);
        
        // Layer description
        layerGroup.append('text')
            .attr('x', width / 2)
            .attr('y', 45)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .text(layer.description);
        
        // Layer technologies
        if (layer.technologies && layer.technologies.length) {
            layerGroup.append('text')
                .attr('x', 70)
                .attr('y', 70)
                .style('font-size', '12px')
                .text(`Technologies: ${layer.technologies.join(', ')}`);
        }
        
        // Number of components
        if (layer.components && layer.components.length) {
            layerGroup.append('text')
                .attr('x', width - 70)
                .attr('y', 70)
                .attr('text-anchor', 'end')
                .style('font-size', '12px')
                .text(`${layer.components.length} components`);
        }
        
        // If not the last layer, draw a downward arrow
        if (i < layers.length - 1) {
            svg.append('path')
                .attr('d', `M ${width/2},${layerY + layerHeight + 5} L ${width/2},${layerY + layerHeight + layerSpacing - 5}`)
                .attr('stroke', '#4e73df')
                .attr('stroke-width', 2)
                .attr('marker-end', 'url(#arrowhead)');
                
            // Arrowhead for the line
            svg.append('path')
                .attr('d', 'M 0,-5 L 10,0 L 0,5')
                .attr('transform', `translate(${width/2},${layerY + layerHeight + layerSpacing - 5}) rotate(90)`)
                .style('fill', '#4e73df');
        }
    });
}

/**
 * Renders financial component details
 * 
 * @param {Array} components - The financial components array
 */
function renderFinancialComponentDetails(components) {
    if (!components || !components.length) return;
    
    const container = document.getElementById('financial-component-details');
    
    // Create a table for financial components
    let html = `
        <div class="table-container">
            <table class="analysis-table">
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Purpose</th>
                        <th>Financial Terms</th>
                        <th>Functions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    components.forEach(component => {
        const fileName = component.file.split('/').pop();
        const terms = component.financial_terms || [];
        const functions = component.functions || [];
        
        html += `
            <tr>
                <td><code>${fileName}</code></td>
                <td>${component.purpose || 'Unknown'}</td>
                <td>${terms.slice(0, 5).join(', ')}${terms.length > 5 ? '...' : ''}</td>
                <td>${functions.slice(0, 3).join(', ')}${functions.length > 3 ? '...' : ''}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Renders financial flow diagram
 * 
 * @param {Object} diagram - The financial flow diagram object
 */
function renderFinancialFlowDiagram(diagram) {
    if (!diagram) return;
    
    const container = document.getElementById('financial-flow-diagram-container');
    
    // Create SVG container
    container.innerHTML = `
        <div class="architecture-diagram" id="financial-flow-svg"></div>
    `;
    
    // Use D3 to create a directed graph similar to component diagram but specific to financial flows
    const width = 800;
    const height = 600;
    
    const svg = d3.select('#financial-flow-svg')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('class', 'architecture-svg');
    
    // Create a title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', 30)
        .attr('text-anchor', 'middle')
        .style('font-size', '20px')
        .style('font-weight', 'bold')
        .text(diagram.title);
    
    // Convert data for D3
    const nodes = diagram.components.map(component => ({
        id: component.id,
        name: component.name || component.file.split('/').pop(),
        type: component.type,
        group: component.group,
        terms: component.terms || []
    }));
    
    const links = diagram.flows.map(flow => ({
        source: flow.source,
        target: flow.target,
        description: flow.description,
        bidirectional: flow.bidirectional
    }));
    
    // Create a force simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(60));
    
    // Determine node color based on type/group
    function getNodeColor(node) {
        if (node.type === 'group') {
            return '#f6c23e';
        }
        
        // Colors for component types
        const typeColors = {
            'data': '#36b9cc',
            'analysis': '#1cc88a',
            'report': '#4e73df',
            'input': '#e74a3b'
        };
        
        // Try to infer type from name or terms
        const nodeText = node.name.toLowerCase() + ' ' + node.terms.join(' ').toLowerCase();
        
        for (const [type, color] of Object.entries(typeColors)) {
            if (nodeText.includes(type)) {
                return color;
            }
        }
        
        // Default color
        return '#4e73df';
    }
    
    // Draw links
    const link = svg.append('g')
        .selectAll('line')
        .data(links)
        .enter().append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 2)
        .attr('marker-end', d => d.bidirectional ? null : 'url(#arrowhead)')
        .attr('marker-start', d => d.bidirectional ? 'url(#arrowhead-reverse)' : null);
    
    // Create arrowhead marker
    svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 15)
        .attr('refY', 0)
        .attr('orient', 'auto')
        .attr('markerWidth', 8)
        .attr('markerHeight', 8)
        .attr('xoverflow', 'visible')
        .append('path')
        .attr('d', 'M 0,-5 L 10,0 L 0,5')
        .attr('fill', '#999');
    
    // Add link labels
    const linkLabels = svg.append('g')
        .selectAll('text')
        .data(links)
        .enter().append('text')
        .attr('font-size', '10px')
        .attr('text-anchor', 'middle')
        .attr('dy', '-5px')
        .text(d => d.description);
    
    // Draw nodes
    const node = svg.append('g')
        .selectAll('g')
        .data(nodes)
        .enter().append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add shapes for nodes (rect for groups, circle for components)
    node.each(function(d) {
        const element = d3.select(this);
        
        if (d.type === 'group') {
            element.append('rect')
                .attr('width', 100)
                .attr('height', 50)
                .attr('x', -50)
                .attr('y', -25)
                .attr('rx', 5)
                .attr('ry', 5)
                .attr('fill', getNodeColor(d))
                .attr('stroke', '#fff')
                .attr('stroke-width', 1.5);
        } else {
            element.append('circle')
                .attr('r', 25)
                .attr('fill', getNodeColor(d))
                .attr('stroke', '#fff')
                .attr('stroke-width', 1.5);
        }
        
        // Add text label
        element.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '.3em')
            .attr('fill', '#fff')
            .text(d => d.name.substring(0, 10));
    });
    
    // Add tooltips
    node.append('title')
        .text(d => {
            let tooltip = d.name;
            
            if (d.terms && d.terms.length) {
                tooltip += '\nTerms: ' + d.terms.join(', ');
            }
            
            return tooltip;
        });
    
    // Update positions on each tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        linkLabels
            .attr('x', d => (d.source.x + d.target.x) / 2)
            .attr('y', d => (d.source.y + d.target.y) / 2);
        
        node
            .attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

/**
 * Renders dependencies information
 * 
 * @param {Object} dependencies - The dependencies object
 */
function renderDependencies(dependencies) {
    if (!dependencies) return;
    
    const container = document.getElementById('external-dependencies-container');
    
    // Combine npm and pip dependencies
    const npmDeps = dependencies.npm || [];
    const pipDeps = dependencies.pip || [];
    
    container.innerHTML = `
        <ul class="nav nav-tabs" id="dependencyTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="npm-tab" data-bs-toggle="tab" data-bs-target="#npm-deps" type="button">
                    NPM Dependencies (${npmDeps.length})
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="pip-tab" data-bs-toggle="tab" data-bs-target="#pip-deps" type="button">
                    Python Dependencies (${pipDeps.length})
                </button>
            </li>
        </ul>
        <div class="tab-content pt-3" id="dependencyTabsContent">
            <div class="tab-pane fade show active" id="npm-deps" role="tabpanel">
                ${renderDependencyTable(npmDeps, 'npm')}
            </div>
            <div class="tab-pane fade" id="pip-deps" role="tabpanel">
                ${renderDependencyTable(pipDeps, 'pip')}
            </div>
        </div>
    `;
}

/**
 * Renders a table of dependencies
 * 
 * @param {Array} deps - Array of dependencies
 * @param {string} type - Type of dependencies (npm, pip)
 * @returns {string} HTML for the dependency table
 */
function renderDependencyTable(deps, type) {
    if (!deps || !deps.length) {
        return `<div class="alert alert-info">No ${type} dependencies detected.</div>`;
    }
    
    return `
        <div class="table-container">
            <table class="analysis-table">
                <thead>
                    <tr>
                        <th>Package</th>
                        <th>Version</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    ${deps.map(dep => `
                        <tr>
                            <td>${dep.name}</td>
                            <td>${dep.version || 'Not specified'}</td>
                            <td>${dep.type || 'production'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

/**
 * Renders dependency charts
 * 
 * @param {Object} dependencies - The dependencies charts data
 */
function renderDependencyChart(dependencies) {
    if (!dependencies) return;
    
    const container = document.getElementById('dependency-chart-container');
    
    // Create canvas for chart
    container.innerHTML = '<canvas id="package-dependency-chart"></canvas>';
    
    // Get package dependencies data
    const packageDeps = dependencies.package_dependencies;
    
    if (packageDeps && packageDeps.groups && packageDeps.dependencies) {
        // Prepare data for chart
        const groups = packageDeps.groups;
        const allDeps = packageDeps.dependencies;
        
        // Group data for chart
        const labels = groups.map(g => g.name);
        const data = groups.map(g => g.count);
        
        // Create chart
        const ctx = document.getElementById('package-dependency-chart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#4e73df',
                        '#1cc88a',
                        '#36b9cc',
                        '#f6c23e'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    title: {
                        display: true,
                        text: 'Package Dependencies by Type'
                    }
                },
                cutout: '60%'
            }
        });
    } else {
        container.innerHTML = '<div class="alert alert-info">No dependency data available.</div>';
    }
    
    // Render module dependencies
    const moduleDepsContainer = document.getElementById('module-dependencies-container');
    const moduleDeps = dependencies.module_dependencies;
    
    if (moduleDeps && moduleDeps.nodes && moduleDeps.links && moduleDeps.nodes.length > 0) {
        // Create container for graph
        moduleDepsContainer.innerHTML = `
            <div class="architecture-diagram" id="module-dependencies-graph"></div>
        `;
        
        // Render force-directed graph with D3 (similar to component diagram)
        const width = 800;
        const height = 600;
        
        const svg = d3.select('#module-dependencies-graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', `0 0 ${width} ${height}`)
            .attr('class', 'architecture-svg');
        
        // Create a force simulation
        const simulation = d3.forceSimulation(moduleDeps.nodes)
            .force('link', d3.forceLink(moduleDeps.links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(50));
        
        // Draw links with varying thickness based on weight
        const link = svg.append('g')
            .selectAll('line')
            .data(moduleDeps.links)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.sqrt(d.weight || 1) * 1.5);
        
        // Draw nodes
        const node = svg.append('g')
            .selectAll('g')
            .data(moduleDeps.nodes)
            .enter().append('g')
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
        
        // Node circles
        node.append('circle')
            .attr('r', d => Math.max(20, Math.min(40, 15 + (d.files || 0) / 3)))
            .attr('fill', d => {
                // Color based on purpose
                const purposeColors = {
                    'ui': '#4e73df',
                    'api': '#1cc88a',
                    'database': '#36b9cc',
                    'util': '#f6c23e',
                    'auth': '#e74a3b',
                    'financial': '#4e4e4e',
                    'unknown': '#858796'
                };
                
                return purposeColors[d.purpose] || '#858796';
            })
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5);
        
        // Node labels
        node.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '.3em')
            .attr('fill', '#fff')
            .text(d => d.name.substring(0, 12));
        
        // Tooltips
        node.append('title')
            .text(d => `${d.name}\nFiles: ${d.files || 0}\nPurpose: ${d.purpose || 'Unknown'}`);
        
        // Update positions on each tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node
                .attr('transform', d => `translate(${d.x},${d.y})`);
        });
        
        // Drag functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    } else {
        moduleDepsContainer.innerHTML = '<div class="alert alert-info">No module dependency data available.</div>';
    }
}

/**
 * Renders execution flow diagram
 * 
 * @param {Object} flow - The execution flow object
 */
function renderExecutionFlow(flow) {
    if (!flow) return;
    
    const container = document.getElementById('financial-feature-map-container');
    
    // Create container for the flow diagram
    container.innerHTML = `
        <div class="architecture-diagram" id="execution-flow-diagram"></div>
    `;
    
    // Render Sankey-like diagram with D3
    const width = 800;
    const height = 600;
    
    const svg = d3.select('#execution-flow-diagram')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('class', 'architecture-svg');
    
    // Create a title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', 30)
        .attr('text-anchor', 'middle')
        .style('font-size', '20px')
        .style('font-weight', 'bold')
        .text('Execution Flow Diagram');
    
    // Group nodes by type and purpose
    const modules = flow.modules || [];
    const flows = flow.flows || [];
    const entryPoints = flow.entry_points || [];
    
    // Create a hierarchical structure based on purpose
    const nodesByPurpose = {};
    
    modules.forEach(module => {
        const purpose = module.purpose || 'unknown';
        
        if (!nodesByPurpose[purpose]) {
            nodesByPurpose[purpose] = [];
        }
        
        nodesByPurpose[purpose].push(module);
    });
    
    // Order purposes by typical flow
    const purposeOrder = ['entry_point', 'ui', 'api', 'database', 'util', 'financial', 'unknown'];
    
    // Filter and sort purposes that actually have nodes
    const activePurposes = purposeOrder.filter(purpose => 
        purpose === 'entry_point' && entryPoints.length > 0 || 
        nodesByPurpose[purpose] && nodesByPurpose[purpose].length > 0
    );
    
    // Create columns for each purpose
    const columns = activePurposes.map(purpose => {
        if (purpose === 'entry_point') {
            return {
                purpose: purpose,
                title: 'Entry Points',
                nodes: modules.filter(m => entryPoints.includes(m.id))
            };
        } else {
            return {
                purpose: purpose,
                title: purpose.charAt(0).toUpperCase() + purpose.slice(1),
                nodes: nodesByPurpose[purpose] || []
            };
        }
    });
    
    // Layout variables
    const columnWidth = width / (columns.length + 1);
    const nodeHeight = 40;
    const nodeSpacing = 20;
    
    // Position nodes in columns
    const nodePositions = {};
    
    columns.forEach((column, colIndex) => {
        const columnX = (colIndex + 1) * columnWidth;
        
        // Calculate total height needed for this column
        const columnHeight = column.nodes.length * nodeHeight + (column.nodes.length - 1) * nodeSpacing;
        const startY = (height - columnHeight) / 2;
        
        // Position each node in the column
        column.nodes.forEach((node, nodeIndex) => {
            const nodeY = startY + nodeIndex * (nodeHeight + nodeSpacing);
            
            nodePositions[node.id] = {
                x: columnX,
                y: nodeY,
                width: columnWidth * 0.8,
                height: nodeHeight
            };
        });
        
        // Draw column title
        svg.append('text')
            .attr('x', columnX)
            .attr('y', 70)
            .attr('text-anchor', 'middle')
            .attr('font-weight', 'bold')
            .text(column.title);
    });
    
    // Draw the flows (connections between nodes)
    flows.forEach(flow => {
        const source = nodePositions[flow.source];
        const target = nodePositions[flow.target];
        
        if (source && target) {
            // Draw a curved path from source to target
            const path = d3.path();
            path.moveTo(source.x + source.width / 2, source.y + source.height / 2);
            
            // Use quadratic curve if nodes are in adjacent columns
            path.bezierCurveTo(
                (source.x + target.x) / 2, source.y + source.height / 2,
                (source.x + target.x) / 2, target.y + target.height / 2,
                target.x - target.width / 2, target.y + target.height / 2
            );
            
            svg.append('path')
                .attr('d', path)
                .attr('stroke', '#aaa')
                .attr('stroke-width', 1.5)
                .attr('fill', 'none')
                .attr('marker-end', 'url(#arrow)');
        }
    });
    
    // Create arrow marker
    svg.append('defs').append('marker')
        .attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 5)
        .attr('refY', 0)
        .attr('markerWidth', 4)
        .attr('markerHeight', 4)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#aaa');
    
    // Draw the nodes
    Object.entries(nodePositions).forEach(([nodeId, position]) => {
        const module = modules.find(m => m.id === nodeId);
        
        if (module) {
            const group = svg.append('g')
                .attr('transform', `translate(${position.x - position.width / 2}, ${position.y})`);
            
            // Node background
            group.append('rect')
                .attr('width', position.width)
                .attr('height', position.height)
                .attr('rx', 5)
                .attr('ry', 5)
                .attr('fill', module.type === 'entry_point' ? '#f6c23e' : '#4e73df')
                .attr('stroke', '#fff')
                .attr('stroke-width', 1);
            
            // Node name
            group.append('text')
                .attr('x', position.width / 2)
                .attr('y', position.height / 2)
                .attr('dy', '0.35em')
                .attr('text-anchor', 'middle')
                .attr('fill', '#fff')
                .text(module.name);
                
            // Tooltip
            group.append('title')
                .text(`${module.name}\nType: ${module.type}\nPurpose: ${module.purpose}`);
        }
    });
}
