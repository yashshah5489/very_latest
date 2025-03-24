import os
import sys
import json
import logging
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)

def generate_architecture_diagram(analysis_results):
    """
    Generates architecture diagrams based on the repository analysis.
    
    Args:
        analysis_results (dict): The analysis results from repo_analyzer
        
    Returns:
        dict: Formatted architecture diagram data
    """
    logger.info("Generating architecture diagrams")
    
    architecture_diagrams = {
        'system_overview': generate_system_overview(analysis_results),
        'component_diagram': generate_component_diagram(analysis_results),
        'layer_diagram': generate_layer_diagram(analysis_results),
        'financial_flow_diagram': generate_financial_flow_diagram(analysis_results)
    }
    
    return architecture_diagrams

def generate_system_overview(analysis_results):
    """
    Generates a high-level system overview diagram.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: System overview diagram data
    """
    technologies = analysis_results.get('technologies', {})
    modules = analysis_results.get('modules', [])
    financial_components = analysis_results.get('financial_components', [])
    
    # Create a high-level system diagram
    diagram = {
        'title': 'System Overview',
        'description': 'High-level overview of the system architecture',
        'components': [],
        'connections': []
    }
    
    # Add frontend components
    if technologies.get('frontend'):
        frontend_component = {
            'id': 'frontend',
            'name': 'Frontend',
            'type': 'container',
            'technologies': technologies.get('frontend', []),
            'description': 'User interface and client-side logic'
        }
        diagram['components'].append(frontend_component)
    
    # Add backend components
    if technologies.get('backend'):
        backend_component = {
            'id': 'backend',
            'name': 'Backend',
            'type': 'container',
            'technologies': technologies.get('backend', []),
            'description': 'Server-side application logic'
        }
        diagram['components'].append(backend_component)
    
    # Add database components
    if technologies.get('databases'):
        db_component = {
            'id': 'database',
            'name': 'Database',
            'type': 'container',
            'technologies': technologies.get('databases', []),
            'description': 'Data persistence layer'
        }
        diagram['components'].append(db_component)
    
    # Add financial analysis component if relevant
    if financial_components:
        financial_component = {
            'id': 'financial_analysis',
            'name': 'Financial Analysis',
            'type': 'container',
            'description': 'Financial data processing and analysis',
            'functions': list(set([fc.get('purpose', 'analysis') for fc in financial_components]))[:5]  # Top 5 purposes
        }
        diagram['components'].append(financial_component)
    
    # Add connections between components
    if 'frontend' in [c['id'] for c in diagram['components']] and 'backend' in [c['id'] for c in diagram['components']]:
        diagram['connections'].append({
            'source': 'frontend',
            'target': 'backend',
            'description': 'HTTP/API Requests'
        })
    
    if 'backend' in [c['id'] for c in diagram['components']] and 'database' in [c['id'] for c in diagram['components']]:
        diagram['connections'].append({
            'source': 'backend',
            'target': 'database',
            'description': 'Data Storage/Retrieval'
        })
    
    if 'backend' in [c['id'] for c in diagram['components']] and 'financial_analysis' in [c['id'] for c in diagram['components']]:
        diagram['connections'].append({
            'source': 'backend',
            'target': 'financial_analysis',
            'description': 'Financial Data Processing'
        })
    
    if 'financial_analysis' in [c['id'] for c in diagram['components']] and 'database' in [c['id'] for c in diagram['components']]:
        diagram['connections'].append({
            'source': 'financial_analysis',
            'target': 'database',
            'description': 'Financial Data Storage/Retrieval'
        })
    
    return diagram

def generate_component_diagram(analysis_results):
    """
    Generates a detailed component diagram showing relationships between modules.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: Component diagram data
    """
    modules = analysis_results.get('modules', [])
    internal_dependencies = analysis_results.get('dependencies', {}).get('internal', [])
    
    # Create graph for component dependencies
    G = nx.DiGraph()
    
    # Add nodes for modules
    for module in modules:
        G.add_node(module['path'], **{
            'name': module['name'],
            'purpose': module.get('potential_purpose', 'unknown'),
            'files': module['files']
        })
    
    # Add edges for dependencies
    for dep in internal_dependencies:
        source = dep['from']
        target = dep['imports']
        
        # Handle relative imports
        if source in G.nodes and target in G.nodes:
            if G.has_edge(source, target):
                G[source][target]['weight'] += 1
            else:
                G.add_edge(source, target, weight=1)
    
    # Prepare diagram data
    diagram = {
        'title': 'Component Diagram',
        'description': 'Detailed view of system components and their relationships',
        'components': [],
        'connections': []
    }
    
    # Add components from graph nodes
    for node in G.nodes():
        component = {
            'id': node,
            'name': G.nodes[node].get('name', os.path.basename(node)),
            'purpose': G.nodes[node].get('purpose', 'unknown'),
            'files': G.nodes[node].get('files', 0)
        }
        diagram['components'].append(component)
    
    # Add connections from graph edges
    for source, target, data in G.edges(data=True):
        connection = {
            'source': source,
            'target': target,
            'weight': data.get('weight', 1),
            'description': f"Uses {data.get('weight', 1)} times"
        }
        diagram['connections'].append(connection)
    
    return diagram

def generate_layer_diagram(analysis_results):
    """
    Generates a layered architecture diagram.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: Layer diagram data
    """
    modules = analysis_results.get('modules', [])
    technologies = analysis_results.get('technologies', {})
    
    # Define layers
    layers = {
        'presentation': {
            'name': 'Presentation Layer',
            'description': 'User interface components',
            'components': []
        },
        'business': {
            'name': 'Business Logic Layer',
            'description': 'Application business logic',
            'components': []
        },
        'data': {
            'name': 'Data Access Layer',
            'description': 'Data persistence and retrieval',
            'components': []
        },
        'util': {
            'name': 'Utility Layer',
            'description': 'Common utilities and helpers',
            'components': []
        }
    }
    
    # Assign modules to layers based on purpose
    for module in modules:
        purpose = module.get('potential_purpose', '').lower()
        
        if purpose in ['ui', 'view', 'template', 'component']:
            layers['presentation']['components'].append({
                'id': module['path'],
                'name': module['name'],
                'files': module['files']
            })
        elif purpose in ['api', 'service', 'controller', 'financial']:
            layers['business']['components'].append({
                'id': module['path'],
                'name': module['name'],
                'files': module['files']
            })
        elif purpose in ['database', 'model', 'repository', 'dao']:
            layers['data']['components'].append({
                'id': module['path'],
                'name': module['name'],
                'files': module['files']
            })
        elif purpose in ['util', 'helper', 'common', 'lib', 'config']:
            layers['util']['components'].append({
                'id': module['path'],
                'name': module['name'],
                'files': module['files']
            })
        else:
            # If purpose not clear, try to infer from module name
            module_name = module['name'].lower()
            
            if any(term in module_name for term in ['ui', 'view', 'template', 'component']):
                layers['presentation']['components'].append({
                    'id': module['path'],
                    'name': module['name'],
                    'files': module['files']
                })
            elif any(term in module_name for term in ['api', 'service', 'controller']):
                layers['business']['components'].append({
                    'id': module['path'],
                    'name': module['name'],
                    'files': module['files']
                })
            elif any(term in module_name for term in ['database', 'model', 'repository', 'dao']):
                layers['data']['components'].append({
                    'id': module['path'],
                    'name': module['name'],
                    'files': module['files']
                })
            elif any(term in module_name for term in ['util', 'helper', 'common', 'lib', 'config']):
                layers['util']['components'].append({
                    'id': module['path'],
                    'name': module['name'],
                    'files': module['files']
                })
            else:
                # Default to business logic if unknown
                layers['business']['components'].append({
                    'id': module['path'],
                    'name': module['name'],
                    'files': module['files']
                })
    
    # Add technologies to layers
    if technologies.get('frontend'):
        layers['presentation']['technologies'] = technologies.get('frontend', [])
    
    if technologies.get('backend'):
        layers['business']['technologies'] = technologies.get('backend', [])
    
    if technologies.get('databases'):
        layers['data']['technologies'] = technologies.get('databases', [])
    
    # Format as diagram
    diagram = {
        'title': 'Layer Diagram',
        'description': 'System architecture organized by layers',
        'layers': []
    }
    
    # Add non-empty layers to diagram
    for layer_id, layer in layers.items():
        if layer['components']:
            diagram['layers'].append({
                'id': layer_id,
                'name': layer['name'],
                'description': layer['description'],
                'technologies': layer.get('technologies', []),
                'components': layer['components']
            })
    
    return diagram

def generate_financial_flow_diagram(analysis_results):
    """
    Generates a financial data flow diagram.
    
    Args:
        analysis_results (dict): The analysis results
        
    Returns:
        dict: Financial flow diagram data
    """
    financial_components = analysis_results.get('financial_components', [])
    
    if not financial_components:
        return {
            'title': 'Financial Flow Diagram',
            'description': 'No financial components detected',
            'components': [],
            'flows': []
        }
    
    # Group components by purpose
    purpose_groups = defaultdict(list)
    for component in financial_components:
        purpose = component.get('purpose', 'unknown')
        purpose_groups[purpose].append(component)
    
    # Create diagram
    diagram = {
        'title': 'Financial Flow Diagram',
        'description': 'Data flow between financial components',
        'components': [],
        'flows': []
    }
    
    # Add grouped components
    group_ids = {}
    for i, (purpose, components) in enumerate(purpose_groups.items()):
        group_id = f"group_{i}"
        group_ids[purpose] = group_id
        
        diagram['components'].append({
            'id': group_id,
            'name': purpose.capitalize(),
            'type': 'group',
            'description': f"{purpose.capitalize()} components",
            'size': len(components),
            'files': [c['file'] for c in components]
        })
    
    # Add individual components in each group
    for i, component in enumerate(financial_components):
        purpose = component.get('purpose', 'unknown')
        group_id = group_ids.get(purpose)
        
        diagram['components'].append({
            'id': f"component_{i}",
            'name': os.path.basename(component['file']),
            'type': 'component',
            'group': group_id,
            'file': component['file'],
            'terms': component.get('financial_terms', [])[:3]  # Top 3 terms
        })
    
    # Infer flow between components based on financial terms
    for i, component1 in enumerate(financial_components):
        for j, component2 in enumerate(financial_components):
            if i >= j:  # Avoid self-connections and duplicates
                continue
            
            # Compare financial terms
            terms1 = set(component1.get('financial_terms', []))
            terms2 = set(component2.get('financial_terms', []))
            
            # Check for data flow relationship
            common_terms = terms1 & terms2
            if common_terms:
                # Check if one component could be input for the other
                input_terms = ['input', 'data', 'source', 'raw', 'fetch']
                output_terms = ['output', 'result', 'report', 'analyze', 'visualization']
                
                is_1_input = any(term in str(component1).lower() for term in input_terms)
                is_2_output = any(term in str(component2).lower() for term in output_terms)
                
                is_2_input = any(term in str(component2).lower() for term in input_terms)
                is_1_output = any(term in str(component1).lower() for term in output_terms)
                
                # Determine flow direction
                if (is_1_input and is_2_output) or component1.get('purpose', '') == 'data' and component2.get('purpose', '') == 'analysis':
                    diagram['flows'].append({
                        'source': f"component_{i}",
                        'target': f"component_{j}",
                        'description': f"Shared terms: {', '.join(list(common_terms)[:3])}"
                    })
                elif (is_2_input and is_1_output) or component2.get('purpose', '') == 'data' and component1.get('purpose', '') == 'analysis':
                    diagram['flows'].append({
                        'source': f"component_{j}",
                        'target': f"component_{i}",
                        'description': f"Shared terms: {', '.join(list(common_terms)[:3])}"
                    })
                else:
                    # If direction not clear, add bidirectional flow
                    diagram['flows'].append({
                        'source': f"component_{i}",
                        'target': f"component_{j}",
                        'description': f"Potential data exchange",
                        'bidirectional': True
                    })
    
    return diagram
