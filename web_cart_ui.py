import os
import json
import asyncio
import gradio as gr
from dotenv import load_dotenv
from web_cart_agent import WebCartAgent, run_from_json

# Load environment variables from .env file
load_dotenv()

# Global variables
temp_json_path = "temp_cart_config.json"

def create_temp_config(website, items_text, credentials=None, headless=False):
    """
    Create a temporary JSON configuration file from the UI inputs.
    
    Args:
        website: Website URL to shop from
        items_text: Text with items (one per line)
        credentials: Optional dictionary with username and password
        headless: Whether to run in headless mode
    
    Returns:
        Path to the created config file
    """
    # Parse items from text - each line is an item
    items = []
    for line in items_text.strip().split('\n'):
        if not line.strip():
            continue
            
        parts = line.split('|')
        item = {"name": parts[0].strip()}
        
        # If there are additional parameters (description, quantity, options)
        if len(parts) > 1 and parts[1].strip():
            item["description"] = parts[1].strip()
            
        if len(parts) > 2 and parts[2].strip():
            try:
                item["quantity"] = int(parts[2].strip())
            except ValueError:
                pass  # If quantity is not a valid number, use default
                
        # If there are options in the format key:value,key2:value2
        if len(parts) > 3 and parts[3].strip():
            options = {}
            option_pairs = parts[3].strip().split(',')
            for pair in option_pairs:
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    options[key.strip()] = value.strip()
            
            if options:
                item["options"] = options
                
        items.append(item)
    
    # Create configuration dictionary
    config = {
        "website": website,
        "items": items,
        "headless": headless
    }
    
    # Add credentials if provided
    if credentials and credentials.get("username") and credentials.get("password"):
        config["credentials"] = credentials
    
    # Write to temp file
    with open(temp_json_path, 'w') as f:
        json.dump(config, f, indent=4)
        
    return temp_json_path

async def run_cart_agent(website, items_text, use_credentials, username, password, headless):
    """Run the web cart agent with the provided configuration."""
    # Create credentials dict if needed
    credentials = None
    if use_credentials:
        credentials = {
            "username": username,
            "password": password
        }
    
    # Create temporary config file
    config_path = create_temp_config(website, items_text, credentials, headless)
    
    # Display the generated configuration
    with open(config_path, 'r') as f:
        config_json = json.load(f)
    
    # Format items for display
    items_display = ""
    for i, item in enumerate(config_json["items"], 1):
        items_display += f"Item {i}: {item['name']}\n"
        if "description" in item:
            items_display += f"  Description: {item['description']}\n"
        items_display += f"  Quantity: {item.get('quantity', 1)}\n"
        
        if "options" in item:
            items_display += "  Options:\n"
            for key, value in item["options"].items():
                items_display += f"    - {key}: {value}\n"
        items_display += "\n"
    
    # Start log with config details
    log = f"Configuration created with {len(config_json['items'])} items for {website}.\n\n"
    log += f"Items to be added to cart:\n{items_display}\n"
    
    # Add login handling information to the log
    if 'credentials' in config_json and config_json['credentials'].get('username') and config_json['credentials'].get('password'):
        log += "Login credentials provided. The agent will attempt to use them if needed.\n"
    else:
        log += "No login credentials provided. If login is required, the browser will open to the login page and pause.\n"
        log += "You will need to manually enter your credentials in the browser when prompted.\n"
        log += "This approach works better for sites with OTP verification, CAPTCHA, or two-factor authentication.\n"
    
    log += "Starting web cart agent...\n"
    
    try:
        # Run the agent
        agent = WebCartAgent(
            website=config_json['website'],
            items=config_json['items'],
            credentials=config_json.get('credentials', {}),
            headless=config_json.get('headless', False)
        )
        
        # Update log with initialization status
        log += f"Agent initialized for {website}.\n"
        
        # Ensure visibility for login
        if not config_json.get('headless', False):
            log += f"Browser will launch with visible window so you can interact with it if needed.\n"
        else:
            log += f"Browser will launch in headless mode. This may not work if login is required.\n"
            
        log += "This may take a few moments...\n"
        log += "If login is required, the agent will navigate to the login page and wait for your input.\n"
        log += "Simply complete the login process in the browser window when it appears.\n"
        
        # Start the agent in a way that allows us to update the UI
        task = asyncio.create_task(agent.run())
        
        # Return initial log message and indicate process is starting
        yield log
        
        # Wait for completion
        await task
        
        # Update log with success message
        log += f"\nSuccess! All items have been added to cart on {website}."
        yield log
    except Exception as e:
        # Update log with error message
        log += f"\nError during execution: {str(e)}"
        yield log
    finally:
        # Clean up temp config file
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)

def create_ui():
    """Create and launch the Gradio UI for the web cart agent."""
    
    # Define the item format helper text
    item_format_text = """
    Enter each item on a separate line using the following format:
    Item Name | Description (optional) | Quantity (optional) | Options (optional)
    
    For options, use key:value format separated by commas. For example:
    Wireless Mouse | Logitech MX Master 3 | 2 | color:black,size:standard
    
    Examples:
    iPhone Charger | Apple original lightning cable | 1 | color:white,length:1m
    Wireless Mouse | Logitech MX Master 3 | 2
    Blue Light Glasses | Computer glasses | 1 | color:black,size:medium
    """
    
    # Create the UI layout
    with gr.Blocks(title="E-commerce Cart Agent", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# E-commerce Cart Agent")
        gr.Markdown("Add items to your cart on e-commerce websites automatically.")
        
        with gr.Row():
            with gr.Column(scale=2):
                # Input fields
                website_input = gr.Textbox(
                    label="Website URL", 
                    placeholder="e.g., amazon.com, walmart.com",
                    info="Enter the e-commerce website URL"
                )
                
                items_input = gr.Textbox(
                    label="Items List",
                    placeholder="Enter items, one per line",
                    info="Enter items to add to cart",
                    lines=10
                )
                
                headless_checkbox = gr.Checkbox(
                    label="Run in Headless Mode",
                    value=False,
                    info="If checked, the browser will run in the background (no visible window)"
                )
                
                # Credentials section
                with gr.Accordion("Login Credentials (Optional)", open=False):
                    gr.Markdown("""
                    ### Login Handling Options:
                    
                    **Option 1:** Provide credentials here (for simple username/password logins)
                    
                    **Option 2:** Leave empty and manually log in when the browser opens
                    
                    **Note:** For websites with OTP verification, CAPTCHA, or two-factor authentication, 
                    you should leave credentials empty and complete the login manually when the browser opens.
                    """)
                    
                    use_credentials = gr.Checkbox(
                        label="Use Login Credentials",
                        value=False,
                        info="Check this to provide basic username/password login information"
                    )
                    
                    with gr.Group(visible=False) as credentials_group:
                        username_input = gr.Textbox(
                            label="Username/Email",
                            placeholder="your_email@example.com"
                        )
                        password_input = gr.Textbox(
                            label="Password",
                            placeholder="your_password",
                            type="password"
                        )
                    
                    # Show/hide credentials inputs based on checkbox
                    use_credentials.change(
                        lambda x: gr.Group(visible=x),
                        inputs=use_credentials,
                        outputs=credentials_group
                    )
                
                # Submit button
                submit_btn = gr.Button("Add Items to Cart", variant="primary")
            
            with gr.Column(scale=1):
                # Format guide
                gr.Markdown("## Item Format Guide")
                gr.Markdown(item_format_text)
        
        # Output area
        output_log = gr.Textbox(
            label="Agent Log",
            placeholder="Agent activity will be displayed here...",
            lines=15,
            max_lines=25
        )
        
        # Connect the submit button to the run function
        submit_btn.click(
            fn=run_cart_agent,
            inputs=[
                website_input, 
                items_input, 
                use_credentials,
                username_input,
                password_input,
                headless_checkbox
            ],
            outputs=output_log,
            api_name="add_to_cart"
        )
        
    return demo

if __name__ == "__main__":
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Web Cart Agent UI")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the UI on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to run the UI on")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    args = parser.parse_args()
    
    # Create and launch the UI
    ui = create_ui()
    ui.queue()
    ui.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        inbrowser=True
    ) 