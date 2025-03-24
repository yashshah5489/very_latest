import os
import sys
import json
import logging
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)

def generate_dependency_chart(analysis_results):
    """
    Generates dependency charts based on the repository analysis.
    
    Args:
        analysis_results (dict): The analysis results from repo_analyzer
        
    Returns:
        dict: Formatted dependency charts data
    """
    logger.info("Generating dependency charts")
    
    dependency_charts = {
        'module_dependencies': generate_module_dependency_chart(analysis_results),
        'package_dependencies': generate_package_dependency_chart(analysis_results),
        'financial_component_dependencies': generate_financial_component_dependency_chart(analysis_results)
    }
    
    return dependency_charts

def generate_module_dependency_chart(analysis_results):
    """
    Generates a dependency chart showing relationships between modules.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: Module dependency data in a chart-friendly format
    """
    modules = analysis_results.get('modules', [])
    internal_dependencies = analysis_results.get('dependencies', {}).get('internal', [])
    
    # Create a graph
    G = nx.DiGraph()
    
    # Add nodes (modules)
    module_paths = set()
    for module in modules:
        module_path = module['path']
        module_paths.add(module_path)
        G.add_node(module_path, **{
            'name': module['name'],
            'files': module['files'],
            'size': module['size'],
            'purpose': module.get('potential_purpose', 'unknown')
        })
    
    # Add edges (dependencies)
    for dep in internal_dependencies:
        source = dep['from']
        target = dep['imports']
        
        # Handle relative imports
        if '.' in target:
            parts = target.split('.')
            if len(parts) > 1:
                # Try to match to an existing module
                potential_module = None
                for module_path in module_paths:
                    if parts[0] in module_path:
                        potential_module = module_path
                        break
                
                if potential_module:
                    target = potential_module
        
        # Only add edge if both nodes exist
        if G.has_node(source) and G.has_node(target):
            if G.has_edge(source, target):
                # Increment weight of existing edge
                G[source][target]['weight'] += 1
            else:
                # Add new edge with weight 1
                G.add_edge(source, target, weight=1)
    
    # Convert graph to chart data
    chart_data = {
        'nodes': [],
        'links': []
    }
    
    for node in G.nodes():
        chart_data['nodes'].append({
            'id': node,
            'name': G.nodes[node].get('name', os.path.basename(node)),
            'files': G.nodes[node].get('files', 0),
            'size': G.nodes[node].get('size', 0),
            'purpose': G.nodes[node].get('purpose', 'unknown')
        })
    
    for source, target, data in G.edges(data=True):
        chart_data['links'].append({
            'source': source,
            'target': target,
            'weight': data.get('weight', 1)
        })
    
    return chart_data

def generate_package_dependency_chart(analysis_results):
    """
    Generates a chart of external package dependencies.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: Package dependency data in a chart-friendly format
    """
    npm_dependencies = analysis_results.get('dependencies', {}).get('npm', [])
    pip_dependencies = analysis_results.get('dependencies', {}).get('pip', [])
    
    # Combine dependencies
    all_dependencies = []
    for dep in npm_dependencies:
        all_dependencies.append({
            'name': dep['name'],
            'version': dep['version'],
            'type': dep['type'],
            'ecosystem': 'npm'
        })
    
    for dep in pip_dependencies:
        all_dependencies.append({
            'name': dep['name'],
            'version': dep['version'],
            'type': dep['type'],
            'ecosystem': 'pip'
        })
    
    # Group dependencies by type and ecosystem
    grouped_deps = defaultdict(list)
    for dep in all_dependencies:
        key = f"{dep['ecosystem']}-{dep['type']}"
        grouped_deps[key].append(dep)
    
    # Format for chart display
    chart_data = {
        'groups': [],
        'dependencies': []
    }
    
    for group_key, deps in grouped_deps.items():
        ecosystem, dep_type = group_key.split('-')
        
        group = {
            'id': group_key,
            'name': f"{ecosystem} {dep_type}",
            'count': len(deps)
        }
        
        chart_data['groups'].append(group)
        
        for dep in deps:
            chart_data['dependencies'].append({
                'name': dep['name'],
                'version': dep['version'],
                'group': group_key
            })
    
    return chart_data

def generate_financial_component_dependency_chart(analysis_results):
    """
    Generates a dependency chart specifically for financial components.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: Financial component dependency data in a chart-friendly format
    """
    financial_components = analysis_results.get('financial_components', [])
    
    # Create a graph
    G = nx.DiGraph()
    
    # Add nodes (financial components)
    for i, component in enumerate(financial_components):
        node_id = f"component_{i}"
        G.add_node(node_id, **{
            'file': component['file'],
            'purpose': component.get('purpose', 'unknown'),
            'terms': component.get('financial_terms', []),
            'functions': component.get('functions', [])
        })
    
    # Try to infer relationships between components
    for i, component1 in enumerate(financial_components):
        for j, component2 in enumerate(financial_components):
            if i == j:
                continue
            
            source_id = f"component_{i}"
            target_id = f"component_{j}"
            
            # Check for shared financial terms
            common_terms = set(component1.get('financial_terms', [])) & set(component2.get('financial_terms', []))
            
            # Check for potentially related functions
            related_functions = False
            for func1 in component1.get('functions', []):
                for func2 in component2.get('functions', []):
                    if func1.lower() in func2.lower() or func2.lower() in func1.lower():
                        related_functions = True
                        break
            
            # Add edge if components appear related
            if common_terms or related_functions:
                G.add_edge(source_id, target_id, weight=len(common_terms) + (1 if related_functions else 0))
    
    # Convert graph to chart data
    chart_data = {
        'nodes': [],
        'links': []
    }
    
    for node in G.nodes():
        chart_data['nodes'].append({
            'id': node,
            'file': G.nodes[node].get('file', ''),
            'purpose': G.nodes[node].get('purpose', 'unknown'),
            'terms': G.nodes[node].get('terms', [])
        })
    
    for source, target, data in G.edges(data=True):
        chart_data['links'].append({
            'source': source,
            'target': target,
            'weight': data.get('weight', 1)
        })
    
    return chart_data
