"""
OCO (One-Cancels-the-Other) Order Implementation for Binance Futures
Places take-profit and stop-loss orders simultaneously
Note: Binance Futures doesn't support native OCO orders like Spot trading.
This implementation simulates OCO by placing both orders and monitoring them.
"""
import sys
import time
from typing import Dict, Any, Optional, Tuple
from base_bot import BasicBot
from utils import BotLogger, Formatter
from binance.exceptions import BinanceAPIException

class OCOOrderBot(BasicBot):
    """Bot for simulating OCO orders on Binance Futures"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.logger = BotLogger('OCOOrder')
    
    def place_oco_order(self, symbol: str, side: str, quantity: float,
                       take_profit_price: float, stop_loss_price: float,
                       position_side: str = 'BOTH') -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Place OCO (One-Cancels-the-Other) orders
        
        This places both a take-profit and stop-loss order. When one is filled,
        you should cancel the other manually or use monitoring.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            side: Original position side for closing ('BUY' or 'SELL')
                  - If closing a LONG position, use 'SELL'
                  - If closing a SHORT position, use 'BUY'
            quantity: Order quantity (should match position size)
            take_profit_price: Take profit limit price
            stop_loss_price: Stop loss trigger price
            position_side: Position side ('BOTH', 'LONG', 'SHORT')
        
        Returns:
            Tuple of (take_profit_order, stop_loss_order)
        """
        # Validate parameters
        if not self.validate_order_params(symbol, side, quantity, take_profit_price):
            raise ValueError("Invalid order parameters")
        
        symbol = symbol.upper()
        side = side.upper()
        position_side = position_side.upper()
        
        # Determine the correct order sides for closing position
        # If closing LONG (selling), TP should be SELL limit, SL should be SELL stop
        # If closing SHORT (buying), TP should be BUY limit, SL should be BUY stop
        
        try:
            current_price = self.get_current_price(symbol)
            
            self.logger.info(f"Placing OCO orders for {symbol}: TP={take_profit_price}, SL={stop_loss_price}")
            
            # Place Take Profit Limit Order
            tp_order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=take_profit_price,
                timeInForce='GTC',
                positionSide=position_side,
                reduceOnly=True  # Only reduce the position
            )
            
            self.logger.info(f"Take Profit order placed. Order ID: {tp_order.get('orderId')}")
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
            # Place Stop Loss Order (STOP_MARKET for guaranteed execution)
            sl_order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP_MARKET',
                quantity=quantity,
                stopPrice=stop_loss_price,
                positionSide=position_side,
                reduceOnly=True  # Only reduce the position
            )
            
            self.logger.info(f"Stop Loss order placed. Order ID: {sl_order.get('orderId')}")
            
            # Log OCO pair
            self.logger.log_order('OCO', {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'takeProfitPrice': take_profit_price,
                'stopLossPrice': stop_loss_price,
                'tpOrderId': tp_order.get('orderId'),
                'slOrderId': sl_order.get('orderId')
            })
            
            self.logger.info("OCO orders placed successfully")
            
            return tp_order, sl_order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API Error: {e.status_code} - {e.message}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise
        except Exception as e:
            error_msg = f"Error placing OCO orders: {str(e)}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise
    
    def monitor_and_cancel_oco(self, symbol: str, tp_order_id: int, sl_order_id: int, 
                               check_interval: int = 5, max_checks: int = 100) -> Optional[str]:
        """
        Monitor OCO orders and cancel the opposite when one fills
        
        Args:
            symbol: Trading pair symbol
            tp_order_id: Take profit order ID
            sl_order_id: Stop loss order ID
            check_interval: Seconds between checks
            max_checks: Maximum number of checks before stopping
        
        Returns:
            'TP' if take profit filled, 'SL' if stop loss filled, None if timeout
        """
        symbol = symbol.upper()
        checks = 0
        
        self.logger.info(f"Monitoring OCO orders for {symbol}")
        
        try:
            while checks < max_checks:
                # Get order statuses
                try:
                    tp_order = self.client.futures_get_order(symbol=symbol, orderId=tp_order_id)
                    sl_order = self.client.futures_get_order(symbol=symbol, orderId=sl_order_id)
                    
                    tp_status = tp_order.get('status')
                    sl_status = sl_order.get('status')
                    
                    # Check if TP filled
                    if tp_status == 'FILLED':
                        self.logger.info("Take Profit order filled! Cancelling Stop Loss...")
                        self.cancel_order(symbol, sl_order_id)
                        return 'TP'
                    
                    # Check if SL filled
                    if sl_status == 'FILLED':
                        self.logger.info("Stop Loss order triggered! Cancelling Take Profit...")
                        self.cancel_order(symbol, tp_order_id)
                        return 'SL'
                    
                    # Check if both are cancelled or expired
                    if tp_status in ['CANCELED', 'EXPIRED'] and sl_status in ['CANCELED', 'EXPIRED']:
                        self.logger.warning("Both OCO orders cancelled/expired")
                        return None
                    
                except BinanceAPIException as e:
                    self.logger.warning(f"Error checking order status: {e.message}")
                
                time.sleep(check_interval)
                checks += 1
            
            self.logger.warning(f"OCO monitoring timeout after {max_checks} checks")
            return None
            
        except Exception as e:
            self.logger.error(f"Error monitoring OCO orders: {str(e)}")
            raise


def main():
    """CLI entry point for OCO orders"""
    Formatter.print_header("BINANCE FUTURES - OCO ORDER (One-Cancels-the-Other)")
    
    # Parse command line arguments
    if len(sys.argv) < 6:
        print(f"Usage: python {sys.argv[0]} <SYMBOL> <SIDE> <QUANTITY> <TAKE_PROFIT_PRICE> <STOP_LOSS_PRICE> [POSITION_SIDE] [--monitor]")
        print(f"\nExample: python {sys.argv[0]} BTCUSDT SELL 0.01 46000 44000")
        print(f"         (Close LONG position with TP at 46000, SL at 44000)")
        print(f"\nExample: python {sys.argv[0]} ETHUSDT BUY 0.1 2900 3100 SHORT --monitor")
        print(f"         (Close SHORT position with TP at 2900, SL at 3100, and monitor)")
        print(f"\nNote: SIDE should be the closing direction (SELL for LONG, BUY for SHORT)")
        sys.exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2]
    
    try:
        quantity = float(sys.argv[3])
        take_profit_price = float(sys.argv[4])
        stop_loss_price = float(sys.argv[5])
    except ValueError:
        print(f"{Formatter.format_error(ValueError('Invalid quantity or prices. Must be numbers'))}")
        sys.exit(1)
    
    position_side = 'BOTH'
    monitor = False
    
    for i in range(6, len(sys.argv)):
        if sys.argv[i].upper() in ['BOTH', 'LONG', 'SHORT']:
            position_side = sys.argv[i]
        elif sys.argv[i] == '--monitor':
            monitor = True
    
    try:
        # Initialize bot
        bot = OCOOrderBot(testnet=True)
        
        # Display current price
        current_price = bot.get_current_price(symbol)
        print(f"Current {symbol} price: {current_price}")
        
        # Confirm order
        print(f"\nOCO Order Details:")
        print(f"  Symbol: {symbol}")
        print(f"  Closing Side: {side}")
        print(f"  Quantity: {quantity}")
        print(f"  Take Profit: {take_profit_price} ({((take_profit_price - current_price) / current_price * 100):+.2f}% from current)")
        print(f"  Stop Loss: {stop_loss_price} ({((stop_loss_price - current_price) / current_price * 100):+.2f}% from current)")
        print(f"  Position Side: {position_side}")
        print(f"  Monitor Mode: {'Enabled' if monitor else 'Disabled'}")
        
        confirm = input("\nConfirm OCO orders? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("Order cancelled by user")
            sys.exit(0)
        
        # Place OCO orders
        tp_order, sl_order = bot.place_oco_order(symbol, side, quantity, take_profit_price, stop_loss_price, position_side)
        
        # Display results
        print(f"\n{Formatter.format_order_response(tp_order)}")
        print(f"\n{Formatter.format_order_response(sl_order)}")
        
        print(f"\n✓ OCO Orders Placed Successfully!")
        print(f"  Take Profit Order ID: {tp_order.get('orderId')}")
        print(f"  Stop Loss Order ID: {sl_order.get('orderId')}")
        
        # Monitor if requested
        if monitor:
            print(f"\nMonitoring OCO orders (Press Ctrl+C to stop)...")
            result = bot.monitor_and_cancel_oco(symbol, tp_order.get('orderId'), sl_order.get('orderId'))
            if result == 'TP':
                print(f"\n✓ Take Profit executed! Stop Loss cancelled.")
            elif result == 'SL':
                print(f"\n✓ Stop Loss triggered! Take Profit cancelled.")
            else:
                print(f"\n⚠ Monitoring ended. Please manually manage orders.")
        else:
            print(f"\n⚠ Remember to manually cancel the other order when one fills!")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(Formatter.format_error(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
