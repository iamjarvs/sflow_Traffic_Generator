import logging
from flask import Flask, request, jsonify
from ansible.playbook.play_context import PlayContext
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
import os
import threading
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ansible_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Store running playbooks and their status
playbook_runs = {}

def run_playbook(run_id):
    params = playbook_runs[run_id]['params']
    logger.info(f"Starting playbook execution - Run ID: {run_id}")
    logger.info(f"Parameters: {params}")
    
    playbook_path = params['playbook_path']
    inventory_path = params['inventory_path']
    
    try:
        loader = DataLoader()
        inventory = InventoryManager(loader=loader, sources=inventory_path)
        variable_manager = VariableManager(loader=loader, inventory=inventory)
    
    playbook_executor = PlaybookExecutor(
        playbooks=[playbook_path],
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={}
    )
    
    try:
        playbook_runs[run_id]['status'] = 'running'
        logger.info(f"Executing playbook - Run ID: {run_id}")
        result = playbook_executor.run()
        playbook_runs[run_id]['status'] = 'completed'
        playbook_runs[run_id]['result'] = result
        logger.info(f"Playbook completed successfully - Run ID: {run_id}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Playbook execution failed - Run ID: {run_id}")
        logger.error(f"Error: {error_msg}")
        playbook_runs[run_id]['status'] = 'failed'
        playbook_runs[run_id]['error'] = error_msg
    except:
        logger.error(f"Unexpected error in playbook execution - Run ID: {run_id}", exc_info=True)
        playbook_runs[run_id]['status'] = 'failed'
        playbook_runs[run_id]['error'] = 'Unexpected error occurred'

@app.route('/playbook/run', methods=['POST'])
def start_playbook():
    logger.info("Received playbook execution request")
    try:
        data = request.json
    
    if not data:
        logger.error("Empty request payload")
        return jsonify({'error': 'Empty request payload'}), 400

    # Only validate the minimum required parameters
    if 'playbook_path' not in data:
        logger.error("Missing playbook_path in request")
        return jsonify({'error': 'playbook_path is required'}), 400
    
    if 'inventory_path' not in data:
        logger.error("Missing inventory_path in request")
        return jsonify({'error': 'inventory_path is required'}), 400

    # Store all payload data for use in playbook execution
    run_id = str(int(time.time()))
    playbook_runs[run_id] = {
        'status': 'starting',
        'start_time': time.time(),
        'params': data  # Store the entire payload
    }
    
    if not os.path.exists(playbook_path):
        return jsonify({'error': 'Playbook file not found'}), 404
    
    if not os.path.exists(inventory_path):
        return jsonify({'error': 'Inventory file not found'}), 404
    
    run_id = str(int(time.time()))
    playbook_runs[run_id] = {
        'status': 'starting',
        'playbook': playbook_path,
        'inventory': inventory_path,
        'start_time': time.time()
    }
    
    thread = threading.Thread(
        target=run_playbook,
        args=(playbook_path, inventory_path, run_id)
    )
    thread.start()
    
    return jsonify({
        'run_id': run_id,
        'status': 'starting'
    })

@app.route('/playbook/status/<run_id>', methods=['GET'])
def get_status(run_id):
    if run_id not in playbook_runs:
        return jsonify({'error': 'Run ID not found'}), 404
    
    return jsonify(playbook_runs[run_id])

@app.route('/playbook/list', methods=['GET'])
def list_runs():
    return jsonify(playbook_runs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
