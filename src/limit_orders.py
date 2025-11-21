"""
Limit Order Implementation for Binance Futures
Places orders at specified price levels
"""
import sys
from typing import Dict, Any, Optional
from base_bot import BasicBot
from utils import BotLogger, Formatter, Validator
from binance.exceptions import BinanceAPIException

class LimitOrderBot(BasicBot):
    """Bot for executing limit orders on Binance Futures"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.logger = BotLogger('LimitOrder')
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                         time_in_force: str = 'GTC', position_side: str = 'BOTH',
                         reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force ('GTC', 'IOC', 'FOK', 'GTX')
            position_side: Position side ('BOTH', 'LONG', 'SHORT') for hedge mode
            reduce_only: If true, only reduces position
        
        Returns:
            Order response dictionary
        """
        # Validate parameters
        if not self.validate_order_params(symbol, side, quantity, price):
            raise ValueError("Invalid order parameters")
        
        if not Validator.validate_time_in_force(time_in_force):
            raise ValueError(f"Invalid time in force: {time_in_force}")
        
        symbol = symbol.upper()
        side = side.upper()
        time_in_force = time_in_force.upper()
        position_side = position_side.upper()
        
        try:
            # Log the order attempt
            self.logger.info(f"Placing LIMIT {side} order: {quantity} {symbol} @ {price}")
            
            # Place limit order
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce=time_in_force,
                positionSide=position_side,
                reduceOnly=reduce_only
            )
            
            # Log successful order
            self.logger.log_order('LIMIT', {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'timeInForce': time_in_force,
                'orderId': order.get('orderId'),
                'status': order.get('status')
            })
            
            self.logger.info(f"Limit order placed successfully. Order ID: {order.get('orderId')}")
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API Error: {e.status_code} - {e.message}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise
        except Exception as e:
            error_msg = f"Error placing limit order: {str(e)}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise
    
    def place_limit_buy(self, symbol: str, quantity: float, price: float) -> Dict[str, Any]:
        """Convenience method for limit buy orders"""
        return self.place_limit_order(symbol, 'BUY', quantity, price)
    
    def place_limit_sell(self, symbol: str, quantity: float, price: float) -> Dict[str, Any]:
        """Convenience method for limit sell orders"""
        return self.place_limit_order(symbol, 'SELL', quantity, price)


def main():
    """CLI entry point for limit orders"""
    Formatter.print_header("BINANCE FUTURES - LIMIT ORDER")
    
    # Parse command line arguments
    if len(sys.argv) < 5:
        print(f"Usage: python {sys.argv[0]} <SYMBOL> <SIDE> <QUANTITY> <PRICE> [TIME_IN_FORCE] [POSITION_SIDE]")
        print(f"Example: python {sys.argv[0]} BTCUSDT BUY 0.01 45000")
        print(f"Example: python {sys.argv[0]} ETHUSDT SELL 0.1 3000 GTC LONG")
        print(f"\nTime in Force options: GTC (Good Till Cancel), IOC (Immediate or Cancel), FOK (Fill or Kill), GTX (Good Till Crossing)")
        sys.exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2]
    
    try:
        quantity = float(sys.argv[3])
        price = float(sys.argv[4])
    except ValueError:
        print(f"{Formatter.format_error(ValueError('Invalid quantity or price. Must be numbers'))}")
        sys.exit(1)
    
    time_in_force = sys.argv[5] if len(sys.argv) > 5 else 'GTC'
    position_side = sys.argv[6] if len(sys.argv) > 6 else 'BOTH'
    
    try:
        # Initialize bot
        bot = LimitOrderBot(testnet=True)
        
        # Display current price
        current_price = bot.get_current_price(symbol)
        print(f"Current {symbol} price: {current_price}")
        
        # Calculate price difference
        price_diff_pct = ((price - current_price) / current_price) * 100
        print(f"Your limit price is {price_diff_pct:+.2f}% from current price")
        
        # Confirm order
        estimated_value = quantity * price
        print(f"\nOrder Details:")
        print(f"  Symbol: {symbol}")
        print(f"  Side: {side}")
        print(f"  Quantity: {quantity}")
        print(f"  Limit Price: {price}")
        print(f"  Time in Force: {time_in_force}")
        print(f"  Position Side: {position_side}")
        print(f"  Order Value: {estimated_value:.2f} USDT")
        
        confirm = input("\nConfirm order? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("Order cancelled by user")
            sys.exit(0)
        
        # Place order
        order = bot.place_limit_order(symbol, side, quantity, price, time_in_force, position_side)
        
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
