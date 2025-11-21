"""
Base Bot class for Binance Futures Trading
Handles API connection and common operations
"""
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from typing import Dict, Any, Optional
from config import Config
from utils import BotLogger, Validator

class BasicBot:
    """Base trading bot class with Binance API integration"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        """
        Initialize the bot
        
        Args:
            api_key: Binance API key (defaults to Config.API_KEY)
            api_secret: Binance API secret (defaults to Config.API_SECRET)
            testnet: Whether to use testnet (default: True)
        """
        self.api_key = api_key or Config.API_KEY
        self.api_secret = api_secret or Config.API_SECRET
        self.testnet = testnet
        self.logger = BotLogger('BasicBot')
        
        # Validate credentials
        if not self.api_key or not self.api_secret:
            raise ValueError("API credentials are required")
        
        # Initialize Binance client
        try:
            self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
            if self.testnet:
                self.client.API_URL = 'https://testnet.binancefuture.com'
            
            self.logger.info(f"Bot initialized {'(TESTNET)' if testnet else '(MAINNET)'}")
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {str(e)}")
            raise
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information"""
        try:
            info = self.client.futures_exchange_info()
            self.logger.debug("Retrieved exchange info")
            return info
        except BinanceAPIException as e:
            self.logger.error(f"API Error getting exchange info: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting exchange info: {e}")
            raise
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get information for a specific symbol"""
        try:
            exchange_info = self.get_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol.upper():
                    return s
            self.logger.warning(f"Symbol {symbol} not found")
            return None
        except Exception as e:
            self.logger.error(f"Error getting symbol info: {e}")
            return None
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            info = self.client.futures_account()
            self.logger.debug("Retrieved account info")
            return info
        except BinanceAPIException as e:
            self.logger.error(f"API Error getting account info: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            # Validate symbol first
            if not Validator.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol '{symbol}'. Must be uppercase and end with 'USDT' (e.g., BTCUSDT, ETHUSDT)")
            
            ticker = self.client.futures_symbol_ticker(symbol=symbol.upper())
            price = float(ticker['price'])
            self.logger.debug(f"Current price for {symbol}: {price}")
            return price
        except BinanceAPIException as e:
            if e.code == -1121:
                self.logger.error(f"Invalid symbol '{symbol}'. Use format like BTCUSDT, ETHUSDT, BNBUSDT")
                raise ValueError(f"Invalid symbol '{symbol}'. Use full symbol name like BTCUSDT, ETHUSDT, etc.")
            self.logger.error(f"API Error getting price for {symbol}: {e}")
            raise
        except ValueError as e:
            self.logger.error(str(e))
            raise
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for a symbol"""
        try:
            if leverage < 1 or leverage > Config.MAX_LEVERAGE:
                raise ValueError(f"Leverage must be between 1 and {Config.MAX_LEVERAGE}")
            
            result = self.client.futures_change_leverage(symbol=symbol.upper(), leverage=leverage)
            self.logger.info(f"Set leverage to {leverage}x for {symbol}")
            return result
        except BinanceAPIException as e:
            self.logger.error(f"API Error setting leverage: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error setting leverage: {e}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Get all open orders"""
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol.upper())
            else:
                orders = self.client.futures_get_open_orders()
            self.logger.debug(f"Retrieved {len(orders)} open orders")
            return orders
        except BinanceAPIException as e:
            self.logger.error(f"API Error getting open orders: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting open orders: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order"""
        try:
            result = self.client.futures_cancel_order(symbol=symbol.upper(), orderId=order_id)
            self.logger.info(f"Cancelled order {order_id} for {symbol}")
            return result
        except BinanceAPIException as e:
            self.logger.error(f"API Error cancelling order: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            raise
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """Cancel all open orders for a symbol"""
        try:
            result = self.client.futures_cancel_all_open_orders(symbol=symbol.upper())
            self.logger.info(f"Cancelled all orders for {symbol}")
            return result
        except BinanceAPIException as e:
            self.logger.error(f"API Error cancelling all orders: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error cancelling all orders: {e}")
            raise
    
    def validate_order_params(self, symbol: str, side: str, quantity: float, price: Optional[float] = None) -> bool:
        """Validate order parameters"""
        if not Validator.validate_symbol(symbol):
            self.logger.error(f"Invalid symbol: {symbol}")
            return False
        
        if not Validator.validate_side(side):
            self.logger.error(f"Invalid side: {side}. Must be BUY or SELL")
            return False
        
        if not Validator.validate_quantity(quantity):
            self.logger.error(f"Invalid quantity: {quantity}. Must be >= {Config.MIN_QUANTITY}")
            return False
        
        if price is not None and not Validator.validate_price(price):
            self.logger.error(f"Invalid price: {price}. Must be >= {Config.MIN_PRICE}")
            return False
        
        return True
