import asyncio
import os
import json
import pathlib
import subprocess
import time
from typing import List, Dict, Optional, Union
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig

# Load environment variables from .env file
load_dotenv()

class WebCartAgent:
    def __init__(
        self, 
        website: str,
        items: List[dict],
        credentials: Dict[str, str] = None,
        headless: bool = False,
        browser_instance_path: Optional[str] = None
    ):
        """
        Initialize the web cart agent.
        
        Args:
            website (str): The website to navigate to (e.g., 'amazon.com', 'walmart.com')
            items (List[dict]): List of items to add to cart, each with name and optional details
            credentials (Dict[str, str], optional): Login credentials with keys 'username' and 'password'
            headless (bool, optional): Whether to run browser in headless mode
            browser_instance_path (str, optional): Path to your browser executable to use for automation
        """
        self.website = website
        self.items = items
        self.browser_process = None
        self.custom_browser_used = False
        
        # Try to get credentials from environment variables if not provided
        self.credentials = self._get_credentials(credentials)
        
        # Get browser configuration from environment or use defaults
        headless = os.getenv('BROWSER_HEADLESS', str(headless)).lower() == 'true'
        width = int(os.getenv('BROWSER_WIDTH', 1280))
        height = int(os.getenv('BROWSER_HEIGHT', 800))
        
        # Get browser_instance_path from environment if not provided
        if not browser_instance_path:
            browser_instance_path = os.getenv('BROWSER_INSTANCE_PATH')
            
        self.browser_instance_path = browser_instance_path
        
        # Initialize browser configuration with defaults
        browser_config = BrowserConfig(headless=headless)
        
        # Launch custom browser if path is provided
        if browser_instance_path:
            print(f"Launching browser from: {browser_instance_path}")
            
            # The browser-use package can directly use the browser_instance_path
            if os.path.isfile(browser_instance_path):
                print(f"Using direct browser executable path")
                browser_config = BrowserConfig(
                    headless=False,  # Always visible for custom browser
                    browser_instance_path=browser_instance_path
                )
                self.custom_browser_used = True
            else:
                print(f"Browser executable not found at path, attempting to resolve...")
                # Handle .app paths for macOS
                if browser_instance_path.endswith('.app') and os.path.isdir(browser_instance_path):
                    full_path = self._resolve_app_path(browser_instance_path)
                    if full_path and os.path.isfile(full_path):
                        print(f"Resolved to: {full_path}")
                        browser_config = BrowserConfig(
                            headless=False,  # Always visible for custom browser
                            browser_instance_path=full_path
                        )
                        self.custom_browser_used = True
                    else:
                        print(f"Could not resolve .app path, using default browser")
                else:
                    print(f"Invalid browser path, using default browser")
        
        # Initialize browser
        print(f"Initializing browser with config: {browser_config}")
        self.browser = Browser(config=browser_config)
        
        # Define task for the agent based on the website and items
        self.task = self._create_task()
        
        # Initialize the LLM-powered agent
        model_name = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.agent = Agent(
            task=self.task,
            llm=ChatOpenAI(model=model_name),
            browser=self.browser,
        )
    
    def _get_credentials(self, provided_credentials: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get credentials from provided dict or environment variables."""
        credentials = provided_credentials or {}
        
        # If no credentials provided, try to get from environment variables
        if not credentials:
            site_upper = self.website.split('.')[0].upper()
            username_key = f"{site_upper}_USERNAME"
            password_key = f"{site_upper}_PASSWORD"
            
            username = os.getenv(username_key)
            password = os.getenv(password_key)
            
            if username:
                credentials['username'] = username
            if password:
                credentials['password'] = password
                
        # Default values if still empty
        if 'username' not in credentials:
            credentials['username'] = '<<ASK_USER>>'
        if 'password' not in credentials:
            credentials['password'] = '<<ASK_USER>>'
            
        return credentials
    
    def _create_task(self) -> str:
        """Generate a detailed task prompt based on the website and items."""
        username = self.credentials.get('username', '<<ASK_USER>>')
        password = self.credentials.get('password', '<<ASK_USER>>')
        
        # Format the items list for the prompt
        items_formatted = ""
        for i, item in enumerate(self.items, 1):
            name = item.get('name', '')
            description = item.get('description', '')
            quantity = item.get('quantity', 1)
            options = item.get('options', {})
            
            items_formatted += f"Item {i}: {name}\n"
            if description:
                items_formatted += f"  Description: {description}\n"
            items_formatted += f"  Quantity: {quantity}\n"
            
            if options:
                items_formatted += "  Options:\n"
                for key, value in options.items():
                    items_formatted += f"    - {key}: {value}\n"
            items_formatted += "\n"
        
        # Create the JavaScript code for login prompt as a separate variable
        js_login_code = """
// No prompt, just silently remain on the login page for the user
"""
        
        # Create a periodic login status check code instead of a confirmation prompt
        js_confirm_code = """
browser.evaluate_and_return(js_code=`
  // Check login status without showing a prompt
  // Look for common login indicators
  const accountElements = document.querySelectorAll('a[href*=account], span[class*=account], div[class*=account], a[class*=account], *[aria-label*=account], *[id*=account]');
  const cartElements = document.querySelectorAll('a[href*=cart], span[class*=cart], div[class*=cart], *[aria-label*=cart], *[id*=cart]');
  const userNameElements = document.querySelectorAll('*:not(meta):not(script):not(style):not(path):not(input):not(button):not(a)[class*=user], *:not(meta):not(script):not(style):not(path):not(input):not(button):not(a)[id*=user]');
  const signOutElements = document.querySelectorAll('a[href*=logout], a[href*=signout], *[class*=logout], *[class*=signout], *[id*=logout], *[id*=signout], a:contains("Sign Out"), a:contains("Log Out")');
  
  // Get text content of potential account elements to check for logged-in state
  const accountText = Array.from(accountElements).map(el => el.textContent.trim()).join('|');
  const userText = Array.from(userNameElements).map(el => el.textContent.trim()).join('|');
  
  // Return the findings as an object
  return {
    hasAccountElements: accountElements.length > 0,
    hasCartElements: cartElements.length > 0,
    hasUserNameElements: userNameElements.length > 0,
    hasSignOutElements: signOutElements.length > 0,
    accountText,
    userText,
    isLikelyLoggedIn: accountElements.length > 0 || signOutElements.length > 0 || userNameElements.length > 0
  };
`)
"""

        # Create universal login instructions for all sites
        universal_login_instructions = """
        CRITICAL INSTRUCTIONS FOR ALL LOGIN PROCESSES:
        - When on ANY login page, DO ABSOLUTELY NOTHING. Do not show alerts or prompts.
        - FREEZE completely and DO NOT interact with the page in any way.
        - DO NOT click any elements, DO NOT refresh the page, DO NOT navigate away.
        - DO NOT SEARCH GOOGLE for any login instructions or text. 
        - WAIT in absolute stillness while the user inputs their credentials.
        - SILENTLY check login status in the background every 10 seconds.
        - DO NOT display any prompts asking if the user has completed login.
        - DO NOT interrupt the user's login process with any messages.
        - After detecting successful login status, verify the login by checking for user account icons/name.
        - Only after detecting login success through silent status checks, proceed with searching for items.
        """

        # Create JavaScript code to check for login status
        js_check_login_status = """
browser.evaluate_and_return(js_code=`
  // Look for common login indicators
  const accountElements = document.querySelectorAll('a[href*=account], span[class*=account], div[class*=account], a[class*=account], *[aria-label*=account], *[id*=account]');
  const cartElements = document.querySelectorAll('a[href*=cart], span[class*=cart], div[class*=cart], *[aria-label*=cart], *[id*=cart]');
  const userNameElements = document.querySelectorAll('*:not(meta):not(script):not(style):not(path):not(input):not(button):not(a)[class*=user], *:not(meta):not(script):not(style):not(path):not(input):not(button):not(a)[id*=user]');
  const signOutElements = document.querySelectorAll('a[href*=logout], a[href*=signout], *[class*=logout], *[class*=signout], *[id*=logout], *[id*=signout], a:contains("Sign Out"), a:contains("Log Out")');
  
  // Get text content of potential account elements to check for logged-in state
  const accountText = Array.from(accountElements).map(el => el.textContent.trim()).join('|');
  const userText = Array.from(userNameElements).map(el => el.textContent.trim()).join('|');
  
  // Return the findings as an object
  return {
    hasAccountElements: accountElements.length > 0,
    hasCartElements: cartElements.length > 0,
    hasUserNameElements: userNameElements.length > 0,
    hasSignOutElements: signOutElements.length > 0,
    accountText,
    userText,
    isLikelyLoggedIn: accountElements.length > 0 || signOutElements.length > 0 || userNameElements.length > 0
  };
`)
"""
        
        base_task = f"""
        # Web Cart Agent Task
        
        ## Objective
        Your task is to navigate to {self.website}, log in to the user's account if required,
        search for the following items, and add them to the cart.
        
        ## Items to Add to Cart
        {items_formatted}
        
        ## Login Information (if required)
        Username/Email: {username}
        Password: {password}
        
        {universal_login_instructions}

        ## Steps to Follow:
        1. Navigate to {self.website}.
        2. If login is required:
           a. Navigate to the login page (look for "Sign In" or "Login" links).
           b. IMPORTANT: After reaching the login page, STOP ALL ACTIONS completely. DO NOT show any alerts or prompts.
           c. WAIT COMPLETELY STILL while the user completes their login manually. DO NOT click anything, refresh, or navigate.
           d. Many websites have multi-step login flows (email → password → OTP). The user needs to complete ALL steps.
           e. Silently check login status in the background every 10 seconds using:
              ```javascript
{js_confirm_code}
              ```
           f. When login status check indicates login success (isLikelyLoggedIn is true), proceed to the next step.
           g. DO NOT use the "done" or "thought" actions during this process. You must actively wait for the user.
           h. DO NOT search Google, use the search box, or navigate away while waiting for login.
           i. YOU MUST NOT INTERACT WITH THE PAGE AT ALL during login - no clicks, no typing, no refreshing.
           j. DO NOT show any popup messages or alerts during the login process.
        
        3. For each item:
           a. Use the search function on the website to search for the item by name.
           b. From the search results, find the most relevant match for the item.
           c. If there are multiple options, try to find the one that best matches the description.
           d. If needed, set quantity and select any specified options before adding to cart.
           e. Click "Add to Cart" or similar button.
           f. Verify the item was successfully added to the cart before proceeding to the next item.
        
        4. After adding all items, navigate to the cart page to confirm all items are in the cart.
        
        5. Do NOT proceed to checkout.
        
        ## Important Notes
        - NEVER end the task with "done" action until all items are added to cart.
        - NEVER search Google for login instructions or waiting messages.
        - During login, you MUST REMAIN COMPLETELY STILL on the login page.
        - DO NOT display any alerts or prompts during the login process.
        - Silently check login status in the background periodically.
        - Be patient during multi-step login flows (username → password → OTP/2FA).
        - Look for the presence of account name, user-specific elements, or cart access as indicators of successful login.
        - Clear search results before searching for items.
        
        ## Website-Specific Instructions
        """
        
        # Add site-specific instructions based on the website domain
        site_name = self.website.split('.')[0].lower()
        site_instructions = {
            "amazon": """
            - For Amazon, use the search bar at the top of the page.
            - Be aware of sponsored results vs. regular results.
            - If there are "Buy Now" vs "Add to Cart" buttons, use "Add to Cart".
            - If prompted about protection plans or additional offerings, decline them.
            - Check for the cart confirmation message or icon update at the top right.
            - For quantity changes, use the dropdown or quantity selector before adding to cart.
            - For login verification, check for the presence of "Hello, [Name]" in the top right or "Account & Lists" dropdown.
            - Amazon typically uses a multi-step login process (email first, then password). Make sure all steps are completed.
            - CRITICAL: When on the login page, DO NOT click any buttons or refresh the page until the user completes login.
            - If OTP verification is required, wait until the user inputs the verification code.
            """,
            
            "walmart": """
            - For Walmart, use the search bar at the top of the page.
            - Pay attention to the "Sold and shipped by" information to ensure you're getting items from Walmart directly if possible.
            - If prompted about protection plans or warranties, decline them.
            - If asked about pickup vs delivery, skip this step as we're only adding to cart.
            - For quantity, use the "+" button to increase or directly update the quantity field.
            - For login verification, check for the presence of account name or "Account" indicator that shows the user is logged in.
            - CRITICAL: When on the login page, DO NOT click any buttons or refresh the page until the user completes login.
            """,
            
            "target": """
            - For Target, use the search bar at the top of the page.
            - Pay attention to "Sold and shipped by" to prioritize items sold directly by Target.
            - If prompted about protection plans or warranties, decline them.
            - For quantity, use the quantity selector before adding to cart.
            - For login verification, check for "Hi, [Name]" or the account icon in the top right.
            - CRITICAL: When on the login page, DO NOT click any buttons or refresh the page until the user completes login.
            """,
            
            "bestbuy": """
            - For Best Buy, use the search bar at the top of the page.
            - If prompted about protection plans or memberships, decline them.
            - If asked about store pickup vs shipping, skip this step.
            - For quantity, update the quantity selector before adding to cart.
            - For login verification, check for the account name or "Account" indicator in the top right.
            - CRITICAL: When on the login page, DO NOT click any buttons or refresh the page until the user completes login.
            """,
            
            "ebay": """
            - For eBay, use the search bar at the top of the page.
            - Filter for "Buy It Now" items to avoid auctions, unless instructed otherwise.
            - For item variations (size, color, etc.), select them from the dropdown menus before adding to cart.
            - For quantity, update the quantity field before clicking "Add to cart".
            - For login verification, check for the username or a "My eBay" dropdown in the top right.
            - CRITICAL: When on the login page, DO NOT click any buttons or refresh the page until the user completes login.
            """,
            
            "newegg": """
            - For Newegg, use the search bar at the top of the page.
            - Pay attention to "Sold and shipped by" information to prioritize items sold by Newegg.
            - If there are combo deals or add-ons suggested, you can skip those.
            - Be aware of the "Auto-Add" features - deselect anything the user didn't specify.
            - For login verification, check for "Hi, [Name]" or account indicators in the top right.
            - CRITICAL: When on the login page, DO NOT click any buttons or refresh the page until the user completes login.
            """,

            "flipkart": """
            - For Flipkart, use the search bar at the top of the page.
            - Pay attention to seller ratings when selecting products.
            - Be aware of "Flipkart Assured" products which are more reliable.
            - For login verification, check for the account name or icon in the top right.
            - CRITICAL: When on the login page, DO NOT click any buttons or refresh the page until the user completes login.
            - Flipkart login often involves OTP verification via phone - wait patiently without any interaction.
            - If a login popup appears, DO NOT close it or click anywhere else on the page.
            - Let the user handle all steps of the login process without any interference.
            - Wait for the user to confirm they've completed login before proceeding.
            - For quantity, use the quantity selector before adding to cart.
            - Look for "ADD TO CART" button typically in orange or yellow.
            - Avoid "BUY NOW" button as we're only adding to cart.
            """
        }
        
        # If we have specific instructions for this site, add them, otherwise add generic
        if site_name in site_instructions:
            site_specific = site_instructions[site_name]
        else:
            site_specific = """
            - Use the search bar at the top of the page to find each item.
            - Try different search terms if you can't find an exact match for an item.
            - For quantity changes, update the quantity field before adding to cart.
            - If prompted about additional options or warranties, decline them.
            - If there are product variations (size, color, etc.), select them before adding to cart.
            - For login verification, look for account name, user-specific elements, or welcome messages.
            - CRITICAL: When on the login page, DO NOT click any buttons or refresh the page until the user completes login.
            - If login involves OTP verification or captcha, wait patiently without any interaction.
            - Let the user handle all steps of the login process without any interference.
            """
        
        return base_task + site_specific
    
    async def run(self):
        """Execute the web cart agent task."""
        print(f"Starting web cart agent for {self.website}")
        print(f"Adding {len(self.items)} item(s) to cart")
        
        try:
            # Run the agent
            await self.agent.run()
            print(f"Task completed successfully. All items have been added to cart on {self.website}.")
            
            # Let the user know we're finishing up
            if self.custom_browser_used:
                print("Task complete. The browser window will remain open so you can continue shopping.")
                print("All browser resources and connections have been preserved for your use.")
            else:
                # For default browser, we just notify completion
                print("Task complete. Your items remain in the cart on the website.")
                
        except Exception as e:
            print(f"Error during execution: {str(e)}")
            print("Browser window is still available for your use.")
            
        # Call cleanup even though it doesn't do much
        await self.cleanup()
    
    async def cleanup(self):
        """
        Cleanup resources but keep the browser open.
        This allows you to continue using the browser window after the agent completes.
        """
        try:
            print("Task complete. The browser window will remain open so you can continue shopping.")
            print("All resources have been preserved for continued use.")
            
            # We don't need to do any cleanup as browser-use package handles it
            # and we've configured the browser to use an existing browser instance
            pass
        except Exception as e:
            print(f"Note: Error during cleanup: {str(e)}")
            print("This is non-critical; continue using your browser window.")
    
    def _resolve_app_path(self, app_path):
        """Resolve macOS .app path to find the executable inside."""
        try:
            if "Brave" in app_path:
                return os.path.join(app_path, 'Contents/MacOS/Brave Browser')
            elif "Chrome" in app_path:
                return os.path.join(app_path, 'Contents/MacOS/Google Chrome')
            elif "Firefox" in app_path:
                return os.path.join(app_path, 'Contents/MacOS/firefox')
            elif "Safari" in app_path:
                return os.path.join(app_path, 'Contents/MacOS/Safari')
            elif "Edge" in app_path:
                return os.path.join(app_path, 'Contents/MacOS/Microsoft Edge')
            else:
                # Generic fallback
                app_name = os.path.basename(app_path).replace('.app', '')
                return os.path.join(app_path, f'Contents/MacOS/{app_name}')
        except Exception as e:
            print(f"Error resolving app path: {str(e)}")
            return None

async def run_from_json(json_file):
    """Run the agent from a JSON configuration file."""
    with open(json_file, 'r') as f:
        config = json.load(f)
    
    agent = WebCartAgent(
        website=config['website'],
        items=config.get('items', []),
        credentials=config.get('credentials', {}),
        headless=config.get('headless', False),
        browser_instance_path=config.get('browser_instance_path')
    )
    
    try:
        await agent.run()
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        print("Browser window is still available for your use.")

async def run_interactive():
    """Run the agent in interactive mode, prompting for details."""
    # Get website
    website = input("Enter the website (e.g., amazon.com, walmart.com): ")
    
    # Get items
    items = []
    while True:
        item_name = input("\nEnter item name (or leave blank to finish): ")
        if not item_name:
            break
            
        item = {'name': item_name}
        
        description = input("Enter item description (optional): ")
        if description:
            item['description'] = description
            
        quantity = input("Enter quantity (or leave blank for default 1): ")
        if quantity:
            item['quantity'] = int(quantity)
        
        options = {}
        while True:
            option_name = input("Enter option name (e.g., 'color', 'size') or leave blank to finish options: ")
            if not option_name:
                break
                
            option_value = input(f"Enter value for {option_name}: ")
            options[option_name] = option_value
        
        if options:
            item['options'] = options
            
        items.append(item)
        
        if input("Add another item? (y/n): ").lower() != 'y':
            break
    
    # No items entered
    if not items:
        print("No items specified. Exiting.")
        return
        
    # Get credentials (optional)
    use_credentials = input("\nDo you want to provide login credentials now? (y/n): ").lower() == 'y'
    credentials = {}
    
    if use_credentials:
        credentials['username'] = input("Enter username/email: ")
        credentials['password'] = input("Enter password: ")
    
    # Get browser instance path (optional)
    browser_path = input("\nEnter path to browser executable (or leave blank for default): ")
    
    # Create and run the agent
    agent = WebCartAgent(
        website=website,
        items=items,
        credentials=credentials,
        browser_instance_path=browser_path if browser_path else None
    )
    
    try:
        await agent.run()
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        print("Browser window is still available for your use.")

async def main():
    print("Web Cart Agent")
    print("-------------")
    
    # Determine how to run the agent
    if len(os.sys.argv) > 1:
        # Check if config file was provided
        config_file = os.sys.argv[1]
        if os.path.exists(config_file) and config_file.endswith('.json'):
            print(f"Running with configuration from {config_file}")
            await run_from_json(config_file)
        else:
            print(f"Error: Config file {config_file} not found or not a JSON file")
    else:
        # Run in interactive mode
        await run_interactive()

if __name__ == "__main__":
    asyncio.run(main()) 