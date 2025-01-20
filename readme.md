# Retailify Bot

Retailify Bot is a Discord bot designed to monitor the availability and prices of specific products on retail websites like Pokémon Center, Best Buy, Walmart, and Target. It uses web scraping techniques powered by Playwright and stealth tools to mimic human-like browsing behavior. The bot is locally hosted on a personal server and deployed using Docker containers for efficient management and portability.

---

## Features
- **Product Watchlist**: Allows users to add product URLs to a personalized watchlist.
- **Stock Monitoring**: Periodically checks the stock status and price of products on supported retail websites.
- **Notifications**: Sends Discord notifications to users when a product in their watchlist is back in stock or its price changes.
- **Database Storage**: Tracks product availability history in an SQLite database.
- **Cookie Persistence**: Saves and reuses browser cookies to bypass bot detection mechanisms on certain websites.
- **Discord Commands**:
  - `!add <url>`: Add a product URL to the watchlist.
  - `!remove <id>`: Remove a product from the watchlist using its ID.
  - `!view`: View all items in the watchlist.
  - `!help`: Show available commands and usage.

---

## Technologies Used
### Backend:
1. **Python**: Core programming language used for the bot's logic and features.
2. **Discord.py**: A library to interact with the Discord API for sending messages and managing commands.
3. **Playwright**: A modern web scraping tool used to navigate and interact with retail websites.
4. **Playwright Stealth**: Helps bypass anti-bot detection by emulating human-like browser behavior.
5. **SQLite**: A lightweight relational database for storing watchlists and product stock history.
6. **Aiosqlite**: An asynchronous library for interacting with the SQLite database.

### Deployment:
1. **Docker**: Encapsulates the bot and its dependencies into a container for portability and ease of deployment.
2. **Docker Compose**: Manages multi-container deployment (bot and database) with a single configuration file.
3. **Lightweight Base Image**: Uses `python:3.10-slim` for minimal resource consumption.

---

## Setup Instructions

### 1. Prerequisites
- Install Docker and Docker Compose on your server.
- Create a `.env` file to securely store your Discord bot token and client ID:
  ```env
  DISCORD_TOKEN=<your_discord_bot_token>
  DISCORD_CLIENT_ID=<your_discord_client_id>
  ```

### 2. File Structure
Ensure the following files are in your project directory:
```
retailify/
├── bot.py
├── check_stock.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── retailify.db
├── cookies.json
├── .env
```

### 3. Docker Compose Configuration
#### `docker-compose.yml`
- Defines two services:
  1. `bot`: The Discord bot service.
  2. `db`: An SQLite container to handle database storage.
- Mounts `cookies.json` and `retailify.db` for persistence.

#### `Dockerfile`
- Builds a lightweight Python container.
- Installs all required Python libraries and Playwright dependencies.

### 4. Build and Run the Containers
- Build the Docker image:
  ```bash
  docker-compose build
  ```
- Start the services:
  ```bash
  docker-compose up -d
  ```
- View running logs (optional):
  ```bash
  docker-compose logs -f bot
  ```

---

## How It Works
1. **Discord Integration**:
   - Users interact with the bot via Discord commands to manage their watchlist and view notifications.

2. **Web Scraping**:
   - Playwright is used to navigate retail websites and check product stock status and price.
   - Cookies are saved and reused to maintain session persistence and reduce bot detection risks.

3. **Periodic Checks**:
   - The bot periodically iterates through the watchlist, scrapes the required data, and compares it with previous data stored in the database.

4. **Database**:
   - Watchlist and stock history are stored in `retailify.db`.
   - SQLite ensures lightweight and fast local data access.

5. **Notifications**:
   - When a product's status changes, the bot sends a Discord message to the user who added the product to their watchlist.

---

## Usage
- Add the bot to your server using the generated invite link:
  ```bash
  Invite your bot using this URL: https://discord.com/api/oauth2/authorize?client_id=<DISCORD_CLIENT_ID>&permissions=2147690560&scope=bot%20applications.commands
  ```
- Start interacting with the bot:
  - **Add a product**: `!add <url>`
  - **Remove a product**: `!remove <id>`
  - **View watchlist**: `!view`
  - **Get help**: `!help`

---

## Notes
- This bot is hosted locally on your server, and its database and cookies are stored as volumes to ensure data persistence.
- The bot uses Docker containers to ensure an isolated and reproducible environment, simplifying deployment and scaling.

---

Feel free to modify the bot's code or commands to suit your needs!