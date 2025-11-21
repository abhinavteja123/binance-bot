"""
Grid Trading Strategy Implementation for Binance Futures
Automated buy-low/sell-high within a price range
Places multiple buy and sell limit orders at different price levels
"""
import sys
import time
from typing import Dict, Any, Optional, List, Tuple
from base_bot import BasicBot
from utils import BotLogger, Formatter
from binance.exceptions import BinanceAPIException

class GridBot(BasicBot):
    """Bot for executing grid trading strategy on Binance Futures"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.logger = BotLogger('GridTrading')
    
    def create_grid_orders(self, symbol: str, lower_price: float, upper_price: float,
                          grid_levels: int, quantity_per_grid: float,
                          position_side: str = 'BOTH') -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Create grid trading orders
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            lower_price: Lower bound of price range
            upper_price: Upper bound of price range
            grid_levels: Number of grid levels
            quantity_per_grid: Quantity for each grid order
            position_side: Position side ('BOTH', 'LONG', 'SHORT')
        
        Returns:
            Tuple of (buy_orders, sell_orders)
        """
        # Validate parameters
        if lower_price >= upper_price:
            raise ValueError("Lower price must be less than upper price")
        
        if grid_levels < 2:
            raise ValueError("Grid levels must be at least 2")
        
        if not self.validate_order_params(symbol, 'BUY', quantity_per_grid, lower_price):
            raise ValueError("Invalid order parameters")
        
        symbol = symbol.upper()
        position_side = position_side.upper()
        
        # Calculate grid parameters
        price_range = upper_price - lower_price
        grid_step = price_range / (grid_levels - 1)
        
        current_price = self.get_current_price(symbol)
        
        self.logger.info(f"Creating grid for {symbol}")
        self.logger.info(f"Price range: {lower_price} - {upper_price}")
        self.logger.info(f"Grid levels: {grid_levels}, Step: {grid_step:.2f}")
        self.logger.info(f"Current price: {current_price}")
        
        buy_orders = []
        sell_orders = []
        
        try:
            # Create buy and sell orders at each grid level
            for i in range(grid_levels):
                grid_price = lower_price + (i * grid_step)
                grid_price = round(grid_price, 2)
                
                # Place buy orders below current price
                if grid_price < current_price:
                    try:
                        buy_order = self.client.futures_create_order(
                            symbol=symbol,
                            side='BUY',
                            type='LIMIT',
                            quantity=quantity_per_grid,
                            price=grid_price,
                            timeInForce='GTC',
                            positionSide=position_side
                        )
                        buy_orders.append(buy_order)
                        self.logger.info(f"Grid BUY order placed at {grid_price}")
                        time.sleep(0.1)  # Rate limiting
                    except BinanceAPIException as e:
                        self.logger.warning(f"Failed to place BUY order at {grid_price}: {e.message}")
                
                # Place sell orders above current price
                elif grid_price > current_price:
                    try:
                        sell_order = self.client.futures_create_order(
                            symbol=symbol,
                            side='SELL',
                            type='LIMIT',
                            quantity=quantity_per_grid,
                            price=grid_price,
                            timeInForce='GTC',
                            positionSide=position_side
                        )
                        sell_orders.append(sell_order)
                        self.logger.info(f"Grid SELL order placed at {grid_price}")
                        time.sleep(0.1)  # Rate limiting
                    except BinanceAPIException as e:
                        self.logger.warning(f"Failed to place SELL order at {grid_price}: {e.message}")
            
            # Log summary
            self.logger.log_order('GRID', {
                'symbol': symbol,
                'lowerPrice': lower_price,
                'upperPrice': upper_price,
                'gridLevels': grid_levels,
                'buyOrders': len(buy_orders),
                'sellOrders': len(sell_orders),
                'quantityPerGrid': quantity_per_grid
            })
            
            self.logger.info(f"Grid created: {len(buy_orders)} BUY orders, {len(sell_orders)} SELL orders")
            
            return buy_orders, sell_orders
            
        except Exception as e:
            error_msg = f"Error creating grid orders: {str(e)}"
            self.logger.error(error_msg)
            self.logger.log_error_trace(e)
            raise
    
    def monitor_and_rebalance_grid(self, symbol: str, lower_price: float, upper_price: float,
                                   grid_levels: int, quantity_per_grid: float,
                                   check_interval: int = 30, max_iterations: int = 100) -> None:
        """
        Monitor grid and replace filled orders
        
        Args:
            symbol: Trading pair symbol
            lower_price: Lower bound of price range
            upper_price: Upper bound of price range
            grid_levels: Number of grid levels
            quantity_per_grid: Quantity for each grid order
            check_interval: Seconds between checks
            max_iterations: Maximum monitoring iterations
        """
        symbol = symbol.upper()
        iteration = 0
        
        self.logger.info(f"Starting grid monitoring for {symbol}")
        
        try:
            while iteration < max_iterations:
                iteration += 1
                
                # Get current price
                current_price = self.get_current_price(symbol)
                
                # Get open orders
                open_orders = self.get_open_orders(symbol)
                open_buy_orders = [o for o in open_orders if o['side'] == 'BUY']
                open_sell_orders = [o for o in open_orders if o['side'] == 'SELL']
                
                self.logger.debug(f"Iteration {iteration}: Price={current_price}, Open BUY={len(open_buy_orders)}, Open SELL={len(open_sell_orders)}")
                
                # Calculate expected grid prices
                grid_step = (upper_price - lower_price) / (grid_levels - 1)
                expected_buy_prices = set()
                expected_sell_prices = set()
                
                for i in range(grid_levels):
                    grid_price = round(lower_price + (i * grid_step), 2)
                    if grid_price < current_price:
                        expected_buy_prices.add(grid_price)
                    elif grid_price > current_price:
                        expected_sell_prices.add(grid_price)
                
                # Check for missing buy orders
                open_buy_prices = {round(float(o['price']), 2) for o in open_buy_orders}
                missing_buy_prices = expected_buy_prices - open_buy_prices
                
                for price in missing_buy_prices:
                    try:
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side='BUY',
                            type='LIMIT',
                            quantity=quantity_per_grid,
                            price=price,
                            timeInForce='GTC',
                            positionSide='BOTH'
                        )
                        self.logger.info(f"Replaced BUY grid order at {price}")
                        time.sleep(0.1)
                    except BinanceAPIException as e:
                        self.logger.warning(f"Failed to replace BUY order at {price}: {e.message}")
                
                # Check for missing sell orders
                open_sell_prices = {round(float(o['price']), 2) for o in open_sell_orders}
                missing_sell_prices = expected_sell_prices - open_sell_prices
                
                for price in missing_sell_prices:
                    try:
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side='SELL',
                            type='LIMIT',
                            quantity=quantity_per_grid,
                            price=price,
                            timeInForce='GTC',
                            positionSide='BOTH'
                        )
                        self.logger.info(f"Replaced SELL grid order at {price}")
                        time.sleep(0.1)
                    except BinanceAPIException as e:
                        self.logger.warning(f"Failed to replace SELL order at {price}: {e.message}")
                
                # Wait before next check
                time.sleep(check_interval)
            
            self.logger.info(f"Grid monitoring completed after {max_iterations} iterations")
            
        except KeyboardInterrupt:
            self.logger.info("Grid monitoring stopped by user")
            raise
        except Exception as e:
            self.logger.error(f"Error during grid monitoring: {str(e)}")
            raise


def main():
    """CLI entry point for grid trading"""
    Formatter.print_header("BINANCE FUTURES - GRID TRADING STRATEGY")
    
    # Parse command line arguments
    if len(sys.argv) < 6:
        print(f"Usage: python {sys.argv[0]} <SYMBOL> <LOWER_PRICE> <UPPER_PRICE> <GRID_LEVELS> <QUANTITY_PER_GRID> [POSITION_SIDE] [--monitor] [--interval SEC]")
        print(f"\nExample: python {sys.argv[0]} BTCUSDT 44000 46000 10 0.01")
        print(f"         (Create 10 grid levels between 44000-46000, 0.01 BTC per grid)")
        print(f"\nExample: python {sys.argv[0]} ETHUSDT 2900 3100 20 0.1 BOTH --monitor --interval 60")
        print(f"         (Create 20 grid levels and monitor with 60s interval)")
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    try:
        lower_price = float(sys.argv[2])
        upper_price = float(sys.argv[3])
        grid_levels = int(sys.argv[4])
        quantity_per_grid = float(sys.argv[5])
    except ValueError:
        print(f"{Formatter.format_error(ValueError('Invalid parameters. Check prices, grid levels, and quantity'))}")
        sys.exit(1)
    
    position_side = 'BOTH'
    monitor = False
    check_interval = 30
    
    i = 6
    while i < len(sys.argv):
        if sys.argv[i].upper() in ['BOTH', 'LONG', 'SHORT']:
            position_side = sys.argv[i]
        elif sys.argv[i] == '--monitor':
            monitor = True
        elif sys.argv[i] == '--interval' and i + 1 < len(sys.argv):
            try:
                check_interval = int(sys.argv[i + 1])
                i += 1
            except ValueError:
                pass
        i += 1
    
    try:
        # Initialize bot
        bot = GridBot(testnet=True)
        
        # Display current price
        current_price = bot.get_current_price(symbol)
        print(f"Current {symbol} price: {current_price}")
        
        # Validate price range
        if current_price < lower_price or current_price > upper_price:
            print(f"\n⚠ WARNING: Current price ({current_price}) is outside grid range ({lower_price}-{upper_price})")
            print("Grid will only create orders on one side. Consider adjusting the range.")
        
        # Calculate grid parameters
        grid_step = (upper_price - lower_price) / (grid_levels - 1)
        total_quantity = quantity_per_grid * grid_levels
        
        # Confirm strategy
        print(f"\nGrid Trading Strategy:")
        print(f"  Symbol: {symbol}")
        print(f"  Price Range: {lower_price} - {upper_price}")
        print(f"  Grid Levels: {grid_levels}")
        print(f"  Grid Step: {grid_step:.2f}")
        print(f"  Quantity per Grid: {quantity_per_grid}")
        print(f"  Total Quantity: ~{total_quantity}")
        print(f"  Position Side: {position_side}")
        print(f"  Monitor Mode: {'Enabled' if monitor else 'Disabled'}")
        if monitor:
            print(f"  Check Interval: {check_interval}s")
        
        confirm = input("\nCreate grid orders? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("Grid creation cancelled by user")
            sys.exit(0)
        
        print(f"\n{'='*60}")
        print(f"Creating grid orders...")
        print(f"{'='*60}\n")
        
        # Create grid
        buy_orders, sell_orders = bot.create_grid_orders(symbol, lower_price, upper_price,
                                                         grid_levels, quantity_per_grid, position_side)
        
        # Display summary
        print(f"\n{'='*60}")
        print(f"GRID CREATION SUMMARY")
        print(f"{'='*60}")
        print(f"BUY Orders Placed: {len(buy_orders)}")
        print(f"SELL Orders Placed: {len(sell_orders)}")
        print(f"Total Orders: {len(buy_orders) + len(sell_orders)}")
        print(f"{'='*60}\n")
        
        # Monitor if requested
        if monitor:
            print(f"Starting grid monitoring (Press Ctrl+C to stop)...\n")
            bot.monitor_and_rebalance_grid(symbol, lower_price, upper_price,
                                          grid_levels, quantity_per_grid, check_interval)
        else:
            print("Grid created successfully. Remember to monitor and manage orders manually!")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(Formatter.format_error(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
