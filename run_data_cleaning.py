
import pandas as pd
import numpy as np
import duckdb as db
from pathlib import Path
from datetime import datetime
import sys

def main():
    print(f"Starting data cleaning pipeline at {datetime.now()}")
    
    results = {}
    
    RAW = Path("./data/raw/menus")
    print(f"Loading data from: {RAW}")
    
    print("Loading datasets...")
    dish_orig = pd.read_csv(RAW / "Dish.csv", low_memory=False)
    item_orig = pd.read_csv(RAW / "MenuItem.csv", low_memory=False) 
    page_orig = pd.read_csv(RAW / "MenuPage.csv", low_memory=False)
    menu_orig = pd.read_csv(RAW / "Menu.csv", low_memory=False)
    
    dish = dish_orig.copy()
    item = item_orig.copy()
    page = page_orig.copy()
    menu = menu_orig.copy()
    
    print("Original Data Shapes")
    print(f"Dish: {dish.shape}")
    print(f"MenuItem: {item.shape}")
    print(f"MenuPage: {page.shape}")
    print(f"Menu: {menu.shape}")
    
    results['original_shapes'] = {
        'dish': dish.shape,
        'item': item.shape,
        'page': page.shape,
        'menu': menu.shape
    }
    
    print("Duplicate Analysis")
    tables = [('Dish', dish), ('MenuItem', item), ('MenuPage', page), ('Menu', menu)]
    duplicate_counts = {}
    
    for name, df in tables:
        duplicates = df.duplicated().sum()
        duplicate_counts[name] = duplicates
        print(f"{name}: {duplicates} duplicate rows")
        
        if duplicates > 0:
            print(f"  Removing {duplicates} duplicates from {name}")
            if name == 'Dish':
                dish = dish.drop_duplicates()
            elif name == 'MenuItem':
                item = item.drop_duplicates()
            elif name == 'MenuPage':
                page = page.drop_duplicates()
            elif name == 'Menu':
                menu = menu.drop_duplicates()
    
    results['duplicate_counts'] = duplicate_counts
    
    print("Null Handling in Critical Columns")
    null_changes = {}
    
    item_null_dish = item['dish_id'].isnull().sum()
    print(f"MenuItem rows with null dish_id: {item_null_dish}")
    if item_null_dish > 0:
        item = item.dropna(subset=['dish_id'])
        null_changes['MenuItem_dish_id'] = item_null_dish
    
    item_null_page = item['menu_page_id'].isnull().sum()
    print(f"MenuItem rows with null menu_page_id: {item_null_page}")
    if item_null_page > 0:
        item = item.dropna(subset=['menu_page_id'])
        null_changes['MenuItem_menu_page_id'] = item_null_page
    
    page_null_menu = page['menu_id'].isnull().sum()
    print(f"MenuPage rows with null menu_id: {page_null_menu}")
    if page_null_menu > 0:
        page = page.dropna(subset=['menu_id'])
        null_changes['MenuPage_menu_id'] = page_null_menu
    
    item_null_price = item['price'].isnull().sum()
    print(f"MenuItem rows with null price: {item_null_price}")
    if item_null_price > 0:
        item = item.dropna(subset=['price'])
        null_changes['MenuItem_price'] = item_null_price
    
    print(f"Total null-related removals: {sum(null_changes.values())}")
    results['null_changes'] = null_changes
    
    print("Optional Column Null Handling")
    menu_name_nulls = menu['name'].isnull().sum()
    menu_place_nulls = menu['place'].isnull().sum()
    dish_name_nulls = dish['name'].isnull().sum()
    
    menu['name'] = menu['name'].fillna('Unknown Menu')
    menu['place'] = menu['place'].fillna('Unknown Location')
    dish['name'] = dish['name'].fillna('Unknown Dish')
    
    optional_fills = menu_name_nulls + menu_place_nulls + dish_name_nulls
    print(f"Filled {optional_fills} null values in optional columns")
    results['optional_fills'] = optional_fills
    
    print("Price Cleaning and Outlier Removal")
    
    item['price_cleaned'] = (
        pd.to_numeric(
            item['price']
                .astype(str)
                .str.replace(r'[^0-9.\-]', '', regex=True), 
            errors='coerce'
        )
    )
    
    unparseable_prices = item['price_cleaned'].isnull().sum()
    print(f"Rows with unparseable prices: {unparseable_prices}")
    item = item.dropna(subset=['price_cleaned'])
    
    print("Price Statistics (Before Outlier Removal)")
    print(item['price_cleaned'].describe())
    
    extreme_outliers = item[(item['price_cleaned'] < 0) | (item['price_cleaned'] > 500)]
    outlier_count = len(extreme_outliers)
    print(f"Extreme outliers (< $0 or > $500): {outlier_count}")
    
    item = item[(item['price_cleaned'] >= 0) & (item['price_cleaned'] <= 500)]
    item['price_cleaned'] = item['price_cleaned'].round(2)
    
    print(f"Removed {outlier_count} extreme price outliers")
    print("Price Statistics (After Cleaning)")
    print(item['price_cleaned'].describe())
    
    results['outlier_count'] = outlier_count
    results['price_stats_after'] = {
        'min': item['price_cleaned'].min(),
        'max': item['price_cleaned'].max(),
        'mean': item['price_cleaned'].mean(),
        'count': len(item)
    }
    
    print("Date Cleaning for U1 Analysis")
    menu['date_orig'] = menu['date'].copy()
    menu['date'] = pd.to_datetime(menu['date'], errors='coerce')
    
    invalid_dates = menu['date'].isnull().sum()
    print(f"Invalid/unparseable dates: {invalid_dates}")
    
    if invalid_dates > 0:
        menu = menu.dropna(subset=['date'])
    
    menu['decade'] = (menu['date'].dt.year // 10) * 10
    print(f"Date range: {menu['date'].min()} to {menu['date'].max()}")
    print(f"Decades represented: {sorted(menu['decade'].dropna().unique())}")
    
    results['invalid_dates'] = invalid_dates
    
    print("Removing Orphaned Foreign Key Records")
    orphan_removals = {}
    
    item_before = len(item)
    valid_dish_ids = set(dish['id'])
    item = item[item['dish_id'].isin(valid_dish_ids)]
    orphan_dish_removed = item_before - len(item)
    orphan_removals['MenuItem_orphan_dish_id'] = orphan_dish_removed
    print(f"Removed {orphan_dish_removed} MenuItem rows with orphaned dish_id")
    
    item_before = len(item)
    valid_page_ids = set(page['id'])
    item = item[item['menu_page_id'].isin(valid_page_ids)]
    orphan_page_removed = item_before - len(item)
    orphan_removals['MenuItem_orphan_page_id'] = orphan_page_removed
    print(f"Removed {orphan_page_removed} MenuItem rows with orphaned menu_page_id")
    
    page_before = len(page)
    valid_menu_ids = set(menu['id'])
    page = page[page['menu_id'].isin(valid_menu_ids)]
    orphan_menu_removed = page_before - len(page)
    orphan_removals['MenuPage_orphan_menu_id'] = orphan_menu_removed
    print(f"Removed {orphan_menu_removed} MenuPage rows with orphaned menu_id")
    
    item_before = len(item)
    valid_page_ids_after = set(page['id'])
    item = item[item['menu_page_id'].isin(valid_page_ids_after)]
    cascaded_item_removed = item_before - len(item)
    orphan_removals['MenuItem_cascaded_from_page_cleanup'] = cascaded_item_removed
    print(f"Removed {cascaded_item_removed} MenuItem rows cascaded from MenuPage cleanup")
    
    print(f"Total orphan-related removals: {sum(orphan_removals.values())}")
    results['orphan_removals'] = orphan_removals
    
    print("Referential Integrity Verification")
    con = db.connect()
    con.register("dish_clean", dish)
    con.register("item_clean", item)
    con.register("page_clean", page)
    con.register("menu_clean", menu)
    
    orphan_dish_check = con.sql("""
        SELECT COUNT(*) as orphan_count
        FROM item_clean i
        LEFT JOIN dish_clean d ON i.dish_id = d.id
        WHERE d.id IS NULL
    """).df()['orphan_count'].iloc[0]
    
    orphan_page_check = con.sql("""
        SELECT COUNT(*) as orphan_count
        FROM item_clean i
        LEFT JOIN page_clean p ON i.menu_page_id = p.id
        WHERE p.id IS NULL
    """).df()['orphan_count'].iloc[0]
    
    orphan_menu_check = con.sql("""
        SELECT COUNT(*) as orphan_count
        FROM page_clean p
        LEFT JOIN menu_clean m ON p.menu_id = m.id
        WHERE m.id IS NULL
    """).df()['orphan_count'].iloc[0]
    
    integrity_check = orphan_dish_check + orphan_page_check + orphan_menu_check
    print(f"Remaining orphaned dish_ids in MenuItem: {orphan_dish_check}")
    print(f"Remaining orphaned menu_page_ids in MenuItem: {orphan_page_check}")
    print(f"Remaining orphaned menu_ids in MenuPage: {orphan_menu_check}")
    print(f"Referential integrity {'PASSED' if integrity_check == 0 else 'FAILED'}")
    
    results['integrity_check'] = integrity_check
    
    print("Comprehensive Cleaning Summary")
    print("Before/After Row Counts:")
    print(f"Dish:     {dish_orig.shape[0]:,} → {dish.shape[0]:,} ({dish_orig.shape[0] - dish.shape[0]:,} removed)")
    print(f"MenuItem: {item_orig.shape[0]:,} → {item.shape[0]:,} ({item_orig.shape[0] - item.shape[0]:,} removed)")
    print(f"MenuPage: {page_orig.shape[0]:,} → {page.shape[0]:,} ({page_orig.shape[0] - page.shape[0]:,} removed)")
    print(f"Menu:     {menu_orig.shape[0]:,} → {menu.shape[0]:,} ({menu_orig.shape[0] - menu.shape[0]:,} removed)")
    
    total_orig = dish_orig.shape[0] + item_orig.shape[0] + page_orig.shape[0] + menu_orig.shape[0]
    total_clean = dish.shape[0] + item.shape[0] + page.shape[0] + menu.shape[0]
    reduction_pct = ((total_orig - total_clean)/total_orig)*100
    
    print(f"TOTAL:    {total_orig:,} → {total_clean:,} ({total_orig - total_clean:,} removed, {reduction_pct:.1f}% reduction)")
    
    results['final_shapes'] = {
        'dish': dish.shape,
        'item': item.shape,
        'page': page.shape,
        'menu': menu.shape
    }
    results['reduction_pct'] = reduction_pct
    
    print("Cleaning Actions Performed:")
    print(f"Duplicates removed: {sum(duplicate_counts.values())}")
    print(f"Null critical columns removed: {sum(null_changes.values())}")
    print(f"Price outliers removed: {outlier_count}")
    print(f"Orphaned records removed: {sum(orphan_removals.values())}")
    print(f"Invalid dates removed: {invalid_dates}")
    print(f"Null optional columns filled: {optional_fills}")
    
    CLEAN_DIR = Path("./data/cleaned")
    CLEAN_DIR.mkdir(exist_ok=True)
    
    print(f"Exporting cleaned data to: {CLEAN_DIR}")
    
    dish.to_csv(CLEAN_DIR / "Dish_cleaned.csv", index=False)
    item.to_csv(CLEAN_DIR / "MenuItem_cleaned.csv", index=False) 
    page.to_csv(CLEAN_DIR / "MenuPage_cleaned.csv", index=False)
    menu.to_csv(CLEAN_DIR / "Menu_cleaned.csv", index=False)
    
    print("Cleaned CSV files exported successfully")
    print("Files created:")
    for file in CLEAN_DIR.glob("*.csv"):
        file_size = file.stat().st_size / (1024*1024)  # MB
        print(f"{file.name} ({file_size:.1f} MB)")
    
    results_file = CLEAN_DIR / "cleaning_results_summary.txt"
    with open(results_file, 'w') as f:
        f.write("DATA CLEANING RESULTS SUMMARY\n")
        f.write("="*50 + "\n\n")
        f.write(f"Execution time: {datetime.now()}\n\n")
        
        f.write("BEFORE/AFTER COUNTS:\n")
        f.write(f"Dish:     {dish_orig.shape[0]:,} → {dish.shape[0]:,}\n")
        f.write(f"MenuItem: {item_orig.shape[0]:,} → {item.shape[0]:,}\n")
        f.write(f"MenuPage: {page_orig.shape[0]:,} → {page.shape[0]:,}\n")
        f.write(f"Menu:     {menu_orig.shape[0]:,} → {menu.shape[0]:,}\n")
        f.write(f"Total reduction: {reduction_pct:.1f}%\n\n")
        
        f.write("KEY METRICS:\n")
        f.write(f"Duplicates removed: {sum(duplicate_counts.values())}\n")
        f.write(f"Null critical columns removed: {sum(null_changes.values())}\n")
        f.write(f"Price outliers removed: {outlier_count}\n")
        f.write(f"Orphaned records removed: {sum(orphan_removals.values())}\n")
        f.write(f"Invalid dates removed: {invalid_dates}\n")
        f.write(f"Referential integrity violations remaining: {integrity_check}\n")
    
    print(f"Results summary saved to: {results_file}")
    print(f"Cleaning completed at {datetime.now()}")
    
    return results

if __name__ == "__main__":
    main() 