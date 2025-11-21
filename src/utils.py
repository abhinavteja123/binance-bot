"""
Utility functions for the Binance Futures Trading Bot
Includes logging, validation, and helper functions
"""
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from colorama import init, Fore, Style
from config import Config

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class BotLogger:
    """Custom logger for the trading bot"""
    
    def __init__(self, name: str = 'BinanceBot'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(Config.LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(Config.LOG_FORMAT, Config.LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
        print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
        print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def log_order(self, order_type: str, details: Dict[str, Any]):
        """Log order details"""
        log_msg = f"{order_type} Order - {details}"
        self.logger.info(log_msg)
    
    def log_api_call(self, endpoint: str, params: Dict[str, Any], response: Any):
        """Log API call details"""
        log_msg = f"API Call - Endpoint: {endpoint}, Params: {params}, Response: {response}"
        self.logger.debug(log_msg)
    
    def log_error_trace(self, error: Exception):
        """Log error with trace"""
        self.logger.exception(f"Error occurred: {str(error)}")


class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate trading symbol format"""
        if not symbol:
            return False
        # Basic validation - should end with USDT for USDT-M futures
        if not symbol.isupper():
            return False
        if len(symbol) < 5:
            return False
        # Must end with USDT for USDT-M futures
        if not symbol.endswith('USDT'):
            return False
        return True
    
    @staticmethod
    def validate_side(side: str) -> bool:
        """Validate order side"""
        return side.upper() in ['BUY', 'SELL']
    
    @staticmethod
    def validate_quantity(quantity: float) -> bool:
        """Validate order quantity"""
        try:
            qty = float(quantity)
            return qty >= Config.MIN_QUANTITY
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_price(price: float) -> bool:
        """Validate price"""
        try:
            p = float(price)
            return p >= Config.MIN_PRICE
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_order_type(order_type: str) -> bool:
        """Validate order type"""
        valid_types = ['MARKET', 'LIMIT', 'STOP', 'STOP_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_MARKET', 'TRAILING_STOP_MARKET']
        return order_type.upper() in valid_types
    
    @staticmethod
    def validate_time_in_force(tif: str) -> bool:
        """Validate time in force"""
        valid_tif = ['GTC', 'IOC', 'FOK', 'GTX']
        return tif.upper() in valid_tif


class Formatter:
    """Output formatting utilities"""
    
    @staticmethod
    def format_order_response(response: Dict[str, Any]) -> str:
        """Format order response for display"""
        if not response:
            return "No response data"
        
        output = "\n" + "="*60 + "\n"
        output += f"{Fore.CYAN}ORDER DETAILS{Style.RESET_ALL}\n"
        output += "="*60 + "\n"
        
        fields = [
            ('Symbol', 'symbol'),
            ('Order ID', 'orderId'),
            ('Client Order ID', 'clientOrderId'),
            ('Side', 'side'),
            ('Type', 'type'),
            ('Position Side', 'positionSide'),
            ('Quantity', 'origQty'),
            ('Price', 'price'),
            ('Stop Price', 'stopPrice'),
            ('Status', 'status'),
            ('Time in Force', 'timeInForce'),
            ('Update Time', 'updateTime'),
        ]
        
        for label, key in fields:
            if key in response and response[key]:
                value = response[key]
                if key == 'updateTime':
                    value = datetime.fromtimestamp(value/1000).strftime('%Y-%m-%d %H:%M:%S')
                output += f"{label}: {Fore.YELLOW}{value}{Style.RESET_ALL}\n"
        
        output += "="*60 + "\n"
        return output
    
    @staticmethod
    def format_error(error: Exception) -> str:
        """Format error message"""
        return f"{Fore.RED}Error: {str(error)}{Style.RESET_ALL}"
    
    @staticmethod
    def print_header(text: str):
        """Print formatted header"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{text.center(60)}")
        print(f"{'='*60}{Style.RESET_ALL}\n")


def parse_float(value: str, default: float = 0.0) -> float:
    """Safely parse float from string"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_int(value: str, default: int = 0) -> int:
    """Safely parse int from string"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_timestamp() -> int:
    """Get current timestamp in milliseconds"""
    return int(datetime.now().timestamp() * 1000)
