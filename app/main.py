import sys
import os
from pathlib import Path

# Add the current directory to sys.path to ensure imports work correctly
sys.path.append(str(Path(__file__).resolve().parent))

import view_inventory
import portfolio_stats
import add_shoe

def main():
    while True:
        print("\n=== Sneaker Inventory Manager ===")
        print("1. View Inventory (CLI)")
        print("2. Add New Shoe (CLI)")
        print("3. View Portfolio Stats (CLI)")
        print("4. Launch Web Dashboard (Streamlit)")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            view_inventory.view_all_inventory()
        elif choice == '2':
            add_shoe.add_shoe_cli()
        elif choice == '3':
            portfolio_stats.calculate_and_print_stats()
        elif choice == '4':
            print("Launching Streamlit Dashboard...")
            dashboard_path = Path(__file__).parent / "dashboard.py"
            # Run streamlit as a subprocess
            os.system(f'"{sys.executable}" -m streamlit run "{dashboard_path}"')
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
