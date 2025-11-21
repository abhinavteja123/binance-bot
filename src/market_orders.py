"""
Market Order Implementation for Binance Futures
Executes immediate buy/sell orders at current market price
"""
import sys
from typing import Dict, Any, Optional
from base_bot import BasicBot
from utils import BotLogger, Formatter
from binance.exceptions import BinanceAPIException

class MarketOrderBot(BasicBot):
    """Bot for executing market orders on Binance Futures"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.logger = BotLogger('MarketOrder')
    
    def place_market_order(self, symbol: str, side: str, quantity: float, 
                          position_side: str = 'BOTH', reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a market order
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            position_side: Position side ('BOTH', 'LONG', 'SHORT') for hedge mode
            reduce_only: If true, only reduces position (doesn't open new)
        
        Returns:
            Order response dictionary
        """
        # Validate parameters
        if not self.validate_order_params(symbol, side, quantity):
            raise ValueError("Invalid order parameters")
        
        symbol = symbol.upper()
        side = side.upper()
        position_side = position_side.upper()
        
        try:
            # Log the order attempt
            self.logger.info(f"Placing MARKET {side} order: {quantity} {symbol}")
            
            # Place market order
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity,
                positionSide=position_side,
                reduceOnly=reduce_only
            )
            
            # Log successful order
            self.logger.log_order('MARKET', {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'orderId': order.get('orderId'),
                'status': order.get('status')
            })
            
            self.logger.info(f"Market order placed successfully. Order ID: {order.get('orderId')}")
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API Error: {e.status_code} - {e.message}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise
        except Exception as e:
            error_msg = f"Error placing market order: {str(e)}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise
    
    def place_market_buy(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Convenience method for market buy orders"""
        return self.place_market_order(symbol, 'BUY', quantity)
    
    def place_market_sell(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Convenience method for market sell orders"""
        return self.place_market_order(symbol, 'SELL', quantity)


def main():
    """CLI entry point for market orders"""
    Formatter.print_header("BINANCE FUTURES - MARKET ORDER")
    
    # Parse command line arguments
    if len(sys.argv) < 4:
        print(f"Usage: python {sys.argv[0]} <SYMBOL> <SIDE> <QUANTITY> [POSITION_SIDE]")
        print(f"Example: python {sys.argv[0]} BTCUSDT BUY 0.01")
        print(f"Example: python {sys.argv[0]} ETHUSDT SELL 0.1 LONG")
        sys.exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2]
    
    try:
        quantity = float(sys.argv[3])
    except ValueError:
        print(f"{Formatter.format_error(ValueError('Invalid quantity. Must be a number'))}")
        sys.exit(1)
    
    position_side = sys.argv[4] if len(sys.argv) > 4 else 'BOTH'
    
    try:
        # Initialize bot
        bot = MarketOrderBot(testnet=True)
        
        # Display current price
        current_price = bot.get_current_price(symbol)
        print(f"Current {symbol} price: {current_price}")
        
        # Confirm order
        estimated_value = quantity * current_price
        print(f"\nOrder Details:")
        print(f"  Symbol: {symbol}")
        print(f"  Side: {side}")
        print(f"  Quantity: {quantity}")
        print(f"  Position Side: {position_side}")
        print(f"  Estimated Value: ~{estimated_value:.2f} USDT")
        
        confirm = input("\nConfirm order? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("Order cancelled by user")
            sys.exit(0)
        
        # Place order
        order = bot.place_market_order(symbol, side, quantity, position_side)
        
        # Display results
        print(Formatter.format_order_response(order))
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(Formatter.format_error(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
