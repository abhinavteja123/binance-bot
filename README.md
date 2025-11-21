# Binance Futures Trading Bot

A comprehensive CLI-based trading bot for Binance USDT-M Futures Testnet with support for multiple order types, robust logging, and advanced trading strategies.

## 🎯 Features

### Core Orders (Mandatory)
- ✅ **Market Orders**: Execute immediate buy/sell at current market price
- ✅ **Limit Orders**: Place orders at specific price levels

### Advanced Orders (Bonus)
- ✅ **Stop-Limit Orders**: Trigger limit orders when stop price is reached
- ✅ **OCO Orders**: One-Cancels-the-Other (simultaneous take-profit and stop-loss)
- ✅ **TWAP Strategy**: Time-Weighted Average Price (split large orders over time)
- ✅ **Grid Trading**: Automated buy-low/sell-high within a price range

### Additional Features
- ✅ Comprehensive input validation
- ✅ Structured logging with timestamps
- ✅ Error handling and retry mechanisms
- ✅ Interactive CLI with colored output
- ✅ Account information and position tracking
- ✅ Real-time order monitoring

## 📁 Project Structure

```
binance-bot/
│
├── src/                          # All source code
│   ├── config.py                 # Configuration and settings
│   ├── utils.py                  # Utility functions and logging
│   ├── base_bot.py               # Base bot class with API integration
│   ├── market_orders.py          # Market order implementation
│   ├── limit_orders.py           # Limit order implementation
│   ├── main.py                   # Main CLI interface
│   │
│   └── advanced/                 # Advanced order implementations
│       ├── stop_limit.py         # Stop-limit orders
│       ├── oco.py                # OCO (One-Cancels-the-Other) orders
│       ├── twap.py               # TWAP strategy
│       └── grid_strategy.py      # Grid trading strategy
│
├── bot.log                       # Execution logs (auto-generated)
├── requirements.txt              # Python dependencies
├── .env.                 # Example environment configuration
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Binance Testnet account
- Git (for repository management)

### 2. Register for Binance Futures Testnet

1. Visit [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Sign up with your email
3. Verify your account
4. Navigate to API Management
5. Create a new API key
6. Save your API Key and Secret Key securely

### 3. Clone the Repository

```bash
git clone https://github.com/yourusername/binance-bot.git
cd binance-bot
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure API Credentials

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:
```env
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_api_secret_here
USE_TESTNET=True
TESTNET_BASE_URL=https://testnet.binancefuture.com
```

**⚠️ IMPORTANT**: Never commit your `.env` file or share your API credentials!

## 💻 Usage

### Interactive CLI Mode (Recommended)

Run the main interactive interface:

```bash
python src/main.py
```

This provides a menu-driven interface for all order types and account management.

### Command-Line Mode

Each order type can also be run independently from the command line:

#### Market Orders
```bash
python src/market_orders.py BTCUSDT BUY 0.01
python src/market_orders.py ETHUSDT SELL 0.1
```

#### Limit Orders
```bash
python src/limit_orders.py BTCUSDT BUY 0.01 45000
python src/limit_orders.py ETHUSDT SELL 0.1 3000 GTC
```

#### Stop-Limit Orders
```bash
python src/advanced/stop_limit.py BTCUSDT BUY 0.01 44000 44100
python src/advanced/stop_limit.py ETHUSDT SELL 0.1 2950 2940
```

#### OCO Orders (One-Cancels-the-Other)
```bash
python src/advanced/oco.py BTCUSDT SELL 0.01 46000 44000
python src/advanced/oco.py ETHUSDT BUY 0.1 2900 3100 --monitor
```

#### TWAP Strategy
```bash
# Execute 0.1 BTC buy order over 10 minutes in 5 chunks
python src/advanced/twap.py BTCUSDT BUY 0.1 10 5

# With limit orders and custom offset
python src/advanced/twap.py ETHUSDT SELL 1.0 30 10 --limit --offset 0.2
```

#### Grid Trading
```bash
# Create 10 grid levels between 44000-46000
python src/advanced/grid_strategy.py BTCUSDT 44000 46000 10 0.01

# With monitoring and custom interval
python src/advanced/grid_strategy.py ETHUSDT 2900 3100 20 0.1 --monitor --interval 60
```

## 📊 Logging

All bot activities are logged to `bot.log` with detailed information:

- API requests and responses
- Order placements and executions
- Errors and exceptions with stack traces
- Timestamps for all events

Example log entry:
```
2025-11-19 10:30:45 - MarketOrder - INFO - MARKET Order - {'symbol': 'BTCUSDT', 'side': 'BUY', 'quantity': 0.01, 'orderId': 12345, 'status': 'FILLED'}
```

## 🔍 Order Types Explained

### Market Order
Executes immediately at the current market price. Best for quick entries/exits.

**Use case**: You want to buy/sell immediately at whatever the current price is.

### Limit Order
Places an order at a specific price. Only executes if market reaches that price.

**Use case**: You want to buy at $44,000 when BTC is currently at $45,000.

### Stop-Limit Order
Triggers a limit order when a stop price is reached.

**Use case**: You want to buy BTC at $44,100 if it drops to $44,000 (stop hunting).

### OCO Order
Places both take-profit and stop-loss orders. When one fills, the other cancels.

**Use case**: You have a position and want automatic exit at either profit target or stop loss.

### TWAP Strategy
Splits a large order into smaller chunks executed over time to minimize market impact.

**Use case**: You want to buy 10 BTC but don't want to move the market with one large order.

### Grid Trading
Places multiple buy/sell orders at different price levels to profit from price oscillation.

**Use case**: You expect BTC to range between $44,000-$46,000 and want to profit from the swings.

## 🛡️ Error Handling

The bot includes comprehensive error handling:

- Input validation for all parameters
- API error catching and logging
- Connection retry mechanisms
- User-friendly error messages
- Detailed error traces in logs

## ⚙️ Configuration

Edit `src/config.py` to customize:

- Leverage settings
- Minimum quantity/price
- Log format and level
- Validation rules

## 🧪 Testing Recommendations

1. **Start Small**: Use minimal quantities (0.001 BTC) for testing
2. **Test Each Order Type**: Verify all order types work correctly
3. **Check Logs**: Review `bot.log` after each operation
4. **Monitor Testnet**: Watch your testnet account for execution
5. **Test Edge Cases**: Try invalid inputs to verify validation

## 📝 Development Notes

### Dependencies
- `python-binance`: Official Binance API wrapper
- `colorama`: Cross-platform colored terminal output
- `python-dotenv`: Environment variable management
- `tabulate`: Table formatting (for future enhancements)

### Code Structure
- Object-oriented design with inheritance
- Separation of concerns (orders, utils, config)
- Type hints for better code clarity
- Comprehensive docstrings

## 🚨 Important Warnings

1. **TESTNET ONLY**: This bot is configured for testnet. DO NOT use mainnet credentials.
2. **API Security**: Never share your API keys or commit them to version control.
3. **Rate Limits**: Be aware of Binance API rate limits.
4. **Risk Management**: Always use stop-losses and proper position sizing.
5. **No Financial Advice**: This is educational software only.

## 🐛 Troubleshooting

### "API credentials not found"
- Ensure `.env` file exists
- Check that API keys are correctly set
- Verify no extra spaces in `.env` file

### "Invalid symbol"
- Use uppercase symbols (BTCUSDT, not btcusdt)
- Ensure symbol exists on Binance Futures
- Check for typos

### "Insufficient balance"
- This is testnet - request more test funds
- Check your testnet account balance
- Reduce order quantity

### Import errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+)
- Verify you're in the correct directory

## 📚 Resources

- [Binance Futures API Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- [Binance Futures Testnet](https://testnet.binancefuture.com/)
- [python-binance Documentation](https://python-binance.readthedocs.io/)

## 📄 License

This project is for educational purposes only. Use at your own risk.

## 👤 Author

[Your Name]
- GitHub: [@yourusername]
- Email: your.email@example.com
ADD .env file includes
BINANCE_API_KEY=
BINANCE_API_SECRET=

# Testnet Configuration
USE_TESTNET=True
TESTNET_BASE_URL=https://testnet.binancefuture.com


## 🙏 Acknowledgments

- Binance for providing the Futures API and Testnet
- python-binance library maintainers
- Open source community

---

**Remember**: This is testnet software for learning purposes. Always practice proper risk management and never invest more than you can afford to lose.
