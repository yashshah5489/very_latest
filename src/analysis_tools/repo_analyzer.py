import os
import sys
import json
import re
import requests
import logging
import tempfile
import subprocess
from git import Repo
from collections import defaultdict

logger = logging.getLogger(__name__)

def analyze_repository(repo_url):
    """
    Analyzes a GitHub repository to extract key information about its structure,
    code patterns, dependencies, and functionality.
    
    Args:
        repo_url (str): The GitHub repository URL to analyze
        
    Returns:
        dict: A dictionary containing analysis results
    """
    logger.info(f"Analyzing repository: {repo_url}")
    
    # Results structure
    results = {
        'repo_info': {},
        'file_structure': [],
        'technologies': {},
        'modules': [],
        'dependencies': {},
        'code_metrics': {},
        'financial_components': [],
    }
    
    try:
        # Clone the repository to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Cloning repository to {temp_dir}")
            repo = Repo.clone_from(repo_url, temp_dir)
            results['repo_info'] = {
                'url': repo_url,
                'name': repo_url.split('/')[-1],
                'last_commit': str(repo.head.commit),
                'commit_date': str(repo.head.commit.committed_datetime),
                'branches': [b.name for b in repo.branches]
            }
            
            # Analyze file structure
            results['file_structure'] = _analyze_file_structure(temp_dir)
            
            # Detect technologies used
            results['technologies'] = _detect_technologies(temp_dir, results['file_structure'])
            
            # Find modules and their relationships
            results['modules'] = _identify_modules(temp_dir, results['file_structure'])
            
            # Analyze dependencies
            results['dependencies'] = _analyze_dependencies(temp_dir, results['technologies'])
            
            # Calculate code metrics
            results['code_metrics'] = _calculate_code_metrics(temp_dir)
            
            # Identify financial components
            results['financial_components'] = _identify_financial_components(temp_dir)
            
    except Exception as e:
        logger.error(f"Error analyzing repository: {str(e)}")
        raise
    
    return results

def _analyze_file_structure(repo_path):
    """
    Recursively analyzes the file structure of the repository.
    
    Args:
        repo_path (str): Path to the repository directory
        
    Returns:
        list: A list of dictionaries representing files and directories
    """
    file_structure = []
    
    for root, dirs, files in os.walk(repo_path):
        rel_path = os.path.relpath(root, repo_path)
        if rel_path == '.':
            rel_path = ''
        
        # Skip .git directory
        if '.git' in dirs:
            dirs.remove('.git')
        
        # Add directory entry
        if rel_path:
            file_structure.append({
                'type': 'directory',
                'path': rel_path,
                'name': os.path.basename(rel_path)
            })
        
        # Add file entries
        for file in files:
            file_path = os.path.join(rel_path, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            file_entry = {
                'type': 'file',
                'path': file_path,
                'name': file,
                'extension': file_ext,
                'size': os.path.getsize(os.path.join(repo_path, file_path))
            }
            
            # Determine file type based on extension
            if file_ext in ['.py', '.js', '.html', '.css', '.php', '.java', '.rb']:
                file_entry['category'] = 'code'
            elif file_ext in ['.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
                file_entry['category'] = 'config'
            elif file_ext in ['.md', '.txt', '.pdf', '.doc', '.docx']:
                file_entry['category'] = 'documentation'
            else:
                file_entry['category'] = 'other'
            
            file_structure.append(file_entry)
    
    return file_structure

def _detect_technologies(repo_path, file_structure):
    """
    Detects technologies used in the repository.
    
    Args:
        repo_path (str): Path to the repository directory
        file_structure (list): The file structure data
        
    Returns:
        dict: Dictionary of detected technologies
    """
    technologies = {
        'languages': defaultdict(int),
        'frameworks': [],
        'databases': [],
        'frontend': [],
        'backend': [],
        'build_tools': [],
    }
    
    # Count files by language
    for file_item in file_structure:
        if file_item['type'] == 'file' and file_item['category'] == 'code':
            ext = file_item['extension']
            if ext == '.py':
                technologies['languages']['Python'] += 1
            elif ext == '.js':
                technologies['languages']['JavaScript'] += 1
            elif ext == '.html':
                technologies['languages']['HTML'] += 1
            elif ext == '.css':
                technologies['languages']['CSS'] += 1
            elif ext == '.php':
                technologies['languages']['PHP'] += 1
            elif ext == '.java':
                technologies['languages']['Java'] += 1
            elif ext == '.rb':
                technologies['languages']['Ruby'] += 1
    
    # Check for frameworks and libraries
    framework_patterns = {
        'Django': [r'django', r'settings\.py', r'wsgi\.py', r'asgi\.py'],
        'Flask': [r'flask', r'from flask import', r'app = Flask'],
        'React': [r'react', r'ReactDOM', r'useState', r'import React'],
        'Vue.js': [r'vue', r'createApp', r'new Vue'],
        'Angular': [r'angular', r'ng-app', r'NgModule'],
        'Express': [r'express', r'app = express\(\)', r'require\(\'express\'\)'],
        'Laravel': [r'laravel', r'Illuminate\\'],
        'Bootstrap': [r'bootstrap', r'class="container"', r'class="row"'],
        'jQuery': [r'jquery', r'\$\(', r'jQuery\('],
    }
    
    database_patterns = {
        'MySQL': [r'mysql', r'mysqli', r'CREATE TABLE', r'SELECT.*FROM'],
        'PostgreSQL': [r'postgres', r'psycopg2', r'pg_'],
        'MongoDB': [r'mongo', r'mongoose', r'MongoClient'],
        'SQLite': [r'sqlite', r'sqlite3', r'conn = sqlite3.connect'],
        'Redis': [r'redis', r'Redis\('],
    }
    
    build_tools = {
        'webpack': [r'webpack'],
        'gulp': [r'gulpfile', r'require\(\'gulp\'\)'],
        'grunt': [r'gruntfile', r'require\(\'grunt\'\)'],
        'npm': [r'package\.json'],
        'pip': [r'requirements\.txt', r'setup\.py'],
    }
    
    # Check for specific files indicating frameworks/tools
    for file_item in file_structure:
        if file_item['type'] == 'file':
            file_path = os.path.join(repo_path, file_item['path'])
            
            # Skip large files (>1MB)
            if os.path.getsize(file_path) > 1_000_000:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check for frameworks
                for framework, patterns in framework_patterns.items():
                    if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                        if framework not in technologies['frameworks']:
                            technologies['frameworks'].append(framework)
                
                # Check for databases
                for db, patterns in database_patterns.items():
                    if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                        if db not in technologies['databases']:
                            technologies['databases'].append(db)
                
                # Check for build tools
                for tool, patterns in build_tools.items():
                    if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                        if tool not in technologies['build_tools']:
                            technologies['build_tools'].append(tool)
            except Exception as e:
                logger.debug(f"Error reading file {file_path}: {str(e)}")
    
    # Categorize frontend and backend technologies
    frontend_techs = ['React', 'Vue.js', 'Angular', 'Bootstrap', 'jQuery']
    backend_techs = ['Django', 'Flask', 'Express', 'Laravel']
    
    for tech in technologies['frameworks']:
        if tech in frontend_techs:
            technologies['frontend'].append(tech)
        if tech in backend_techs:
            technologies['backend'].append(tech)
    
    return technologies

def _identify_modules(repo_path, file_structure):
    """
    Identifies modules and their functionality within the repository.
    
    Args:
        repo_path (str): Path to the repository directory
        file_structure (list): The file structure data
        
    Returns:
        list: A list of modules and their details
    """
    modules = []
    
    # Group files by directory to identify modules
    directories = defaultdict(list)
    for file_item in file_structure:
        if file_item['type'] == 'file':
            dir_path = os.path.dirname(file_item['path'])
            directories[dir_path].append(file_item)
    
    # Analyze each potential module (directory)
    for dir_path, files in directories.items():
        if not dir_path:  # Skip root directory
            continue
        
        module = {
            'name': os.path.basename(dir_path),
            'path': dir_path,
            'files': len(files),
            'size': sum(f['size'] for f in files),
            'languages': {},
            'potential_purpose': ''
        }
        
        # Count languages in this module
        for file in files:
            ext = file['extension']
            if ext not in module['languages']:
                module['languages'][ext] = 0
            module['languages'][ext] += 1
        
        # Determine potential purpose of the module
        keywords = {
            'auth': ['auth', 'login', 'register', 'user', 'password'],
            'api': ['api', 'rest', 'endpoint', 'route'],
            'database': ['model', 'schema', 'database', 'db', 'query'],
            'ui': ['component', 'view', 'template', 'style', 'css'],
            'util': ['util', 'helper', 'common', 'lib'],
            'test': ['test', 'spec', 'mock'],
            'config': ['config', 'setting', 'env'],
            'financial': ['finance', 'money', 'transaction', 'payment', 'account', 'balance', 'budget', 'income', 'expense']
        }
        
        purpose_scores = defaultdict(int)
        
        # Check file names and folder structure for clues
        dir_parts = dir_path.lower().split(os.sep)
        for part in dir_parts:
            for purpose, terms in keywords.items():
                if any(term in part for term in terms):
                    purpose_scores[purpose] += 2
        
        for file in files:
            file_name = file['name'].lower()
            for purpose, terms in keywords.items():
                if any(term in file_name for term in terms):
                    purpose_scores[purpose] += 1
        
        # Analyze file contents for more clues
        for file in files:
            if file['category'] == 'code':
                try:
                    file_path = os.path.join(repo_path, file['path'])
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        
                        # Look for imports or includes that indicate purpose
                        for purpose, terms in keywords.items():
                            score = sum(content.count(term) for term in terms)
                            purpose_scores[purpose] += min(score, 5)  # Cap to avoid skew
                except Exception as e:
                    logger.debug(f"Error reading {file_path}: {str(e)}")
        
        # Assign purpose based on highest score
        if purpose_scores:
            module['potential_purpose'] = max(purpose_scores.items(), key=lambda x: x[1])[0]
        
        modules.append(module)
    
    return modules

def _analyze_dependencies(repo_path, technologies):
    """
    Analyzes dependencies used in the project.
    
    Args:
        repo_path (str): Path to the repository directory
        technologies (dict): Detected technologies
        
    Returns:
        dict: Dictionary of dependencies
    """
    dependencies = {
        'npm': [],
        'pip': [],
        'internal': []
    }
    
    # Check for package.json for npm dependencies
    package_json_path = os.path.join(repo_path, 'package.json')
    if os.path.exists(package_json_path):
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                
                # Extract dependencies
                if 'dependencies' in package_data:
                    for dep, version in package_data['dependencies'].items():
                        dependencies['npm'].append({
                            'name': dep,
                            'version': version,
                            'type': 'production'
                        })
                
                # Extract dev dependencies
                if 'devDependencies' in package_data:
                    for dep, version in package_data['devDependencies'].items():
                        dependencies['npm'].append({
                            'name': dep,
                            'version': version,
                            'type': 'development'
                        })
        except Exception as e:
            logger.error(f"Error parsing package.json: {str(e)}")
    
    # Check for requirements.txt for pip dependencies
    requirements_path = os.path.join(repo_path, 'requirements.txt')
    if os.path.exists(requirements_path):
        try:
            with open(requirements_path, 'r') as f:
                requirements = f.readlines()
                
                for req in requirements:
                    req = req.strip()
                    if req and not req.startswith('#'):
                        # Parse requirement (name and version)
                        parts = req.split('==')
                        if len(parts) == 2:
                            name, version = parts
                        else:
                            name = parts[0]
                            version = None
                        
                        dependencies['pip'].append({
                            'name': name,
                            'version': version,
                            'type': 'production'
                        })
        except Exception as e:
            logger.error(f"Error parsing requirements.txt: {str(e)}")
    
    # Analyze imports in Python files to find internal dependencies
    if 'Python' in technologies['languages']:
        import_graph = defaultdict(set)
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    module_path = os.path.relpath(file_path, repo_path).replace('\\', '/').replace('.py', '')
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Find import statements
                            import_patterns = [
                                r'^\s*import\s+([a-zA-Z0-9_.]+)',
                                r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import',
                            ]
                            
                            for pattern in import_patterns:
                                for match in re.finditer(pattern, content, re.MULTILINE):
                                    imported_module = match.group(1)
                                    
                                    # Only keep internal imports
                                    if not imported_module.startswith(('os', 'sys', 're', 'json', 'time', 'datetime', 'collections')):
                                        import_graph[module_path].add(imported_module)
                    except Exception as e:
                        logger.debug(f"Error analyzing imports in {file_path}: {str(e)}")
        
        # Convert import graph to list of dependencies
        for module, imports in import_graph.items():
            for imported in imports:
                dependencies['internal'].append({
                    'from': module,
                    'imports': imported
                })
    
    return dependencies

def _calculate_code_metrics(repo_path):
    """
    Calculates various code metrics for the repository.
    
    Args:
        repo_path (str): Path to the repository directory
        
    Returns:
        dict: Dictionary of code metrics
    """
    metrics = {
        'total_files': 0,
        'total_lines': 0,
        'code_lines': 0,
        'comment_lines': 0,
        'blank_lines': 0,
        'files_by_type': defaultdict(int),
        'complexity': {
            'average': 0,
            'max': 0,
            'distribution': {}
        }
    }
    
    line_counts = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)
            
            # Skip binary files and non-text files
            if ext.lower() in ['.pyc', '.so', '.dll', '.exe', '.bin', '.jpg', '.png', '.gif']:
                continue
            
            metrics['total_files'] += 1
            metrics['files_by_type'][ext] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    file_lines = len(lines)
                    file_blank = sum(1 for line in lines if not line.strip())
                    
                    # Count comment lines based on file type
                    file_comments = 0
                    if ext.lower() in ['.py']:
                        file_comments = sum(1 for line in lines if line.strip().startswith('#'))
                    elif ext.lower() in ['.js', '.java', '.c', '.cpp', '.cs']:
                        file_comments = sum(1 for line in lines if line.strip().startswith('//'))
                    elif ext.lower() in ['.html', '.xml']:
                        file_comments = sum(1 for line in lines if line.strip().startswith('<!--'))
                    
                    file_code = file_lines - file_blank - file_comments
                    
                    metrics['total_lines'] += file_lines
                    metrics['blank_lines'] += file_blank
                    metrics['comment_lines'] += file_comments
                    metrics['code_lines'] += file_code
                    
                    line_counts.append(file_code)
            except Exception as e:
                logger.debug(f"Error analyzing file {file_path}: {str(e)}")
    
    # Calculate complexity distribution
    if line_counts:
        metrics['complexity']['average'] = sum(line_counts) / len(line_counts)
        metrics['complexity']['max'] = max(line_counts)
        
        # Categorize files by complexity (lines of code)
        complexity_ranges = [(0, 50), (51, 100), (101, 200), (201, 500), (501, float('inf'))]
        
        for low, high in complexity_ranges:
            count = sum(1 for lc in line_counts if low <= lc <= high)
            metrics['complexity']['distribution'][f"{low}-{high if high != float('inf') else 'inf'}"] = count
    
    return metrics

def _identify_financial_components(repo_path):
    """
    Identifies financial analysis components in the codebase.
    
    Args:
        repo_path (str): Path to the repository directory
        
    Returns:
        list: A list of identified financial components
    """
    financial_components = []
    
    # Financial keywords to look for
    financial_terms = [
        'finance', 'financial', 'budget', 'accounting', 'transaction',
        'payment', 'income', 'expense', 'balance', 'asset', 'liability',
        'equity', 'profit', 'loss', 'revenue', 'cost', 'investment',
        'portfolio', 'stock', 'bond', 'fund', 'dividend', 'interest',
        'loan', 'credit', 'debit', 'tax', 'cash flow', 'analyze', 'forecast',
        'report', 'statement', 'ledger', 'journal', 'account', 'ratio',
        'benchmark', 'roi', 'irr', 'npv', 'depreciation', 'amortization'
    ]
    
    # Financial data processing functions
    financial_functions = [
        'calculate', 'compute', 'analyze', 'process', 'report',
        'summarize', 'forecast', 'predict', 'project', 'estimate',
        'chart', 'plot', 'graph', 'visualize', 'compare'
    ]
    
    # Iterate through code files to find financial components
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)
            
            # Skip non-code files
            if ext.lower() not in ['.py', '.js', '.html', '.css', '.php', '.java']:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    # Look for financial terms and functions
                    financial_term_matches = []
                    for term in financial_terms:
                        matches = re.finditer(r'\b' + re.escape(term) + r'\b', content, re.IGNORECASE)
                        financial_term_matches.extend([(term, m.start()) for m in matches])
                    
                    function_matches = []
                    for func in financial_functions:
                        for term in financial_terms:
                            pattern = r'\b' + re.escape(func) + r'\w*\s*\(.*' + re.escape(term)
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            function_matches.extend([(f"{func} {term}", m.start()) for m in matches])
                    
                    # If we have matches, consider this a financial component
                    if financial_term_matches or function_matches:
                        # Get class/function definitions near the matches
                        if ext.lower() == '.py':
                            class_pattern = r'class\s+([A-Za-z0-9_]+)'
                            func_pattern = r'def\s+([A-Za-z0-9_]+)'
                        elif ext.lower() in ['.js', '.java']:
                            class_pattern = r'class\s+([A-Za-z0-9_]+)'
                            func_pattern = r'function\s+([A-Za-z0-9_]+)'
                        else:
                            class_pattern = None
                            func_pattern = None
                        
                        classes = []
                        functions = []
                        
                        if class_pattern:
                            classes = [match.group(1) for match in re.finditer(class_pattern, content)]
                        
                        if func_pattern:
                            functions = [match.group(1) for match in re.finditer(func_pattern, content)]
                        
                        component = {
                            'file': rel_path,
                            'extension': ext,
                            'financial_terms': [term for term, _ in financial_term_matches],
                            'financial_functions': [func for func, _ in function_matches],
                            'classes': classes,
                            'functions': functions,
                            'purpose': 'unknown'
                        }
                        
                        # Try to determine component purpose
                        term_counts = defaultdict(int)
                        for term, _ in financial_term_matches:
                            term_counts[term] += 1
                        
                        # If any term appears more than others, use it for purpose
                        if term_counts:
                            primary_term = max(term_counts.items(), key=lambda x: x[1])[0]
                            component['purpose'] = f"{primary_term} analysis"
                        
                        financial_components.append(component)
            except Exception as e:
                logger.debug(f"Error analyzing file for financial components {file_path}: {str(e)}")
    
    return financial_components
