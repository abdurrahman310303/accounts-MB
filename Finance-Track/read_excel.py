#!/usr/bin/env python3
import pandas as pd
import sys
import os

def read_excel_file(filename):
    try:
        print(f"Analyzing file: {filename}")
        
        # Try to read as Excel first
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(filename)
            sheet_names = excel_file.sheet_names
            print(f"Excel sheets found: {sheet_names}")
            
            for sheet_name in sheet_names:
                print(f"\n{'='*50}")
                print(f"SHEET: {sheet_name}")
                print(f"{'='*50}")
                
                df = pd.read_excel(filename, sheet_name=sheet_name)
                print(f"Shape: {df.shape} (rows, columns)")
                print(f"Columns: {list(df.columns)}")
                
                # Show first few rows
                print(f"\nFirst 10 rows:")
                print(df.head(10).to_string())
                
                # Show data types
                print(f"\nData types:")
                print(df.dtypes)
                
                # Show non-null counts
                print(f"\nNon-null counts:")
                print(df.count())
                
                # Show unique values for categorical columns
                print(f"\nSample data for each column:")
                for col in df.columns:
                    unique_vals = df[col].dropna().unique()[:5]  # First 5 unique values
                    print(f"{col}: {unique_vals}")
                
                print("-" * 50)
        
        except Exception as excel_error:
            print(f"Not an Excel file, trying CSV: {excel_error}")
            
            # Try to read as CSV
            try:
                df = pd.read_csv(filename)
                print(f"CSV file loaded successfully!")
                print(f"Shape: {df.shape} (rows, columns)")
                print(f"Columns: {list(df.columns)}")
                
                # Show first few rows
                print(f"\nFirst 10 rows:")
                print(df.head(10).to_string())
                
                # Show data types
                print(f"\nData types:")
                print(df.dtypes)
                
            except Exception as csv_error:
                print(f"Failed to read as CSV: {csv_error}")
                
                # Try with different encoding
                try:
                    df = pd.read_csv(filename, encoding='latin-1')
                    print(f"CSV file loaded with latin-1 encoding!")
                    print(f"Shape: {df.shape} (rows, columns)")
                    print(f"Columns: {list(df.columns)}")
                    
                    # Show first few rows
                    print(f"\nFirst 10 rows:")
                    print(df.head(10).to_string())
                    
                except Exception as final_error:
                    print(f"All attempts failed: {final_error}")
        
    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    filename = "FinancialTracker_MasterRef__ AbdurRehman.csv"
    if os.path.exists(filename):
        read_excel_file(filename)
    else:
        print(f"File {filename} not found in current directory")
        print("Available files:")
        for f in os.listdir("."):
            if f.endswith(('.csv', '.xlsx', '.xls')):
                print(f"  - {f}")
