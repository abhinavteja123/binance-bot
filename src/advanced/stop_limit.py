"""
Stop-Limit Order Implementation for Binance Futures
Places limit orders that trigger when a stop price is reached
"""
import sys
from typing import Dict, Any, Optional
from base_bot import BasicBot
from utils import BotLogger, Formatter, Validator
from binance.exceptions import BinanceAPIException

class StopLimitOrderBot(BasicBot):
    """Bot for executing stop-limit orders on Binance Futures"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.logger = BotLogger('StopLimitOrder')
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                              stop_price: float, limit_price: float,
                              time_in_force: str = 'GTC', position_side: str = 'BOTH',
                              reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a stop-limit order
        
        A stop-limit order will be placed as a limit order when the stop price is triggered.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            stop_price: Stop trigger price
            limit_price: Limit order price after trigger
            time_in_force: Time in force ('GTC', 'IOC', 'FOK', 'GTX')
            position_side: Position side ('BOTH', 'LONG', 'SHORT')
            reduce_only: If true, only reduces position
        
        Returns:
            Order response dictionary
        """
        # Validate parameters
        if not self.validate_order_params(symbol, side, quantity, limit_price):
            raise ValueError("Invalid order parameters")
        
        if not Validator.validate_price(stop_price):
            raise ValueError(f"Invalid stop price: {stop_price}")
        
        if not Validator.validate_time_in_force(time_in_force):
            raise ValueError(f"Invalid time in force: {time_in_force}")
        
        symbol = symbol.upper()
        side = side.upper()
        time_in_force = time_in_force.upper()
        position_side = position_side.upper()
        
        try:
            # Log the order attempt
            self.logger.info(f"Placing STOP_LIMIT {side} order: {quantity} {symbol} | Stop: {stop_price}, Limit: {limit_price}")
            
            # Place stop-limit order
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP',
                quantity=quantity,
                price=limit_price,
                stopPrice=stop_price,
                timeInForce=time_in_force,
                positionSide=position_side,
                reduceOnly=reduce_only
            )
            
            # Log successful order
            self.logger.log_order('STOP_LIMIT', {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'stopPrice': stop_price,
                'limitPrice': limit_price,
                'timeInForce': time_in_force,
                'orderId': order.get('orderId'),
                'status': order.get('status')
            })
            
            self.logger.info(f"Stop-limit order placed successfully. Order ID: {order.get('orderId')}")
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API Error: {e.status_code} - {e.message}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise
        except Exception as e:
            error_msg = f"Error placing stop-limit order: {str(e)}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise


def main():
    """CLI entry point for stop-limit orders"""
    Formatter.print_header("BINANCE FUTURES - STOP-LIMIT ORDER")
    
    # Parse command line arguments
    if len(sys.argv) < 6:
        print(f"Usage: python {sys.argv[0]} <SYMBOL> <SIDE> <QUANTITY> <STOP_PRICE> <LIMIT_PRICE> [TIME_IN_FORCE] [POSITION_SIDE]")
        print(f"Example: python {sys.argv[0]} BTCUSDT BUY 0.01 44000 44100")
        print(f"Example: python {sys.argv[0]} ETHUSDT SELL 0.1 2950 2940 GTC LONG")
        print(f"\nStop-Limit Order: Triggers a limit order when stop price is reached")
        sys.exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2]
    
    try:
        quantity = float(sys.argv[3])
        stop_price = float(sys.argv[4])
        limit_price = float(sys.argv[5])
    except ValueError:
        print(f"{Formatter.format_error(ValueError('Invalid quantity, stop price, or limit price. Must be numbers'))}")
        sys.exit(1)
    
    time_in_force = sys.argv[6] if len(sys.argv) > 6 else 'GTC'
    position_side = sys.argv[7] if len(sys.argv) > 7 else 'BOTH'
    
    try:
        # Initialize bot
        bot = StopLimitOrderBot(testnet=True)
        
        # Display current price
        current_price = bot.get_current_price(symbol)
        print(f"Current {symbol} price: {current_price}")
        
        # Validate stop-limit logic
        if side.upper() == 'BUY':
            if stop_price <= current_price:
                print(f"\n⚠ WARNING: For BUY stop-limit, stop price should be > current price")
        else:  # SELL
            if stop_price >= current_price:
                print(f"\n⚠ WARNING: For SELL stop-limit, stop price should be < current price")
        
        # Confirm order
        print(f"\nOrder Details:")
        print(f"  Symbol: {symbol}")
        print(f"  Side: {side}")
        print(f"  Quantity: {quantity}")
        print(f"  Stop Price: {stop_price} ({((stop_price - current_price) / current_price * 100):+.2f}% from current)")
        print(f"  Limit Price: {limit_price} ({((limit_price - current_price) / current_price * 100):+.2f}% from current)")
        print(f"  Time in Force: {time_in_force}")
        print(f"  Position Side: {position_side}")
        
        confirm = input("\nConfirm order? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("Order cancelled by user")
            sys.exit(0)
        
        # Place order
        order = bot.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price, time_in_force, position_side)
        
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
