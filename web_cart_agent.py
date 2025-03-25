import asyncio
import os
import json
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
        headless: bool = False
    ):
        """
        Initialize the web cart agent.
        
        Args:
            website (str): The website to navigate to (e.g., 'amazon.com', 'walmart.com')
            items (List[dict]): List of items to add to cart, each with name and optional details
            credentials (Dict[str, str], optional): Login credentials with keys 'username' and 'password'
            headless (bool, optional): Whether to run browser in headless mode
        """
        self.website = website
        self.items = items
        
        # Try to get credentials from environment variables if not provided
        self.credentials = self._get_credentials(credentials)
        
        # Get browser configuration from environment or use defaults
        headless = os.getenv('BROWSER_HEADLESS', str(headless)).lower() == 'true'
        width = int(os.getenv('BROWSER_WIDTH', 1280))
        height = int(os.getenv('BROWSER_HEIGHT', 800))
        
        # Browser configuration
        browser_config = BrowserConfig(
            headless=headless
        )
        
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
browser.evaluate(js_code="alert('Please log in manually in this browser window. Click OK to dismiss this message and begin login. For multi-step login flows (email → password → OTP), complete ALL steps.');")
"""
        
        # Create a confirmation JavaScript code
        js_confirm_code = """
browser.evaluate_and_return(js_code="return confirm('Have you COMPLETELY finished logging in? Click OK only after you have FULLY logged in including any OTP/2FA steps. Click Cancel if you need more time.');")
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
        
        ## Steps to Follow:
        1. Navigate to {self.website}.
        2. If login is required:
           a. Navigate to the login page (look for "Sign In" or "Login" links).
           b. IMPORTANT: Execute the following JavaScript code to show an alert to the user:
              ```javascript
{js_login_code}
              ```
           c. WAIT while the user completes their login manually (do not proceed to next steps).
           d. Many websites have multi-step login flows (email → password → OTP). The user needs to complete ALL steps.
           e. After waiting at least 15 seconds for login to begin, check if the user has completed login using:
              ```javascript
{js_confirm_code}
              ```
           f. If the user clicks Cancel, wait 10 more seconds and check again. REPEAT this step until the user confirms.
           g. After the user confirms login completion, VERIFY the login was successful by checking for login indicators:
              ```javascript
{js_check_login_status}
              ```
           h. If login indicators are not found (isLikelyLoggedIn is false), inform the user that you don't detect a login yet and ask them to confirm again after they have completed ALL login steps.
           i. DO NOT use the "done" or "thought" actions during this process. You must actively wait for the user.
           j. DO NOT search Google, use the search box, or navigate away while waiting for login.
           k. You MUST execute the JavaScript alert and confirmation prompts - DO NOT SKIP THESE STEPS.
        
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
        - During login, you MUST show the JavaScript alert and then actively wait for confirmation.
        - The JavaScript alert shown to the user will inform them to log in manually.
        - You must REPEATEDLY check if login is complete using the confirmation prompt.
        - Be patient during multi-step login flows (username → password → OTP/2FA).
        - Use the login status check to verify that login was successful before proceeding.
        - If the user confirms login but the status check fails, ask them to double-check that all login steps were completed.
        - Look for the presence of account name, user-specific elements, or cart access as indicators of successful login.
        
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
            - If OTP verification is required, wait until the user inputs the verification code.
            """,
            
            "walmart": """
            - For Walmart, use the search bar at the top of the page.
            - Pay attention to the "Sold and shipped by" information to ensure you're getting items from Walmart directly if possible.
            - If prompted about protection plans or warranties, decline them.
            - If asked about pickup vs delivery, skip this step as we're only adding to cart.
            - For quantity, use the "+" button to increase or directly update the quantity field.
            - For login verification, check for the presence of account name or "Account" indicator that shows the user is logged in.
            """,
            
            "target": """
            - For Target, use the search bar at the top of the page.
            - Pay attention to "Sold and shipped by" to prioritize items sold directly by Target.
            - If prompted about protection plans or warranties, decline them.
            - For quantity, use the quantity selector before adding to cart.
            - For login verification, check for "Hi, [Name]" or the account icon in the top right.
            """,
            
            "bestbuy": """
            - For Best Buy, use the search bar at the top of the page.
            - If prompted about protection plans or memberships, decline them.
            - If asked about store pickup vs shipping, skip this step.
            - For quantity, update the quantity selector before adding to cart.
            - For login verification, check for the account name or "Account" indicator in the top right.
            """,
            
            "ebay": """
            - For eBay, use the search bar at the top of the page.
            - Filter for "Buy It Now" items to avoid auctions, unless instructed otherwise.
            - For item variations (size, color, etc.), select them from the dropdown menus before adding to cart.
            - For quantity, update the quantity field before clicking "Add to cart".
            - For login verification, check for the username or a "My eBay" dropdown in the top right.
            """,
            
            "newegg": """
            - For Newegg, use the search bar at the top of the page.
            - Pay attention to "Sold and shipped by" information to prioritize items sold by Newegg.
            - If there are combo deals or add-ons suggested, you can skip those.
            - Be aware of the "Auto-Add" features - deselect anything the user didn't specify.
            - For login verification, check for "Hi, [Name]" or account indicators in the top right.
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
            """
        
        return base_task + site_specific
    
    async def run(self):
        """Execute the web cart agent task."""
        print(f"Starting web cart agent for {self.website}")
        print(f"Adding {len(self.items)} item(s) to cart")
        
        # If credentials were provided via the UI, use them directly
        # If not, let the agent navigate to the site first and handle login when required
        # through browser interaction
        
        # Run the agent
        try:
            await self.agent.run()
            print(f"Task completed successfully. All items have been added to cart on {self.website}.")
        except Exception as e:
            print(f"Error during execution: {str(e)}")
        finally:
            # Wait 5 seconds before closing the browser
            print("Browser will close in 5 seconds. Your items remain in the cart on the website.")
            await asyncio.sleep(5)  # 5-second delay
            await self.browser.close()

async def run_from_json(json_file):
    """Run the agent from a JSON configuration file."""
    with open(json_file, 'r') as f:
        config = json.load(f)
    
    agent = WebCartAgent(
        website=config['website'],
        items=config.get('items', []),
        credentials=config.get('credentials', {}),
        headless=config.get('headless', False)
    )
    
    await agent.run()

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
    
    # Create and run the agent
    agent = WebCartAgent(
        website=website,
        items=items,
        credentials=credentials
    )
    
    await agent.run()

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