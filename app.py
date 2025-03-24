from flask import Flask, render_template, request, send_file, jsonify
import os
import sys
import json
import markdown
import logging
from src.analysis_tools.repo_analyzer import analyze_repository
from src.analysis_tools.dependency_chart import generate_dependency_chart
from src.visualization.architecture_visualizer import generate_architecture_diagram
from src.visualization.code_flow import generate_code_flow_diagram

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
REPO_URL = "https://github.com/yashshah5489/updated_college_proj"
ANALYSIS_RESULTS = {}

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('report_template.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Trigger repository analysis and return results."""
    try:
        repo_url = request.form.get('repo_url', REPO_URL)
        logger.info(f"Starting analysis for repository: {repo_url}")
        
        # Analyze repository
        analysis_results = analyze_repository(repo_url)
        
        # Generate architecture diagrams
        arch_diagram = generate_architecture_diagram(analysis_results)
        
        # Generate dependency chart
        dep_chart = generate_dependency_chart(analysis_results)
        
        # Generate code flow diagram
        flow_diagram = generate_code_flow_diagram(analysis_results)
        
        # Store results
        ANALYSIS_RESULTS.update({
            'repository': analysis_results,
            'architecture': arch_diagram,
            'dependencies': dep_chart,
            'code_flow': flow_diagram
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Analysis completed successfully',
            'data': ANALYSIS_RESULTS
        })
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/analysis_results')
def get_analysis_results():
    """Return the current analysis results."""
    if not ANALYSIS_RESULTS:
        return jsonify({
            'status': 'error',
            'message': 'No analysis results available. Run analysis first.'
        }), 404
    return jsonify(ANALYSIS_RESULTS)

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate a markdown report from the analysis results."""
    try:
        report_type = request.form.get('report_type', 'code_analysis')
        
        if not ANALYSIS_RESULTS:
            return jsonify({
                'status': 'error',
                'message': 'No analysis results available. Run analysis first.'
            }), 404
        
        # Generate appropriate report based on type
        if report_type == 'code_analysis':
            with open('code_analysis.md', 'r') as f:
                report_content = f.read()
        elif report_type == 'architecture':
            with open('architecture.md', 'r') as f:
                report_content = f.read()
        elif report_type == 'setup_guide':
            with open('setup_guide.md', 'r') as f:
                report_content = f.read()
        elif report_type == 'enhancement_plan':
            with open('enhancement_plan.md', 'r') as f:
                report_content = f.read()
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unsupported report type: {report_type}'
            }), 400
        
        # Convert markdown to HTML
        html_content = markdown.markdown(report_content)
        
        return jsonify({
            'status': 'success',
            'content': html_content
        })
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate report: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
