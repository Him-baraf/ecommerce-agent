# E-commerce Cart Agent UI Guide

This guide will help you use the E-commerce Cart Agent UI to easily add items to your cart on various e-commerce websites.

## Getting Started

1. Launch the UI by running:
   ```
   python web_cart_ui.py
   ```

2. Your default web browser will open with the UI interface.

## Adding Items to Cart

### Step 1: Enter the Website

In the "Website URL" field, enter the domain of the e-commerce site you want to shop on. For example:
- amazon.com
- walmart.com
- bestbuy.com
- target.com
- ebay.com

### Step 2: Enter Your Shopping List

In the "Items List" text area, enter each item you want to add to your cart on a separate line using this format:

```
Item Name | Description (optional) | Quantity (optional) | Options (optional)
```

The format explained:
- **Item Name**: Required. The name of the product you want to search for
- **Description**: Optional. Additional details to help find the right product
- **Quantity**: Optional. Number of items to add (default is 1)
- **Options**: Optional. Product-specific options in the format `key:value,key2:value2`

Example:
```
iPhone USB-C Charging Cable | Apple original 1 meter cable | 2 | color:white,length:1m
Wireless Mouse | Logitech MX Master 3, graphite color | 1 | color:graphite
Reusable Water Bottle | 32oz stainless steel vacuum insulated | 1 | color:silver,size:32oz
```

> **Tip**: You can copy the sample shopping list from the `example_items.txt` file and modify it for your needs.

### Step 3: Configure Additional Options

#### Headless Mode
- If you check "Run in Headless Mode", the browser will run in the background without showing its window.
- Leave this unchecked if you want to see the agent in action.

#### Login Credentials
1. Click the "Login Credentials (Optional)" dropdown
2. Check "Use Login Credentials"
3. Enter your username/email and password for the website
4. If you don't provide credentials, the agent will prompt you during execution if login is required

### Step 4: Add Items to Cart

1. Click the "Add Items to Cart" button
2. Watch the "Agent Log" area for real-time updates
3. The agent will:
   - Navigate to the website
   - Log in (if credentials were provided)
   - Search for and add each item to your cart
   - Show a success message when complete

### Step 5: Complete Your Purchase

Once the agent has finished, your cart will be filled with the requested items. You can:
1. Review your cart in the browser
2. Continue shopping manually
3. Proceed to checkout

## Troubleshooting

- **Items not found**: Try providing more specific descriptions or different search terms
- **Login issues**: Check that your credentials are correct and that you don't have 2FA enabled
- **Browser crashes**: Try running with headless mode disabled to see what's happening
- **Website changes**: E-commerce sites occasionally change their layouts, which might affect the agent's ability to navigate them

## Advanced Options

When launching the UI, you can specify additional parameters:

```
python web_cart_ui.py --port 8080 --host 0.0.0.0 --share
```

- `--port`: Change the default port (default is 7860)
- `--host`: Change the host address (default is 127.0.0.1)
- `--share`: Create a shareable public URL (useful for sharing with others)

## Examples

### Example 1: Amazon Shopping List

Website: amazon.com

Items:
```
iPhone USB-C Charging Cable | Apple original 1 meter cable | 2 | color:white,length:1m
Wireless Mouse | Logitech MX Master 3, graphite color | 1 | color:graphite
Blue Light Blocking Glasses | Anti-fatigue computer glasses with clear lenses | 1 | color:black,size:medium
```

### Example 2: Walmart Grocery List

Website: walmart.com

Items:
```
Bananas | Organic if available | 1
Milk | 2% milk, half-gallon | 1
Bread | Whole wheat sandwich bread | 1
Eggs | Organic large eggs, dozen | 1
```

### Example 3: Target Home Goods

Website: target.com

Items:
```
Bath Towels | Cotton bath towels, set of 4 | 1 | color:gray
Bed Sheets | Queen size, 100% cotton | 1 | size:queen,color:white
Picture Frames | 8x10 black frames | 2 | size:8x10,color:black
``` 