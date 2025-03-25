# E-commerce Browser Agent

A browser agent that automates the process of adding products to your cart on e-commerce websites using Browser Use.

## Features

- Automatically navigates to product pages on various e-commerce sites
- Handles login when required (with robust multi-step login support)
  - Supports traditional username/password logins
  - Handles multi-step login processes (email → password → OTP)
  - Works with sites requiring OTP, CAPTCHA, or two-factor authentication
- Adds products to the cart with intelligent matching
- Supports multiple popular e-commerce platforms:
  - Amazon
  - eBay
  - Walmart
  - Best Buy
  - Target
  - Newegg
  - And more (with generic fallback behavior)
- Handles product options (size, color, etc.)
- Multiple product support
- Multiple interaction methods:
  - URL-based approach (provide specific product URLs)
  - Search-based approach (provide website and product names to search for)
- User-friendly web interface with Gradio
- Session persistence for maintaining login state between runs

## Requirements

- Python 3.8+
- Browser Use library
- OpenAI API key for GPT-4o
- Gradio (for the UI)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/browser-use/browser-use.git
git clone https://github.com/browser-use/web-ui.git
```

2. Install the required dependencies:
```bash
cd browser-use
pip install -e .

# Install additional dependencies
pip install python-dotenv langchain-openai gradio
```

3. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Web Interface

The easiest way to use the e-commerce cart agent is through the web interface:

```bash
python web_cart_ui.py
```

The web interface provides:
- A field to enter the e-commerce website URL
- A text area to list the items you want to add to cart
- Optional login credentials
- Real-time log of the agent's actions
- Support for manual login with clear guidance

You can also specify additional options:
```bash
python web_cart_ui.py --port 8080 --host 0.0.0.0 --share
```

Arguments:
- `--port`: Port to run the UI on (default: 7860)
- `--host`: Host to run the UI on (default: 127.0.0.1)
- `--share`: Create a shareable public link

### Item Format in the UI

In the web interface, enter each item on a separate line using the following format:
```
Item Name | Description (optional) | Quantity (optional) | Options (optional)
```

For options, use key:value format separated by commas. For example:
```
Wireless Mouse | Logitech MX Master 3 | 2 | color:black,size:standard
```

Examples:
```
iPhone Charger | Apple original lightning cable | 1 | color:white,length:1m
Wireless Mouse | Logitech MX Master 3 | 2
Blue Light Glasses | Computer glasses | 1 | color:black,size:medium
```

## Login Handling

The agent provides two approaches for handling login:

### 1. Automated Login (Basic Sites)

For simple login systems that just require username and password (without additional verification):
- Provide login credentials in the UI or command line
- The agent will enter these credentials on the login page

### 2. Manual Login with Assistance (Recommended)

For sites with complex login processes (OTP, 2FA, CAPTCHA, etc.):
- Leave credentials empty in the UI
- The agent will:
  - Navigate to the login page
  - Display an alert informing you to log in manually
  - Wait while you complete all login steps (including any OTP or verification)
  - Verify successful login before proceeding
  - Continue with adding items to cart after successful login

This approach works reliably with:
- Multi-step login flows (common on Amazon, where email and password are on separate pages)
- Sites requiring OTP (one-time passwords) via SMS or email
- CAPTCHAs or other human verification
- Two-factor authentication
- Sites with complex login forms or unusual login flows

### Login Verification

After login, the agent actively verifies successful login by checking for:
- Account information elements on the page
- Username indicators
- Sign out links or buttons
- Account-specific features
- Cart access

This ensures the agent only proceeds when login is truly complete.

### Session Persistence

The agent now supports maintaining your login state between runs:

- **How it works**: After successful login, the agent saves your browser session (cookies, local storage) to a local file
- **Next run**: When you run the agent for the same website again, it automatically loads your saved session
- **Benefits**:
  - No need to log in every time you use the agent for the same website
  - Handles cookies and other session data securely on your local machine
  - Separate sessions for different websites and user accounts
  - Especially valuable for sites with complex login processes (OTP, 2FA)

- **Configuration**:
  - In the web UI: The session is saved automatically
  - In command line: You'll be asked if you want to save the session
  - In code/API: Use the `use_session=True` parameter when creating the agent

Note: For security, session data is stored in a `sessions` directory in the project root. You can delete these files at any time to clear saved login information.

## Command Line Usage

### Basic URL-Based Usage

Run the simple e-commerce cart agent that takes specific product URLs:

```bash
python ecommerce_cart_agent.py
```

The script will prompt you for:
1. The product URL (e.g., https://www.amazon.com/product/...)
2. The e-commerce site name (e.g., amazon, ebay, walmart)
3. Login credentials if required

### Advanced URL-Based Usage

#### Advanced Agent with Multiple Products

The advanced agent provides more features for URL-based shopping:

```bash
python ecommerce_cart_agent_advanced.py
```

This will run in interactive mode, prompting you for:
1. E-commerce site name
2. Multiple product URLs
3. Quantity for each product
4. Product options (color, size, etc.)
5. Login credentials

#### Using JSON Configuration for URL-Based Shopping

You can also specify everything in a JSON configuration file:

```bash
python ecommerce_cart_agent_advanced.py sample_config.json
```

The JSON file should follow this format:

```json
{
    "ecommerce_site": "amazon",
    "headless": false,
    "credentials": {
        "username": "your_email@example.com",
        "password": "your_password"
    },
    "products": [
        {
            "url": "https://www.amazon.com/example-product-1",
            "quantity": 2,
            "options": {
                "color": "blue",
                "size": "medium"
            }
        },
        {
            "url": "https://www.amazon.com/example-product-2",
            "quantity": 1
        }
    ]
}
```

### Search-Based Shopping

If you don't have specific product URLs but know the items you want to purchase, you can use the web cart agent:

```bash
python web_cart_agent.py
```

This agent:
1. Navigates to a specified e-commerce site
2. Searches for items by name
3. Adds the most relevant matches to the cart

#### Using JSON Configuration for Search-Based Shopping

You can provide a JSON configuration file:

```bash
python web_cart_agent.py web_cart_config.json
```

The JSON file should follow this format:

```json
{
    "website": "amazon.com",
    "headless": false,
    "credentials": {
        "username": "your_email@example.com",
        "password": "your_password"
    },
    "use_session": true,
    "items": [
        {
            "name": "iPhone charger",
            "description": "Apple original lightning cable, white color, 1 meter length",
            "quantity": 2,
            "options": {
                "color": "white",
                "length": "1m"
            }
        },
        {
            "name": "wireless mouse",
            "description": "Logitech MX Master 3, graphite color",
            "quantity": 1
        }
    ]
}
```

## Using Environment Variables

You can store credentials in environment variables to avoid typing them repeatedly:

```
AMAZON_USERNAME=your_amazon_email@example.com
AMAZON_PASSWORD=your_amazon_password
WALMART_USERNAME=your_walmart_email@example.com
WALMART_PASSWORD=your_walmart_password
```

The agent will automatically use these credentials when interacting with the respective sites.

## Programmatic API

### URL-Based Shopping API

```python
import asyncio
from ecommerce_cart_agent import EcommerceCartAgent

async def main():
    # Initialize with product URL and site
    agent = EcommerceCartAgent(
        product_url="https://www.amazon.com/product/...",
        ecommerce_site="amazon",
        credentials={
            "username": "your_email@example.com",
            "password": "your_password"
        }
    )
    
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

Or for the advanced agent:

```python
import asyncio
from ecommerce_cart_agent_advanced import EcommerceCartAgent, Product

async def main():
    # Create products
    products = [
        Product(
            url="https://www.amazon.com/product1/...",
            quantity=2,
            options={"color": "red", "size": "large"}
        ),
        Product(
            url="https://www.amazon.com/product2/..."
        )
    ]
    
    # Initialize agent
    agent = EcommerceCartAgent(
        products=products,
        ecommerce_site="amazon",
        credentials={
            "username": "your_email@example.com",
            "password": "your_password"
        },
        headless=False
    )
    
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Search-Based Shopping API

```python
import asyncio
from web_cart_agent import WebCartAgent

async def main():
    # Items to search for and add to cart
    items = [
        {
            "name": "iPhone charger",
            "description": "Apple original lightning cable",
            "quantity": 2,
            "options": {"color": "white"}
        },
        {
            "name": "wireless mouse",
            "description": "Logitech MX Master 3",
            "quantity": 1
        }
    ]
    
    # Initialize agent
    agent = WebCartAgent(
        website="amazon.com",
        items=items,
        credentials={
            "username": "your_email@example.com",
            "password": "your_password"
        },
        headless=False,
        use_session=True  # Enable session persistence
    )
    
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## How It Works

The agent uses Browser Use, a framework that combines LLMs (specifically GPT-4o) with web browser automation. Its workflow includes:

1. **Website Navigation**: Navigates to the specified e-commerce website or product URL(s)

2. **Login Handling**:
   - For basic login: Uses provided credentials if available
   - For complex login: Displays an alert instructing the user to log in manually
   - Waits patiently during multi-step login processes (email → password → OTP)
   - Verifies successful login by checking for account elements before proceeding

3. **Product Search and Selection**:
   - Searches for products if using search-based approach
   - Intelligently selects the most relevant match based on description
   - Handles product variations and options

4. **Cart Management**:
   - Sets quantity if different from default
   - Selects product options if specified (color, size, etc.)
   - Adds products to cart
   - Verifies the products were added successfully before proceeding to the next item

5. **Completion**:
   - Navigates to the cart page to confirm all items are in the cart
   - Waits 5 seconds for the user to view the cart contents
   - Automatically closes the browser after the brief viewing period
   - Provides a confirmation message with the website where items were added

The agent uses LLM reasoning to adapt to different website layouts and changes, making it more resilient compared to traditional web automation tools. It combines structured tasks with flexible response to variations in site design.

## Key Technical Features

1. **Robust Login Detection**:
   - JavaScript-based login verification checks multiple indicators of login status
   - Handles multi-page login flows with session detection
   - Waits for user confirmation of login completion

2. **Intelligent Product Matching**:
   - Uses semantic understanding to find products that best match descriptions
   - Handles variations in product listings and search results

3. **Website-Specific Adaptations**:
   - Contains custom instructions for major e-commerce platforms
   - Falls back to generic behavior for unsupported sites

4. **User-Friendly UI**:
   - Clear instructions for login handling
   - Real-time logging of agent actions
   - Intuitive item specification format

5. **Error Handling and Recovery**:
   - Verifies each step before proceeding
   - Provides clear feedback when actions succeed or fail

6. **Session Persistence**:
   - Maintains login state between agent runs
   - Securely stores cookies and session data locally
   - Creates separate sessions for different websites and accounts
   - Reduces the need for repetitive logins

## Future Improvements

- Implement handling for more e-commerce sites
- Add checkout automation (optional)
- Enhance session management with expiration handling
- Enhanced handling for complex captchas
- Price monitoring and comparison across multiple sites
- Enhance the UI with additional features (saved shopping lists, history tracking)
- Browser fingerprinting protection for more reliable operation

## License

This project is licensed under the MIT License - see the LICENSE file for details. 