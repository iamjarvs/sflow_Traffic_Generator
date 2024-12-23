Here's how to use it:

Start the server by running the script:

bashCopypython ansible_api.py

To run a playbook, make a POST request:

bashCopycurl -X POST http://localhost:5000/playbook/run \
-H "Content-Type: application/json" \
-d '{"playbook_path": "/path/to/playbook.yml", "inventory_path": "/path/to/inventory.ini"}'

To check the status of a running playbook:

bashCopycurl http://localhost:5000/playbook/status/<run_id>

To list all playbook runs:

bashCopycurl http://localhost:5000/playbook/list
The API provides these features:

Asynchronous playbook execution
Status monitoring
Basic error handling
Run history

The status responses will include:

starting: Playbook execution is being initialized
running: Playbook is currently executing
completed: Playbook finished successfully
failed: Playbook execution failed (with error details)


The logs will be written to ansible_api.log and will include:

Playbook execution starts and completions
Error details when failures occur
Request information
Timing information

The log format looks like:
Copy2024-12-15 10:30:45,123 - INFO - Starting playbook execution - Run ID: 1702654245
2024-12-15 10:30:45,124 - INFO - Playbook: /path/to/playbook.yml
2024-12-15 10:30:45,124 - INFO - Inventory: /path/to/inventory.ini
Error handling now includes:

Input validation errors
File not found errors
Ansible execution errors
Unexpected errors
