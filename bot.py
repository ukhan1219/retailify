import discord
from discord.ext import commands
import aiosqlite
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import json
from pathlib import Path

COOKIES_PATH = "cookies.json"
#   env vars
load_dotenv()
TOKEN=os.getenv("DISCORD_TOKEN")
DB_PATH="retailify.db"

#   intents
intents = discord.Intents.default()
intents.message_content=True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Stock checking function
async def check_stock(url):
    print(f"[DEBUG] Checking stock for URL: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use visible browser for debugging
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Load cookies if they exist
        if Path(COOKIES_PATH).exists():
            with open(COOKIES_PATH, "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)

        page = await context.new_page()
        
        try:
            print(f"[DEBUG] Navigating to URL: {url}")
            await page.goto(url, wait_until="load")

            # Save cookies and local storage for future use
            cookies = await context.cookies()
            with open(COOKIES_PATH, "w") as f:
                json.dump(cookies, f)
            # Delay to ensure page is fully loaded
            await asyncio.sleep(5)

            stock_text = None
            price_text = None
            in_stock = False

            if "pokemoncenter.com" in url:
                print("[DEBUG] Detected Pokémon Center")
                try:
                    # Wait for the stock button and check its state
                    await page.wait_for_selector(".add-to-cart-button--PZmQF", timeout=15000)
                    stock_element = await page.query_selector(".add-to-cart-button--PZmQF")
                    if stock_element:
                        stock_text = await stock_element.inner_text()
                        print(f"[DEBUG] Pokémon Center button text: {stock_text}")
                        in_stock = "unavailable" not in stock_text.lower()

                    # Get the price
                    price_element = await page.query_selector(".product-price--1E59R")
                    if price_element:
                        price_text = await price_element.inner_text()
                        print(f"[DEBUG] Pokémon Center price: {price_text}")
                except Exception as e:
                    print(f"[ERROR] Error while checking Pokémon Center stock: {e}")
                    in_stock = False
            elif "bestbuy.com" in url:
                print("[DEBUG] Detected Best Buy")
                stock_element = await page.query_selector(".add-to-cart-button")
                if stock_element:
                    stock_text = await stock_element.inner_text()
                    in_stock = "sold out" not in stock_text.lower()
                price_element = await page.query_selector(".priceView-customer-price span")
                if price_element:
                    price_text = await price_element.inner_text()

            elif "walmart.com" in url:
                print("[DEBUG] Detected Walmart")
                stock_element = await page.query_selector("[data-automation-id='atc']")
                if stock_element:
                    stock_text = await stock_element.inner_text()
                    in_stock = "add to cart" in stock_text.lower()
                price_element = await page.query_selector(".price-characteristic")
                if price_element:
                    price_text = await price_element.inner_text()

            elif "target.com" in url:
                print("[DEBUG] Detected Target")
                try:
                    # Wait for the stock status button
                    await page.wait_for_selector("#addToCartButtonOrTextIdFor93954435, button[aria-label*='Add to cart']", timeout=15000)

                    # Query the button for stock status
                    stock_element = await page.query_selector("#addToCartButtonOrTextIdFor93954435, button[aria-label*='Add to cart']")
                    if stock_element:
                        is_disabled = await stock_element.get_attribute("disabled")  # Check if the button is disabled
                        button_text = await stock_element.get_attribute("aria-label")
                        print(f"[DEBUG] Target button aria-label: {button_text}")
                        print(f"[DEBUG] Target button disabled attribute: {is_disabled}")

                        # Check if the button is not disabled
                        in_stock = is_disabled is None  # If disabled attribute is None, the item is in stock
                    else:
                        print("[DEBUG] Target stock button not found.")
                        in_stock = False

                    # Attempt to get the price
                    price_element = await page.query_selector("[data-test='product-price']")
                    if price_element:
                        price_text = await price_element.inner_text()
                        print(f"[DEBUG] Target price found: {price_text}")
                except Exception as e:
                    print(f"[ERROR] Error while checking Target stock: {e}")
                    in_stock = False


            else:
                print(f"[DEBUG] Unsupported website for URL: {url}")

            if stock_text:
                print(f"[DEBUG] Stock text found: {stock_text}")
            if price_text:
                print(f"[DEBUG] Price found: {price_text}")

        except Exception as e:
            print(f"[ERROR] Error while checking stock: {e}")
            in_stock = False
        finally:
            await browser.close()

        print(f"[DEBUG] Stock status for URL '{url}': {'In Stock' if in_stock else 'Out of Stock'}")
        if price_text:
            print(f"[DEBUG] Price for URL '{url}': {price_text}")
        return in_stock, price_text


# Periodic stock checking
async def periodic_stock_check():
    while True:
        print("[DEBUG] Starting periodic stock checks...")
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id, url FROM watchlist") as cursor:
                items = await cursor.fetchall()
            print(f"[DEBUG] Fetched {len(items)} items from watchlist.")

            for user_id, url in items:
                print(f"[DEBUG] Checking stock for User ID: {user_id}, URL: {url}")
                in_stock, price = await check_stock(url)
                now = datetime.utcnow()

                async with db.execute(
                    "SELECT in_stock FROM stock_log WHERE user_id = ? AND url = ?",
                    (user_id, url),
                ) as cursor:
                    result = await cursor.fetchone()

                if result and result[0] == in_stock:
                    print(f"[DEBUG] No change in stock status for URL: {url}. Skipping update.")
                    continue

                print(f"[DEBUG] Updating stock log for URL: {url}")
                await db.execute(
                    """
                    INSERT INTO stock_log (user_id, url, in_stock, last_checked)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, url) DO UPDATE SET
                    in_stock = excluded.in_stock,
                    last_checked = excluded.last_checked
                    """,
                    (user_id, url, in_stock, now),
                )
                await db.commit()

                if in_stock:
                    message = f"Item from `{url}` is now in stock!"
                    if price:
                        message += f" Price: {price}"
                    print(f"[DEBUG] Notifying user {user_id}: {message}")
                    user = await bot.fetch_user(user_id)
                    await user.send(message)

        print("[DEBUG] Stock check complete. Sleeping for 10 minutes.")
        await asyncio.sleep(600)  # Wait for 10 minutes before checking again


# On bot ready
@bot.event
async def on_ready():
    print(f"[DEBUG] Bot logged in as {bot.user}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                UNIQUE(user_id, url)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stock_log (
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                in_stock BOOLEAN NOT NULL,
                last_checked TIMESTAMP NOT NULL,
                PRIMARY KEY (user_id, url)
            )
        """)
        await db.commit()
    print("[DEBUG] Database initialized and ready.")
    bot.loop.create_task(periodic_stock_check())


# Add product URL
@bot.command(name="add")
async def add_url(ctx, url: str):
    print(f"[DEBUG] User {ctx.author.id} requested to add URL: {url}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, url) VALUES (?, ?)",
            (ctx.author.id, url)
        )
        async with db.execute(
            "SELECT id FROM watchlist WHERE user_id = ? AND url = ?",
            (ctx.author.id, url)
        ) as cursor:
            result = await cursor.fetchone()
        await db.commit()
    if result:
        print(f"[DEBUG] URL added with ID: {result[0]}")
        await ctx.send(f"Added URL `{url}` to your watchlist with ID `{result[0]}`")
    else:
        print(f"[DEBUG] URL `{url}` is already in the watchlist.")
        await ctx.send(f"URL `{url}` is already in your watchlist.")


# Remove product URL by ID
@bot.command(name="remove")
async def remove_url(ctx, item_id: int):
    print(f"[DEBUG] User {ctx.author.id} requested to remove item with ID: {item_id}")
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT url FROM watchlist WHERE user_id = ? AND id = ?",
            (ctx.author.id, item_id)
        ) as cursor:
            result = await cursor.fetchone()

        if result:
            print(f"[DEBUG] Removing URL: {result[0]}")
            await db.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND id = ?",
                (ctx.author.id, item_id)
            )
            await db.commit()
            await ctx.send(f"Removed URL `{result[0]}` from your watchlist.")
        else:
            print(f"[DEBUG] No item found with ID: {item_id}")
            await ctx.send(f"No item found with ID `{item_id}` in your watchlist.")


# View watchlist
@bot.command(name="view")
async def view_watchlist(ctx):
    print(f"[DEBUG] User {ctx.author.id} requested to view their watchlist.")
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, url FROM watchlist WHERE user_id = ?",
            (ctx.author.id,)
        ) as cursor:
            rows = await cursor.fetchall()

    if rows:
        print(f"[DEBUG] Watchlist for User {ctx.author.id}: {rows}")
        watchlist = "\n".join([f"ID: {item_id}, URL: {url}" for item_id, url in rows])
        await ctx.send(f"Your watchlist:\n{watchlist}")
    else:
        print(f"[DEBUG] Watchlist is empty for User {ctx.author.id}")
        await ctx.send("Your watchlist is empty.")

# Help command
@bot.command(name="help")
async def show_help(ctx):
    help_message = """
**Retailify Bot Commands:**
1. `!add <url>` - Add a product URL to your watchlist. Example:
   `!add https://example.com/product-page`
   
2. `!remove <id>` - Remove a product from your watchlist by its ID. Example:
   `!remove 1`
   
3. `!view` - View all items in your watchlist along with their IDs.
   
4. `!help` - Show this help message.
    """
    print(f"[DEBUG] User {ctx.author.id} requested the help command.")
    await ctx.send(help_message)
    
    
#   create invite link     
def generate_invite_link(client_id, permissions):
    base_url = "https://discord.com/api/oauth2/authorize"
    scopes = ["bot", "applications.commands"]
    permissions = str(permissions)
    return f"{base_url}?client_id={client_id}&permissions={permissions}&scope={'%20'.join(scopes)}"

invite_link = generate_invite_link(os.getenv("DISCORD_CLIENT_ID"), 2147690560)
print(f"Invite your bot using this URL:\n{invite_link}")

bot.run(TOKEN)