"""
Main CLI Interface for Binance Futures Trading Bot
Provides interactive menu-driven interface for all order types
"""
import sys
from colorama import Fore, Style
from config import Config
from utils import Formatter, BotLogger
from base_bot import BasicBot
from market_orders import MarketOrderBot
from limit_orders import LimitOrderBot

# Import advanced order types
sys.path.append('advanced')
from advanced.stop_limit import StopLimitOrderBot
from advanced.oco import OCOOrderBot
from advanced.twap import TWAPBot
from advanced.grid_strategy import GridBot


class TradingBotCLI:
    """Main CLI interface for the trading bot"""
    
    def __init__(self):
        self.logger = BotLogger('BotCLI')
        self.bot = None
    
    def print_banner(self):
        """Print welcome banner"""
        banner = f"""
{Fore.CYAN}{'='*70}
    ____  _                            ______      __                     
   / __ )(_)___  ____ _____  _______ / ____/_  __/ /___  ___________  ___
  / __  / / __ \\/ __ `/ __ \\/ ___/ _ \\\\__  \\/ / / / __/ / / ___/ _ \\/ ___/
 / /_/ / / / / / /_/ / / / / /__/  __/__/ / /_/ / /_/ /_/ / /  /  __(__  ) 
/_____/_/_/ /_/\\__,_/_/ /_/\\___/\\___/____/\\__,_/\\__/\\__,_/_/   \\___/____/  
                                                                           
            TRADING BOT - USDT-M Futures (TESTNET)
{'='*70}{Style.RESET_ALL}
"""
        print(banner)
    
    def print_menu(self):
        """Print main menu"""
        menu = f"""
{Fore.YELLOW}MAIN MENU:{Style.RESET_ALL}

{Fore.GREEN}Core Orders:{Style.RESET_ALL}
  1. Market Order (BUY/SELL at current price)
  2. Limit Order (BUY/SELL at specific price)

{Fore.CYAN}Advanced Orders:{Style.RESET_ALL}
  3. Stop-Limit Order (Trigger limit order at stop price)
  4. OCO Order (One-Cancels-the-Other: TP + SL)
  5. TWAP Strategy (Time-Weighted Average Price)
  6. Grid Trading (Automated buy-low/sell-high)

{Fore.MAGENTA}Account & Info:{Style.RESET_ALL}
  7. View Account Information
  8. View Current Price
  9. View Open Orders
  10. Cancel Order
  11. Cancel All Orders

{Fore.RED}0. Exit{Style.RESET_ALL}
"""
        print(menu)
    
    def initialize_bot(self):
        """Initialize the bot with credentials"""
        try:
            Config.validate()
            self.bot = BasicBot(testnet=True)
            self.logger.info("Bot initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {str(e)}")
            print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            print(f"\nPlease ensure you have:")
            print(f"1. Created a .env file with your API credentials")
            print(f"2. Set BINANCE_API_KEY and BINANCE_API_SECRET")
            print(f"\nSee .env.example for reference")
            return False
    
    def get_input(self, prompt: str, type_func=str, default=None):
        """Get user input with type conversion"""
        while True:
            try:
                value = input(f"{prompt}: ").strip()
                if not value and default is not None:
                    return default
                return type_func(value)
            except ValueError:
                print(f"{Fore.RED}Invalid input. Please try again.{Style.RESET_ALL}")
    
    def handle_market_order(self):
        """Handle market order placement"""
        Formatter.print_header("MARKET ORDER")
        
        print(f"{Fore.YELLOW}Common symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT{Style.RESET_ALL}")
        symbol = self.get_input("Symbol (e.g., BTCUSDT)").upper()
        side = self.get_input("Side (BUY/SELL)").upper()
        quantity = self.get_input("Quantity", float)
        
        try:
            bot = MarketOrderBot(testnet=True)
            current_price = bot.get_current_price(symbol)
            print(f"\nCurrent {symbol} price: {current_price}")
            
            confirm = input(f"\nConfirm MARKET {side} {quantity} {symbol}? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                order = bot.place_market_order(symbol, side, quantity)
                print(Formatter.format_order_response(order))
            else:
                print("Order cancelled")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_limit_order(self):
        """Handle limit order placement"""
        Formatter.print_header("LIMIT ORDER")
        
        print(f"{Fore.YELLOW}Common symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT{Style.RESET_ALL}")
        symbol = self.get_input("Symbol (e.g., BTCUSDT)").upper()
        side = self.get_input("Side (BUY/SELL)").upper()
        quantity = self.get_input("Quantity", float)
        price = self.get_input("Limit Price", float)
        
        try:
            bot = LimitOrderBot(testnet=True)
            current_price = bot.get_current_price(symbol)
            print(f"\nCurrent {symbol} price: {current_price}")
            print(f"Your limit price is {((price - current_price) / current_price * 100):+.2f}% from current")
            
            confirm = input(f"\nConfirm LIMIT {side} {quantity} {symbol} @ {price}? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                order = bot.place_limit_order(symbol, side, quantity, price)
                print(Formatter.format_order_response(order))
            else:
                print("Order cancelled")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_stop_limit_order(self):
        """Handle stop-limit order placement"""
        Formatter.print_header("STOP-LIMIT ORDER")
        
        symbol = self.get_input("Symbol (e.g., BTCUSDT)").upper()
        side = self.get_input("Side (BUY/SELL)").upper()
        quantity = self.get_input("Quantity", float)
        stop_price = self.get_input("Stop Price", float)
        limit_price = self.get_input("Limit Price", float)
        
        try:
            bot = StopLimitOrderBot(testnet=True)
            current_price = bot.get_current_price(symbol)
            print(f"\nCurrent {symbol} price: {current_price}")
            
            confirm = input(f"\nConfirm STOP-LIMIT {side} {quantity} {symbol}? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                order = bot.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
                print(Formatter.format_order_response(order))
            else:
                print("Order cancelled")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_oco_order(self):
        """Handle OCO order placement"""
        Formatter.print_header("OCO ORDER (One-Cancels-the-Other)")
        
        print("Note: Use this to close an existing position with TP and SL")
        symbol = self.get_input("Symbol (e.g., BTCUSDT)").upper()
        side = self.get_input("Closing Side (SELL for LONG, BUY for SHORT)").upper()
        quantity = self.get_input("Quantity", float)
        tp_price = self.get_input("Take Profit Price", float)
        sl_price = self.get_input("Stop Loss Price", float)
        
        try:
            bot = OCOOrderBot(testnet=True)
            current_price = bot.get_current_price(symbol)
            print(f"\nCurrent {symbol} price: {current_price}")
            
            confirm = input(f"\nConfirm OCO orders? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                tp_order, sl_order = bot.place_oco_order(symbol, side, quantity, tp_price, sl_price)
                print(Formatter.format_order_response(tp_order))
                print(Formatter.format_order_response(sl_order))
            else:
                print("Order cancelled")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_twap(self):
        """Handle TWAP strategy execution"""
        Formatter.print_header("TWAP STRATEGY")
        
        symbol = self.get_input("Symbol (e.g., BTCUSDT)").upper()
        side = self.get_input("Side (BUY/SELL)").upper()
        total_quantity = self.get_input("Total Quantity", float)
        duration = self.get_input("Duration (minutes)", int)
        num_orders = self.get_input("Number of Orders", int)
        
        try:
            bot = TWAPBot(testnet=True)
            current_price = bot.get_current_price(symbol)
            print(f"\nCurrent {symbol} price: {current_price}")
            
            order_size = total_quantity / num_orders
            interval = (duration * 60) / num_orders
            print(f"Order size: {order_size}, Interval: {interval:.1f}s")
            
            confirm = input(f"\nStart TWAP execution? (This will take {duration} minutes) (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                orders = bot.execute_twap(symbol, side, total_quantity, duration, num_orders)
                summary = bot.get_twap_summary(orders)
                print(f"\n{Fore.GREEN}TWAP completed!{Style.RESET_ALL}")
                print(f"Orders executed: {summary.get('total_orders', 0)}")
                print(f"Average price: {summary.get('average_price', 0):.2f}")
            else:
                print("TWAP cancelled")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_grid_trading(self):
        """Handle grid trading strategy"""
        Formatter.print_header("GRID TRADING STRATEGY")
        
        symbol = self.get_input("Symbol (e.g., BTCUSDT)").upper()
        lower_price = self.get_input("Lower Price", float)
        upper_price = self.get_input("Upper Price", float)
        grid_levels = self.get_input("Grid Levels", int)
        quantity = self.get_input("Quantity per Grid", float)
        
        try:
            bot = GridBot(testnet=True)
            current_price = bot.get_current_price(symbol)
            print(f"\nCurrent {symbol} price: {current_price}")
            
            grid_step = (upper_price - lower_price) / (grid_levels - 1)
            print(f"Grid step: {grid_step:.2f}")
            
            confirm = input(f"\nCreate grid orders? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                buy_orders, sell_orders = bot.create_grid_orders(symbol, lower_price, upper_price, grid_levels, quantity)
                print(f"\n{Fore.GREEN}Grid created!{Style.RESET_ALL}")
                print(f"BUY orders: {len(buy_orders)}, SELL orders: {len(sell_orders)}")
            else:
                print("Grid creation cancelled")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_account_info(self):
        """Display account information"""
        Formatter.print_header("ACCOUNT INFORMATION")
        
        try:
            info = self.bot.get_account_info()
            print(f"Total Wallet Balance: {info.get('totalWalletBalance', 0)} USDT")
            print(f"Available Balance: {info.get('availableBalance', 0)} USDT")
            print(f"Total Unrealized Profit: {info.get('totalUnrealizedProfit', 0)} USDT")
            
            positions = [p for p in info.get('positions', []) if float(p.get('positionAmt', 0)) != 0]
            if positions:
                print(f"\nOpen Positions ({len(positions)}):")
                for pos in positions:
                    print(f"  {pos['symbol']}: {pos['positionAmt']} @ {pos['entryPrice']}")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_current_price(self):
        """Display current price"""
        print(f"{Fore.YELLOW}Common symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT{Style.RESET_ALL}")
        symbol = self.get_input("Symbol (e.g., BTCUSDT)").upper()
        
        try:
            price = self.bot.get_current_price(symbol)
            print(f"\n{Fore.GREEN}{symbol}: {price}{Style.RESET_ALL}")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_open_orders(self):
        """Display open orders"""
        Formatter.print_header("OPEN ORDERS")
        
        symbol = self.get_input("Symbol (leave empty for all)", default='')
        
        try:
            orders = self.bot.get_open_orders(symbol if symbol else None)
            if not orders:
                print("No open orders")
            else:
                print(f"\nFound {len(orders)} open orders:")
                for order in orders:
                    print(f"\n  Order ID: {order['orderId']}")
                    print(f"  Symbol: {order['symbol']}")
                    print(f"  Side: {order['side']}")
                    print(f"  Type: {order['type']}")
                    print(f"  Price: {order.get('price', 'N/A')}")
                    print(f"  Quantity: {order['origQty']}")
                    print(f"  Status: {order['status']}")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_cancel_order(self):
        """Cancel a specific order"""
        Formatter.print_header("CANCEL ORDER")
        
        symbol = self.get_input("Symbol").upper()
        order_id = self.get_input("Order ID", int)
        
        try:
            result = self.bot.cancel_order(symbol, order_id)
            print(f"\n{Fore.GREEN}Order {order_id} cancelled successfully{Style.RESET_ALL}")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def handle_cancel_all_orders(self):
        """Cancel all orders for a symbol"""
        Formatter.print_header("CANCEL ALL ORDERS")
        
        symbol = self.get_input("Symbol").upper()
        
        confirm = input(f"\n{Fore.RED}Cancel ALL orders for {symbol}? (yes/no): {Style.RESET_ALL}").strip().lower()
        if confirm not in ['yes', 'y']:
            print("Cancelled")
            return
        
        try:
            result = self.bot.cancel_all_orders(symbol)
            print(f"\n{Fore.GREEN}All orders for {symbol} cancelled{Style.RESET_ALL}")
        except Exception as e:
            print(Formatter.format_error(e))
    
    def run(self):
        """Main CLI loop"""
        self.print_banner()
        
        if not self.initialize_bot():
            return
        
        while True:
            self.print_menu()
            
            try:
                choice = input(f"\n{Fore.CYAN}Select option: {Style.RESET_ALL}").strip()
                
                if choice == '0':
                    print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}\n")
                    break
                elif choice == '1':
                    self.handle_market_order()
                elif choice == '2':
                    self.handle_limit_order()
                elif choice == '3':
                    self.handle_stop_limit_order()
                elif choice == '4':
                    self.handle_oco_order()
                elif choice == '5':
                    self.handle_twap()
                elif choice == '6':
                    self.handle_grid_trading()
                elif choice == '7':
                    self.handle_account_info()
                elif choice == '8':
                    self.handle_current_price()
                elif choice == '9':
                    self.handle_open_orders()
                elif choice == '10':
                    self.handle_cancel_order()
                elif choice == '11':
                    self.handle_cancel_all_orders()
                else:
                    print(f"{Fore.RED}Invalid option. Please try again.{Style.RESET_ALL}")
                
                input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Interrupted. Exiting...{Style.RESET_ALL}\n")
                break
            except Exception as e:
                print(Formatter.format_error(e))
                input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")


def main():
    """Entry point"""
    cli = TradingBotCLI()
    cli.run()


if __name__ == "__main__":
    main()
