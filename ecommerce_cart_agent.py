import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig

# Load environment variables from .env file
load_dotenv()

class EcommerceCartAgent:
    def __init__(self, product_url, ecommerce_site, credentials=None, quantity=1):
        """
        Initialize the e-commerce cart agent.
        
        Args:
            product_url (str): URL of the product to add to cart
            ecommerce_site (str): Name of the e-commerce site (e.g., 'amazon', 'ebay', 'walmart')
            credentials (dict, optional): Login credentials with keys 'username' and 'password'
            quantity (int, optional): Quantity to add to cart. Defaults to 1.
        """
        self.product_url = product_url
        self.ecommerce_site = ecommerce_site.lower()
        self.credentials = credentials or {}
        self.quantity = quantity
        
        # Browser configuration
        browser_config = BrowserConfig(
            headless=False  # Set to True in production
        )
        
        self.browser = Browser(config=browser_config)
        
        # Define task for the agent based on the e-commerce site and product URL
        self.task = self._create_task()
        
        # Initialize the LLM-powered agent
        self.agent = Agent(
            task=self.task,
            llm=ChatOpenAI(model="gpt-4o"),
            browser=self.browser,
        )
    
    def _create_task(self):
        """Create a task description for the agent."""
        product_description = f"""Product URL: {self.product_url}
Quantity: {self.quantity}"""
        
        # Create the JavaScript code for login prompt as a separate variable
        js_login_code = """
await browser.evaluate_and_return(js_code="return new Promise(resolve => { const confirmLogin = () => { if (confirm('Have you COMPLETELY finished logging in? Click OK only if you have FULLY logged in including any OTP/2FA steps.')) { resolve('Login confirmed by user'); } else { setTimeout(confirmLogin, 5000); } }; alert('Please log in manually in this browser window. The agent will wait until you finish.'); setTimeout(confirmLogin, 5000); })")
"""
        
        return f"""You are an e-commerce shopping assistant. Your task is to add a product to a cart.

Product Information:
{product_description}

Follow these steps:
1. Go to the product page at the provided URL.
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
3. If the product page has size or configuration options, select the default options.
4. Set the quantity to the requested amount.
5. Add the item to the cart.
6. Confirm that the item was successfully added to the cart.

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

        try:
            await self.agent.run()
            print(f"Task completed successfully. Items have been added to cart.")
        except Exception as e:
            print(f"Error during execution: {str(e)}")
        finally:
            # Keep browser open for user to review the cart
            input("Press Enter to close the browser...")
            await self.browser.close()

async def main():
    # Example usage
    product_url = input("Enter the product URL: ")
    ecommerce_site = input("Enter the e-commerce site name (e.g., amazon, ebay, walmart): ")
    quantity = input("Enter quantity (or leave blank for default 1): ")
    quantity = int(quantity) if quantity else 1
    
    # Initialize agent with product URL and site
    agent = EcommerceCartAgent(
        product_url=product_url,
        ecommerce_site=ecommerce_site,
        quantity=quantity
    )
    
    # Run the agent
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main()) 