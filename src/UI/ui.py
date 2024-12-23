import streamlit as st
import requests
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Optional

if 'task_running' not in st.session_state:
    st.session_state.task_running = False

class AnsibleTaskUI:
    def __init__(self):
        st.set_page_config(page_title="Ansible Playbook Executor", layout="wide")
        
        # Initialize session state
        if 'console_messages' not in st.session_state:
            st.session_state.console_messages = []
        if 'task_running' not in st.session_state:
            st.session_state.task_running = False
        if 'verbose_console' not in st.session_state:
            st.session_state.verbose_console = False
        if 'last_api_call' not in st.session_state:
            st.session_state.last_api_call = None
        
        # API Configuration
        self.api_host = "http://localhost:8000"  # Default API host
            
    def log_to_console(self, message: str, level: str = "info"):
        """Add a timestamped message to the console output."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if level == "error":
            formatted_message = f"❌ {timestamp} - ERROR: {message}"
        elif level == "success":
            formatted_message = f"✅ {timestamp} - SUCCESS: {message}"
        elif level == "warning":
            formatted_message = f"⚠️ {timestamp} - WARNING: {message}"
        else:
            formatted_message = f"ℹ️ {timestamp} - INFO: {message}"
            
        st.session_state.console_messages.append(formatted_message)
        
    def clear_console(self):
        """Clear the console output."""
        st.session_state.console_messages = []

    def render_console(self):
        """Render the console output."""
        st.markdown("### Console Output")
        
        # Add clear button
        if st.button("Clear Console", type="secondary", key="clear_console"):
            self.clear_console()
            st.experimental_rerun()
            
        # Show console content
        if not st.session_state.console_messages:
            st.info("No console output yet. Execute the playbook to see updates here.")
        else:
            console_content = "\n".join(st.session_state.console_messages)
            st.code(console_content, language="plain")

    def format_json_output(self, data: Dict) -> str:
        """Format JSON data for console display."""
        return json.dumps(data, indent=2)
        
    def create_input_form(self) -> Dict:
        """Create the input form for collecting user parameters."""
        with st.form("playbook_params", clear_on_submit=False):
            # API Configuration
            with st.expander("API Configuration", expanded=False):
                api_host = st.text_input(
                    "API Host",
                    value=self.api_host,
                    placeholder="http://localhost:8000",
                    help="API endpoint host (e.g., http://localhost:8000)"
                )
            
            # Divider
            st.divider()
            
            # Playbook parameters
            collector_ip = st.text_input(
                "Collector IP (Required)", 
                placeholder="192.168.1.100",
                help="sFlow collector IP address"
            )
            
            collector_port = st.number_input(
                "Collector Port", 
                min_value=1,
                max_value=65535,
                value=6343,
                help="sFlow collector port (default: 6343)"
            )
            
            sampling_rate = st.number_input(
                "Sampling Rate",
                min_value=1,
                value=1000,
                help="sFlow sampling rate (default: 1000)"
            )
            
            # Divider before controls
            st.divider()
            
            # Form controls in a more compact layout
            col1, col2 = st.columns([1, 1])
            with col1:
                submit_button = st.form_submit_button(
                    "Execute Playbook",
                    type="primary",
                    disabled=st.session_state.task_running,
                    use_container_width=True
                )
            
            with col2:
                st.write("")  # Spacing
                st.toggle("Verbose Console", key="verbose_console", 
                         help="Show detailed API calls and responses")
            
            if st.session_state.task_running:
                st.info("⏳ Task is currently running...")
            
            if submit_button:
                if not collector_ip:
                    st.error("❌ Collector IP is required!")
                    return None
                    
                return {
                    "collector_ip": collector_ip,
                    "collector_port": collector_port,
                    "sampling_rate": sampling_rate
                }
        return None

    def api_call_with_timeout(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make API call with timeout handling."""
        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=10,  # 10 second timeout
                **kwargs
            )
            response.raise_for_status()
            st.session_state.last_api_call = datetime.now()
            return response
        except requests.Timeout:
            raise TimeoutError("Request timed out after 10 seconds")
        except requests.RequestException as e:
            raise RuntimeError(f"API call failed: {str(e)}")

    def run(self):
        """Main application loop."""
        # Full width title
        st.title("Network Configuration Tool")
        
        # Create tabs or sections for different tools
        tab1, tab2 = st.tabs(["sFlow Configuration", "Future Component"])
        
        with tab1:
            # Card container for the playbook executor
            with st.container():
                st.markdown("### Ansible Playbook Executor")
                
                # Create two main columns with 1:2 ratio for the executor content
                main_col1, main_col2 = st.columns([1, 2])
                
                with main_col1:
                    # Create input form
                    params = self.create_input_form()
                    
                    # Create status container
                    status_container = st.empty()
                    
                with main_col2:
                    # Make console take full height
                    with st.container():
                        # Render console output
                        self.render_console()
        
        with tab2:
            st.info("Future component will be added here")
        
        # Handle form submission
        if params and not st.session_state.task_running:
            st.session_state.task_running = True
            
            try:
                # Log request details if verbose
                if st.session_state.verbose_console:
                    self.log_to_console("Making API request to execute playbook")
                    self.log_to_console(f"Parameters:\n{self.format_json_output(params)}")
                
                # Execute playbook
                response = self.api_call_with_timeout(
                    "POST",
                    f"{self.api_host}/execute",
                    json=params
                )
                
                task_data = response.json()
                task_id = task_data.get('task_id')
                
                if not task_id:
                    raise ValueError("No task ID received from API")
                
                self.log_to_console(f"Playbook execution started. Task ID: {task_id}", "success")
                
                # Poll for status updates
                max_retries = 3
                retry_count = 0
                
                while st.session_state.task_running:
                    try:
                        # Check for timeout between polls
                        if st.session_state.last_api_call:
                            time_since_last_call = (datetime.now() - st.session_state.last_api_call).total_seconds()
                            if time_since_last_call > 10:
                                raise TimeoutError("No response from API for over 10 seconds")
                        
                        # Get status update
                        status_response = self.api_call_with_timeout(
                            "GET",
                            f"{self.api_host}/status/{task_id}"
                        )
                        
                        status_data = status_response.json()
                        
                        # Update status display
                        with status_container:
                            st.markdown("### Task Status")
                            status = status_data.get('status', 'UNKNOWN')
                            
                            if status == 'COMPLETED':
                                st.success(f"Status: {status}")
                            elif status in ['FAILED', 'ERROR']:
                                st.error(f"Status: {status}")
                            else:
                                st.info(f"Status: {status}")
                            
                            if 'progress' in status_data:
                                st.progress(float(status_data['progress']) / 100)
                            
                            if 'message' in status_data:
                                st.markdown(f"**Message:** {status_data['message']}")
                        
                        # Log verbose output if enabled
                        if st.session_state.verbose_console:
                            self.log_to_console(f"Raw status update:\n{self.format_json_output(status_data)}")
                        
                        # Check if task is complete
                        if status in ['COMPLETED', 'FAILED', 'ERROR']:
                            st.session_state.task_running = False
                            break
                        
                        time.sleep(2)  # Short sleep between polls
                        
                    except TimeoutError as e:
                        self.log_to_console(str(e), "error")
                        retry_count += 1
                        if retry_count >= max_retries:
                            st.session_state.task_running = False
                            self.log_to_console("Maximum retry attempts reached. Stopping task.", "error")
                            break
                        time.sleep(2)
                        
                    except Exception as e:
                        self.log_to_console(f"Error during status check: {str(e)}", "error")
                        st.session_state.task_running = False
                        break
                
            except TimeoutError as e:
                self.log_to_console(str(e), "error")
                st.session_state.task_running = False
                
            except Exception as e:
                self.log_to_console(f"Error: {str(e)}", "error")
                st.session_state.task_running = False
            
            st.experimental_rerun()

if __name__ == "__main__":
    app = AnsibleTaskUI()
    app.run()
