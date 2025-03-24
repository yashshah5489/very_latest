import os
import sys
import json
import logging
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)

def generate_code_flow_diagram(analysis_results):
    """
    Generates code flow diagrams based on the repository analysis.
    
    Args:
        analysis_results (dict): The analysis results from repo_analyzer
        
    Returns:
        dict: Formatted code flow diagram data
    """
    logger.info("Generating code flow diagrams")
    
    code_flow_diagrams = {
        'execution_flow': generate_execution_flow(analysis_results),
        'financial_analysis_flow': generate_financial_analysis_flow(analysis_results),
        'data_processing_flow': generate_data_processing_flow(analysis_results)
    }
    
    return code_flow_diagrams

def generate_execution_flow(analysis_results):
    """
    Generates an execution flow diagram showing the main application flow.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: Execution flow diagram data
    """
    modules = analysis_results.get('modules', [])
    dependencies = analysis_results.get('dependencies', {}).get('internal', [])
    
    # Create graph
    G = nx.DiGraph()
    
    # Find entry points (likely main modules or app initialization)
    entry_point_patterns = ['main', 'app', 'index', 'server', 'application']
    entry_points = []
    
    for module in modules:
        module_name = module['name'].lower()
        module_path = module['path']
        
        # Check if module name matches entry point patterns
        if any(pattern in module_name for pattern in entry_point_patterns):
            entry_points.append(module_path)
            G.add_node(module_path, **{
                'name': module['name'],
                'type': 'entry_point',
                'purpose': module.get('potential_purpose', 'unknown')
            })
        else:
            G.add_node(module_path, **{
                'name': module['name'],
                'type': 'module',
                'purpose': module.get('potential_purpose', 'unknown')
            })
    
    # Add dependency edges
    for dep in dependencies:
        source = dep['from']
        target = dep['imports']
        
        if source in G.nodes and target in G.nodes:
            G.add_edge(source, target)
    
    # If no entry points found, use nodes with highest out-degree as entry points
    if not entry_points and G.nodes:
        out_degrees = sorted(G.out_degree, key=lambda x: x[1], reverse=True)
        if out_degrees:
            top_node = out_degrees[0][0]
            entry_points.append(top_node)
            G.nodes[top_node]['type'] = 'entry_point'
    
    # Generate paths from entry points
    execution_paths = []
    
    for entry_point in entry_points:
        # Find all simple paths up to length 10 from the entry point
        for node in G.nodes:
            if node != entry_point:
                try:
                    # Get shortest path
                    if nx.has_path(G, entry_point, node):
                        path = nx.shortest_path(G, entry_point, node)
                        execution_paths.append(path)
                except nx.NetworkXNoPath:
                    continue
    
    # Prepare diagram data
    diagram = {
        'title': 'Execution Flow Diagram',
        'description': 'Main application execution flows',
        'entry_points': entry_points,
        'modules': [],
        'flows': []
    }
    
    # Add modules
    for node in G.nodes:
        diagram['modules'].append({
            'id': node,
            'name': G.nodes[node].get('name', os.path.basename(node)),
            'type': G.nodes[node].get('type', 'module'),
            'purpose': G.nodes[node].get('purpose', 'unknown')
        })
    
    # Add execution flows
    for i, path in enumerate(execution_paths):
        for j in range(len(path) - 1):
            source = path[j]
            target = path[j + 1]
            
            flow = {
                'id': f"flow_{i}_{j}",
                'source': source,
                'target': target,
                'path_id': i
            }
            
            # Check if this flow is already in the diagram
            if not any(f['source'] == source and f['target'] == target for f in diagram['flows']):
                diagram['flows'].append(flow)
    
    return diagram

def generate_financial_analysis_flow(analysis_results):
    """
    Generates a flow diagram specific to financial analysis processes.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: Financial analysis flow diagram data
    """
    financial_components = analysis_results.get('financial_components', [])
    
    if not financial_components:
        return {
            'title': 'Financial Analysis Flow',
            'description': 'No financial components detected',
            'components': [],
            'flows': []
        }
    
    # Create a directed graph for the financial flow
    G = nx.DiGraph()
    
    # Map components to specialized financial roles
    roles = {
        'data_input': ['input', 'import', 'load', 'fetch', 'source', 'provider'],
        'processing': ['process', 'calculate', 'compute', 'transform'],
        'analysis': ['analyze', 'forecast', 'predict', 'estimate', 'model'],
        'reporting': ['report', 'output', 'display', 'visualization', 'chart', 'graph', 'export']
    }
    
    # Assign roles to components
    component_roles = {}
    for i, component in enumerate(financial_components):
        component_id = f"component_{i}"
        component_text = str(component).lower()
        assigned_role = None
        
        # Try to determine role from financial terms and functions
        for role, keywords in roles.items():
            if any(keyword in component_text for keyword in keywords):
                assigned_role = role
                break
        
        # If no role determined, infer from file name
        if not assigned_role:
            file_name = os.path.basename(component['file']).lower()
            for role, keywords in roles.items():
                if any(keyword in file_name for keyword in keywords):
                    assigned_role = role
                    break
        
        # Default to processing if no role assigned
        if not assigned_role:
            assigned_role = 'processing'
        
        component_roles[component_id] = assigned_role
        
        G.add_node(component_id, **{
            'name': os.path.basename(component['file']),
            'file': component['file'],
            'role': assigned_role,
            'terms': component.get('financial_terms', [])
        })
    
    # Add edges based on the natural flow: data_input -> processing -> analysis -> reporting
    role_order = ['data_input', 'processing', 'analysis', 'reporting']
    
    # Group components by role
    role_groups = defaultdict(list)
    for component_id, role in component_roles.items():
        role_groups[role].append(component_id)
    
    # Connect components following the natural flow
    for i in range(len(role_order) - 1):
        current_role = role_order[i]
        next_role = role_order[i + 1]
        
        current_components = role_groups[current_role]
        next_components = role_groups[next_role]
        
        for source in current_components:
            for target in next_components:
                G.add_edge(source, target)
    
    # Add additional connections based on shared financial terms
    for i, component1 in enumerate(financial_components):
        for j, component2 in enumerate(financial_components):
            if i >= j:
                continue
            
            source_id = f"component_{i}"
            target_id = f"component_{j}"
            
            # Skip if already connected
            if G.has_edge(source_id, target_id) or G.has_edge(target_id, source_id):
                continue
            
            # Check for shared financial terms
            terms1 = set(component1.get('financial_terms', []))
            terms2 = set(component2.get('financial_terms', []))
            
            common_terms = terms1 & terms2
            
            if common_terms:
                # Determine direction based on role order
                source_role_idx = role_order.index(component_roles[source_id])
                target_role_idx = role_order.index(component_roles[target_id])
                
                if source_role_idx < target_role_idx:
                    G.add_edge(source_id, target_id, common_terms=list(common_terms))
                else:
                    G.add_edge(target_id, source_id, common_terms=list(common_terms))
    
    # Prepare diagram data
    diagram = {
        'title': 'Financial Analysis Flow',
        'description': 'Data flow for financial analysis processes',
        'components': [],
        'flows': []
    }
    
    # Add components
    for node in G.nodes:
        diagram['components'].append({
            'id': node,
            'name': G.nodes[node].get('name', ''),
            'file': G.nodes[node].get('file', ''),
            'role': G.nodes[node].get('role', 'unknown'),
            'terms': G.nodes[node].get('terms', [])[:3]  # Top 3 terms
        })
    
    # Add flows
    for source, target, data in G.edges(data=True):
        flow = {
            'source': source,
            'target': target,
            'description': 'Data flow'
        }
        
        if 'common_terms' in data:
            flow['shared_terms'] = data['common_terms'][:3]  # Top 3 terms
        
        diagram['flows'].append(flow)
    
    return diagram

def generate_data_processing_flow(analysis_results):
    """
    Generates a diagram showing data processing flows in the application.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: Data processing flow diagram data
    """
    modules = analysis_results.get('modules', [])
    financial_components = analysis_results.get('financial_components', [])
    
    # Create a graph for data processing
    G = nx.DiGraph()
    
    # Identify data processing related modules
    data_modules = []
    for module in modules:
        purpose = module.get('potential_purpose', '').lower()
        module_name = module['name'].lower()
        
        # Check if module is related to data processing
        if (purpose in ['database', 'data', 'model', 'util'] or
                any(term in module_name for term in ['data', 'process', 'model', 'util', 'helper'])):
            data_modules.append(module)
            
            G.add_node(module['path'], **{
                'name': module['name'],
                'type': 'module',
                'purpose': purpose
            })
    
    # Add financial components
    for i, component in enumerate(financial_components):
        component_id = f"financial_{i}"
        G.add_node(component_id, **{
            'name': os.path.basename(component['file']),
            'type': 'financial_component',
            'purpose': component.get('purpose', 'financial_analysis')
        })
    
    # Try to infer data processing relationships
    # 1. Database -> Data Access -> Business Logic -> UI
    # 2. Raw Data -> Processing -> Analysis -> Reporting
    
    # Group nodes by general purpose
    purpose_groups = {
        'data_source': [],
        'processing': [],
        'analysis': [],
        'presentation': []
    }
    
    # Classify modules
    for module in data_modules:
        purpose = module.get('potential_purpose', '').lower()
        module_path = module['path']
        
        if purpose in ['database', 'data']:
            purpose_groups['data_source'].append(module_path)
        elif purpose in ['util', 'helper', 'service']:
            purpose_groups['processing'].append(module_path)
        elif purpose in ['api', 'controller', 'business']:
            purpose_groups['analysis'].append(module_path)
        elif purpose in ['ui', 'view', 'template']:
            purpose_groups['presentation'].append(module_path)
        else:
            # Determine purpose from module name
            module_name = module['name'].lower()
            if any(term in module_name for term in ['data', 'db', 'model', 'repository']):
                purpose_groups['data_source'].append(module_path)
            elif any(term in module_name for term in ['service', 'process', 'util', 'helper']):
                purpose_groups['processing'].append(module_path)
            elif any(term in module_name for term in ['controller', 'api', 'business']):
                purpose_groups['analysis'].append(module_path)
            elif any(term in module_name for term in ['view', 'ui', 'template', 'component']):
                purpose_groups['presentation'].append(module_path)
            else:
                # Default to processing
                purpose_groups['processing'].append(module_path)
    
    # Classify financial components
    for i, component in enumerate(financial_components):
        component_id = f"financial_{i}"
        component_text = str(component).lower()
        
        if any(term in component_text for term in ['input', 'import', 'load', 'fetch', 'source']):
            purpose_groups['data_source'].append(component_id)
        elif any(term in component_text for term in ['process', 'transform', 'calculate', 'compute']):
            purpose_groups['processing'].append(component_id)
        elif any(term in component_text for term in ['analyze', 'forecast', 'predict', 'estimate']):
            purpose_groups['analysis'].append(component_id)
        elif any(term in component_text for term in ['report', 'output', 'display', 'visualization']):
            purpose_groups['presentation'].append(component_id)
        else:
            # Default to analysis for financial components
            purpose_groups['analysis'].append(component_id)
    
    # Connect nodes following the data flow
    flow_order = ['data_source', 'processing', 'analysis', 'presentation']
    
    for i in range(len(flow_order) - 1):
        current_purpose = flow_order[i]
        next_purpose = flow_order[i + 1]
        
        current_nodes = purpose_groups[current_purpose]
        next_nodes = purpose_groups[next_purpose]
        
        for source in current_nodes:
            for target in next_nodes:
                G.add_edge(source, target)
    
    # Prepare diagram data
    diagram = {
        'title': 'Data Processing Flow',
        'description': 'Flow of data through processing pipeline',
        'stages': [],
        'nodes': [],
        'flows': []
    }
    
    # Add stages
    for purpose in flow_order:
        diagram['stages'].append({
            'id': purpose,
            'name': purpose.replace('_', ' ').title(),
            'nodes': purpose_groups[purpose]
        })
    
    # Add nodes
    for node in G.nodes:
        diagram['nodes'].append({
            'id': node,
            'name': G.nodes[node].get('name', ''),
            'type': G.nodes[node].get('type', 'module'),
            'purpose': G.nodes[node].get('purpose', 'unknown')
        })
    
    # Add flows
    for source, target in G.edges:
        diagram['flows'].append({
            'source': source,
            'target': target,
            'description': 'Data flow'
        })
    
    return diagram
