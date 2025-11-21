"""
TWAP (Time-Weighted Average Price) Strategy Implementation
Splits large orders into smaller chunks executed over time to minimize market impact
"""
import sys
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from base_bot import BasicBot
from utils import BotLogger, Formatter
from binance.exceptions import BinanceAPIException

class TWAPBot(BasicBot):
    """Bot for executing TWAP strategy on Binance Futures"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.logger = BotLogger('TWAP')
    
    def execute_twap(self, symbol: str, side: str, total_quantity: float,
                    duration_minutes: int, num_orders: int,
                    position_side: str = 'BOTH', use_limit: bool = False,
                    limit_offset_pct: float = 0.1) -> List[Dict[str, Any]]:
        """
        Execute TWAP strategy
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            total_quantity: Total quantity to trade
            duration_minutes: Total duration in minutes to spread orders
            num_orders: Number of orders to split into
            position_side: Position side ('BOTH', 'LONG', 'SHORT')
            use_limit: If True, use limit orders instead of market
            limit_offset_pct: Price offset percentage for limit orders
        
        Returns:
            List of executed order responses
        """
        # Validate parameters
        if not self.validate_order_params(symbol, side, total_quantity):
            raise ValueError("Invalid order parameters")
        
        if num_orders < 1:
            raise ValueError("Number of orders must be at least 1")
        
        if duration_minutes < 1:
            raise ValueError("Duration must be at least 1 minute")
        
        symbol = symbol.upper()
        side = side.upper()
        position_side = position_side.upper()
        
        # Calculate order parameters
        order_size = total_quantity / num_orders
        interval_seconds = (duration_minutes * 60) / num_orders
        
        self.logger.info(f"Starting TWAP execution for {symbol}")
        self.logger.info(f"Total quantity: {total_quantity}, Orders: {num_orders}, Duration: {duration_minutes}min")
        self.logger.info(f"Order size: {order_size}, Interval: {interval_seconds:.1f}s")
        
        executed_orders = []
        start_time = datetime.now()
        
        try:
            for i in range(num_orders):
                order_num = i + 1
                
                try:
                    # Get current price
                    current_price = self.get_current_price(symbol)
                    
                    # Place order
                    if use_limit:
                        # Calculate limit price with offset
                        if side == 'BUY':
                            # For buy, place slightly above current price
                            limit_price = current_price * (1 + limit_offset_pct / 100)
                        else:
                            # For sell, place slightly below current price
                            limit_price = current_price * (1 - limit_offset_pct / 100)
                        
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side=side,
                            type='LIMIT',
                            quantity=order_size,
                            price=round(limit_price, 2),
                            timeInForce='GTC',
                            positionSide=position_side
                        )
                        order_type = 'LIMIT'
                    else:
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side=side,
                            type='MARKET',
                            quantity=order_size,
                            positionSide=position_side
                        )
                        order_type = 'MARKET'
                    
                    executed_orders.append(order)
                    
                    # Log order
                    self.logger.info(f"TWAP Order {order_num}/{num_orders} executed: {order_type} {side} {order_size} @ {current_price}")
                    self.logger.log_order(f'TWAP_{order_type}', {
                        'orderNumber': order_num,
                        'symbol': symbol,
                        'side': side,
                        'quantity': order_size,
                        'price': current_price,
                        'orderId': order.get('orderId')
                    })
                    
                except BinanceAPIException as e:
                    error_msg = f"Error placing TWAP order {order_num}: {e.message}"
                    self.logger.error(error_msg)
                    # Continue with remaining orders
                    continue
                
                # Wait for next interval (except for last order)
                if i < num_orders - 1:
                    self.logger.debug(f"Waiting {interval_seconds:.1f}s for next order...")
                    time.sleep(interval_seconds)
            
            # Summary
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            total_executed = sum(float(order.get('executedQty', 0)) for order in executed_orders)
            avg_price = sum(float(order.get('avgPrice', 0)) * float(order.get('executedQty', 0)) 
                          for order in executed_orders if order.get('avgPrice')) / total_executed if total_executed > 0 else 0
            
            self.logger.info(f"TWAP execution completed")
            self.logger.info(f"Orders placed: {len(executed_orders)}/{num_orders}")
            self.logger.info(f"Total executed: {total_executed}/{total_quantity}")
            self.logger.info(f"Average price: {avg_price:.2f}")
            self.logger.info(f"Time elapsed: {elapsed:.1f}s")
            
            return executed_orders
            
        except Exception as e:
            error_msg = f"Error during TWAP execution: {str(e)}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise
    
    def get_twap_summary(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for TWAP execution"""
        if not orders:
            return {}
        
        total_qty = sum(float(order.get('executedQty', 0)) for order in orders)
        total_value = sum(float(order.get('avgPrice', 0)) * float(order.get('executedQty', 0)) 
                         for order in orders if order.get('avgPrice'))
        avg_price = total_value / total_qty if total_qty > 0 else 0
        
        prices = [float(order.get('avgPrice', 0)) for order in orders if order.get('avgPrice')]
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        return {
            'total_orders': len(orders),
            'total_quantity': total_qty,
            'average_price': avg_price,
            'min_price': min_price,
            'max_price': max_price,
            'price_range_pct': ((max_price - min_price) / avg_price * 100) if avg_price > 0 else 0
        }


def main():
    """CLI entry point for TWAP strategy"""
    Formatter.print_header("BINANCE FUTURES - TWAP STRATEGY")
    
    # Parse command line arguments
    if len(sys.argv) < 6:
        print(f"Usage: python {sys.argv[0]} <SYMBOL> <SIDE> <TOTAL_QUANTITY> <DURATION_MINUTES> <NUM_ORDERS> [POSITION_SIDE] [--limit] [--offset PCT]")
        print(f"\nExample (Market orders): python {sys.argv[0]} BTCUSDT BUY 0.1 10 5")
        print(f"         (Buy 0.1 BTC over 10 minutes in 5 market orders)")
        print(f"\nExample (Limit orders): python {sys.argv[0]} ETHUSDT SELL 1.0 30 10 LONG --limit --offset 0.2")
        print(f"         (Sell 1 ETH over 30 minutes in 10 limit orders with 0.2% price offset)")
        sys.exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2]
    
    try:
        total_quantity = float(sys.argv[3])
        duration_minutes = int(sys.argv[4])
        num_orders = int(sys.argv[5])
    except ValueError:
        print(f"{Formatter.format_error(ValueError('Invalid parameters. Check quantity, duration, and num_orders'))}")
        sys.exit(1)
    
    position_side = 'BOTH'
    use_limit = False
    limit_offset_pct = 0.1
    
    i = 6
    while i < len(sys.argv):
        if sys.argv[i].upper() in ['BOTH', 'LONG', 'SHORT']:
            position_side = sys.argv[i]
        elif sys.argv[i] == '--limit':
            use_limit = True
        elif sys.argv[i] == '--offset' and i + 1 < len(sys.argv):
            try:
                limit_offset_pct = float(sys.argv[i + 1])
                i += 1
            except ValueError:
                pass
        i += 1
    
    try:
        # Initialize bot
        bot = TWAPBot(testnet=True)
        
        # Display current price
        current_price = bot.get_current_price(symbol)
        print(f"Current {symbol} price: {current_price}")
        
        # Calculate parameters
        order_size = total_quantity / num_orders
        interval_seconds = (duration_minutes * 60) / num_orders
        estimated_value = total_quantity * current_price
        
        # Confirm strategy
        print(f"\nTWAP Strategy Details:")
        print(f"  Symbol: {symbol}")
        print(f"  Side: {side}")
        print(f"  Total Quantity: {total_quantity}")
        print(f"  Order Type: {'LIMIT' if use_limit else 'MARKET'}")
        if use_limit:
            print(f"  Limit Offset: {limit_offset_pct}%")
        print(f"  Duration: {duration_minutes} minutes")
        print(f"  Number of Orders: {num_orders}")
        print(f"  Order Size: {order_size:.8f}")
        print(f"  Interval: {interval_seconds:.1f} seconds")
        print(f"  Position Side: {position_side}")
        print(f"  Estimated Value: ~{estimated_value:.2f} USDT")
        
        confirm = input("\nStart TWAP execution? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("TWAP execution cancelled by user")
            sys.exit(0)
        
        print(f"\n{'='*60}")
        print(f"Starting TWAP execution... (This will take {duration_minutes} minutes)")
        print(f"{'='*60}\n")
        
        # Execute TWAP
        orders = bot.execute_twap(symbol, side, total_quantity, duration_minutes, num_orders,
                                 position_side, use_limit, limit_offset_pct)
        
        # Display summary
        summary = bot.get_twap_summary(orders)
        
        print(f"\n{'='*60}")
        print(f"TWAP EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Orders Executed: {summary.get('total_orders', 0)}/{num_orders}")
        print(f"Total Quantity: {summary.get('total_quantity', 0):.8f}")
        print(f"Average Price: {summary.get('average_price', 0):.2f}")
        print(f"Price Range: {summary.get('min_price', 0):.2f} - {summary.get('max_price', 0):.2f}")
        print(f"Price Variance: {summary.get('price_range_pct', 0):.2f}%")
        print(f"{'='*60}\n")
        
    except KeyboardInterrupt:
        print("\n\nTWAP execution interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(Formatter.format_error(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
