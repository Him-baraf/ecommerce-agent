import asyncio
import os
import json
from typing import List, Dict, Optional, Union
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig

# Load environment variables from .env file
load_dotenv()

class Product:
    def __init__(self, url: str, quantity: int = 1, options: Dict[str, str] = None):
        """
        Initialize a product to be added to cart.
        
        Args:
            url (str): URL of the product
            quantity (int, optional): Quantity to add. Defaults to 1.
            options (Dict[str, str], optional): Product options like size, color, etc. Defaults to None.
        """
        self.url = url
        self.quantity = quantity
        self.options = options or {}

class EcommerceCartAgent:
    def __init__(
        self, 
        products: Union[Product, List[Product]], 
        ecommerce_site: str,
        credentials: Dict[str, str] = None,
        headless: bool = False
    ):
        """
        Initialize the advanced e-commerce cart agent.
        
        Args:
            products: Single Product instance or list of Product instances
            ecommerce_site: Name of the e-commerce site (e.g., 'amazon', 'ebay', 'walmart')
            credentials: Login credentials with keys 'username' and 'password'
            headless: Whether to run browser in headless mode
        """
        # Convert single product to list
        if isinstance(products, Product):
            self.products = [products]
        else:
            self.products = products
        
        self.ecommerce_site = ecommerce_site.lower()
        
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
        
        # Define task for the agent based on the e-commerce site and product URLs
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
            site_upper = self.ecommerce_site.upper()
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
    
    def _create_task(self):
        """Create a task description for the agent."""
        items_description = "\n".join([f"- Product URL: {product.url} (Quantity: {product.quantity})" for product in self.products])
        
        # Create the JavaScript code for login prompt as a separate variable
        js_login_code = """
await browser.evaluate_and_return(js_code="return new Promise(resolve => { const confirmLogin = () => { if (confirm('Have you COMPLETELY finished logging in? Click OK only if you have FULLY logged in including any OTP/2FA steps.')) { resolve('Login confirmed by user'); } else { setTimeout(confirmLogin, 5000); } }; alert('Please log in manually in this browser window. The agent will wait until you finish.'); setTimeout(confirmLogin, 5000); })")
"""
        
        return f"""You are an e-commerce shopping assistant. Your task is to add multiple items to a cart on {self.ecommerce_site}.

Items to add:
{items_description}

Follow these steps:
1. Go to the website: {self.ecommerce_site}
2. If login is required:
   a. Navigate to the login page (look for "Sign In" or "Login" links).
   b. Once on the login page, simply execute this JavaScript:
      ```javascript
{js_login_code}
      ```
   c. After showing this alert to the user, DO NOT navigate away from the login page.
   d. Wait for the user to complete their login process entirely.
   e. After the user dismisses the alert, verify they have successfully logged in.
   f. DO NOT use the search box for anything related to login or waiting.
   g. DO NOT search Google.
3. For each item in the list:
   a. Navigate to the product URL
   b. If the item has size or configuration options, select the default options
   c. Set the quantity to the requested amount
   d. Add the item to the cart
   e. Confirm the item was successfully added
4. After adding all items, navigate to the cart page to verify all items are in the cart

Important notes:
- NEVER search Google for login instructions or waiting messages
- Stay on the site's login page until the user completes their login
- The JavaScript alert shown to the user will block their interaction until they click OK
- The user will dismiss the alert ONLY after they have completely finished the login process
- Be patient during OTP verification, captcha, or two-factor authentication
- Verify login success by checking for user account indicators before proceeding

Regularly report your status and what you are doing."""
    
    async def run(self):
        """Run the e-commerce cart agent."""
        print(f"Starting cart agent for {self.ecommerce_site}")
        print(f"Adding {len(self.products)} item(s) to cart")

        try:
            await self.agent.run()
            print(f"Task completed successfully. All items have been added to cart.")
        except Exception as e:
            print(f"Error during execution: {str(e)}")
        finally:
            # Keep browser open for user to review the cart
            input("Press Enter to close the browser...")
            await self.browser.close()

async def run_from_json(json_file):
    """Run the agent from a JSON configuration file."""
    with open(json_file, 'r') as f:
        config = json.load(f)
    
    products = []
    for product_data in config.get('products', []):
        products.append(Product(
            url=product_data['url'],
            quantity=product_data.get('quantity', 1),
            options=product_data.get('options', {})
        ))
    
    agent = EcommerceCartAgent(
        products=products,
        ecommerce_site=config['ecommerce_site'],
        credentials=config.get('credentials', {}),
        headless=config.get('headless', False)
    )
    
    await agent.run()

async def run_interactive():
    """Run the agent in interactive mode, prompting for details."""
    products = []
    
    # Get ecommerce site
    ecommerce_site = input("Enter the e-commerce site name (e.g., amazon, ebay, walmart): ")
    
    # Get product details
    while True:
        product_url = input("Enter product URL (or leave blank to finish): ")
        if not product_url:
            break
            
        quantity = input("Enter quantity (or leave blank for default 1): ")
        quantity = int(quantity) if quantity else 1
        
        options = {}
        while True:
            option_name = input("Enter option name (e.g., 'color', 'size') or leave blank to finish options: ")
            if not option_name:
                break
                
            option_value = input(f"Enter value for {option_name}: ")
            options[option_name] = option_value
            
        products.append(Product(url=product_url, quantity=quantity, options=options))
        
        if input("Add another product? (y/n): ").lower() != 'y':
            break
    
    # No products entered
    if not products:
        print("No products specified. Exiting.")
        return
        
    # Get credentials (optional)
    use_credentials = input("Do you want to provide login credentials now? (y/n): ").lower() == 'y'
    credentials = {}
    
    if use_credentials:
        credentials['username'] = input("Enter username/email: ")
        credentials['password'] = input("Enter password: ")
    
    # Create and run the agent
    agent = EcommerceCartAgent(
        products=products,
        ecommerce_site=ecommerce_site,
        credentials=credentials
    )
    
    await agent.run()

async def main():
    print("E-commerce Cart Agent - Advanced Version")
    print("----------------------------------------")
    
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