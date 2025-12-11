import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

# ---------------------------
# GLOBAL CONSTANTS
# ---------------------------
CONVERSIONS = {'pcs': 1.0, 'each': 1.0, 'm': 1.0, 'cm': 0.01, 'ft': 0.3048, 'in': 0.0254}
P_L_STATUS = ["Work Done", "Closed"]
ACTIVE_STATUSES = ["New Lead", "Estimate Given", "Order Received", "Work In Progress"]
ACTIVE_STATUSES = ["New Lead", "Estimate Given", "Order Received", "Work In Progress"]
INACTIVE_STATUSES = ["Work Done", "Closed"]

# --- PROFESSIONAL PDF GENERATOR ---
class PDFGenerator:
    def __init__(self):
        self.pdf = FPDF()

    def _add_header(self, title):
        self.pdf.add_page()
        self.pdf.set_font("Arial", 'B', 20)
        self.pdf.cell(0, 10, "Galaxy Fabrication Experts", ln=True, align='L')
        # Tagline removed as requested
        self.pdf.line(10, 20, 200, 20) # Adjusted line position up since tagline is gone
        self.pdf.ln(15)
        self.pdf.set_font("Arial", 'B', 12)
        self.pdf.cell(0, 8, title, ln=True)
        self.pdf.set_font("Arial", '', 10)
        self.pdf.cell(0, 8, f"Date: {datetime.now().strftime('%d-%b-%Y')}", ln=True)
        self.pdf.ln(5)

    def generate_client_invoice(self, client_name, items, labor_days, labor_total, grand_total, advance_amount, is_final=False):
        title = f"INVOICE For: {client_name}" if is_final else f"Estimate For: {client_name}"
        self._add_header(title)
        
        self.pdf.set_fill_color(240, 240, 240)
        self.pdf.set_font("Arial", 'B', 10)
        self.pdf.cell(100, 10, "Description", 1, 0, 'L', 1)
        self.pdf.cell(15, 10, "Qty", 1, 0, 'C', 1)
        self.pdf.cell(15, 10, "Unit", 1, 0, 'C', 1)
        self.pdf.cell(60, 10, "Amount (INR)", 1, 1, 'R', 1)
        
        self.pdf.set_font("Arial", '', 10)
        for item in items:
            self.pdf.cell(100, 8, str(item.get('Item', '')), 1)
            self.pdf.cell(15, 8, str(item.get('Qty', 0)), 1, 0, 'C')
            self.pdf.cell(15, 8, str(item.get('Unit', '')), 1, 0, 'C')
            self.pdf.cell(60, 8, f"{item.get('Total Price', 0):,.2f}", 1, 1, 'R')
            
        self.pdf.set_font("Arial", '', 10)
        self.pdf.cell(130, 8, f"Labor / Installation ({labor_days} Days)", 1, 0, 'R')
        self.pdf.cell(60, 8, f"{labor_total:,.2f}", 1, 1, 'R')
        
        self.pdf.set_font("Arial", 'B', 12)
        self.pdf.cell(130, 10, "Grand Total", 1, 0, 'R')
        self.pdf.cell(60, 10, f"Rs. {grand_total:,.2f}", 1, 1, 'R')
        
        self.pdf.ln(10)
        self.pdf.set_font("Arial", 'B', 10)
        
        if is_final:
            self.pdf.multi_cell(0, 5, f"Total Amount: Rs. {grand_total:,.2f}")
            self.pdf.ln(5)
            self.pdf.set_font("Arial", 'I', 10)
            self.pdf.multi_cell(0, 5, "Thank you for your business!")
        else:
            self.pdf.multi_cell(0, 5, f"Advance Payment Required: Rs. {advance_amount:,.2f}")
            self.pdf.ln(5)
            self.pdf.set_font("Arial", 'I', 8)
            self.pdf.set_text_color(100, 100, 100)
            self.pdf.multi_cell(0, 5, "NOTE: This is an estimate only. Final rates may vary based on actual site conditions and market fluctuations. Valid for 7 days.")
        
        pdf_output = BytesIO()
        pdf_string = self.pdf.output(dest='S')
        pdf_output.write(pdf_string.encode('latin-1'))
        return pdf_output.getvalue()

    def generate_internal_report(self, client_name, items, labor_days, labor_cost, labor_charged, grand_total, total_profit):
        self._add_header(f"INTERNAL PROFIT REPORT (CONFIDENTIAL) - {client_name}")
        
        self.pdf.set_fill_color(220, 220, 220)
        self.pdf.set_font("Arial", 'B', 9)
        self.pdf.cell(70, 8, "Item Description", 1, 0, 'L', 1)
        self.pdf.cell(15, 8, "Qty", 1, 0, 'C', 1)
        self.pdf.cell(35, 8, "Base Rate", 1, 0, 'R', 1)
        self.pdf.cell(35, 8, "Sold At", 1, 0, 'R', 1)
        self.pdf.cell(35, 8, "Profit", 1, 1, 'R', 1)

        self.pdf.set_font("Arial", '', 9)
        for item in items:
            qty = float(item.get('Qty', 0))
            base = float(item.get('Base Rate', 0))
            total_sell = float(item.get('Total Price', 0))
            unit_sell = total_sell / qty if qty > 0 else 0
            row_profit = total_sell - (base * qty)
            
            self.pdf.cell(70, 8, str(item.get('Item', ''))[:35], 1)
            self.pdf.cell(15, 8, str(qty), 1, 0, 'C')
            self.pdf.cell(35, 8, f"{base:,.2f}", 1, 0, 'R')
            self.pdf.cell(35, 8, f"{unit_sell:,.2f}", 1, 0, 'R')
            self.pdf.set_text_color(0, 150, 0); self.pdf.cell(35, 8, f"{row_profit:,.2f}", 1, 1, 'R'); self.pdf.set_text_color(0, 0, 0)

        labor_profit = labor_charged - labor_cost
        self.pdf.ln(5)
        self.pdf.set_font("Arial", 'B', 10)
        self.pdf.cell(120, 8, f"Labor ({labor_days} Days)", 1, 0, 'R')
        self.pdf.cell(35, 8, f"Cost: {labor_cost:,.2f}", 1, 0, 'R')
        self.pdf.cell(35, 8, f"Chrg: {labor_charged:,.2f}", 1, 1, 'R')

        self.pdf.ln(10)
        self.pdf.set_font("Arial", 'B', 12)
        self.pdf.cell(120, 10, "TOTAL REVENUE:", 1, 0, 'R')
        self.pdf.cell(70, 10, f"Rs. {grand_total:,.2f}", 1, 1, 'R')
        self.pdf.cell(120, 10, "NET PROFIT:", 1, 0, 'R')
        self.pdf.set_text_color(0, 150, 0); self.pdf.cell(70, 10, f"Rs. {total_profit:,.2f}", 1, 1, 'R')

        pdf_output = BytesIO()
        pdf_string = self.pdf.output(dest='S')
        pdf_output.write(pdf_string.encode('latin-1'))
        return pdf_output.getvalue()

    def generate_order_list(self, client_name, items):
        self._add_header(f"ORDER LIST - {client_name}")
        
        self.pdf.set_fill_color(230, 230, 250) # Light lavender
        self.pdf.set_font("Arial", 'B', 10)
        
        # Columns: Sr No (15), Item (95), Qty pcs (40), Qty ft (40)
        self.pdf.cell(15, 10, "Sr No", 1, 0, 'C', 1)
        self.pdf.cell(95, 10, "Item Description", 1, 0, 'L', 1)
        self.pdf.cell(40, 10, "Qty (pcs)", 1, 0, 'C', 1)
        self.pdf.cell(40, 10, "Qty (feet)", 1, 1, 'C', 1)
        
        self.pdf.set_font("Arial", '', 10)
        for idx, item in enumerate(items, 1):
            name = str(item.get('Item', ''))
            qty_pcs = float(item.get('Qty (pcs)', 0))
            qty_raw = float(item.get('Qty', 0))
            unit = str(item.get('Unit', ''))
            
            # Formatting
            pcs_str = f"{qty_pcs:.2f}"
            ft_str = f"{qty_raw:.2f}" if unit == 'ft' else "-"
            
            self.pdf.cell(15, 8, str(idx), 1, 0, 'C')
            self.pdf.cell(95, 8, name[:50], 1, 0, 'L')
            self.pdf.cell(40, 8, pcs_str, 1, 0, 'C')
            self.pdf.cell(40, 8, ft_str, 1, 1, 'C')
            
        pdf_output = BytesIO()
        pdf_string = self.pdf.output(dest='S')
        pdf_output.write(pdf_string.encode('latin-1'))
        return pdf_output.getvalue()

def create_pdf(*args, **kwargs):
    pdf_gen = PDFGenerator()
    return pdf_gen.generate_client_invoice(*args, **kwargs)

def create_internal_pdf(*args, **kwargs):
    pdf_gen = PDFGenerator()
    return pdf_gen.generate_internal_report(*args, **kwargs)

def create_order_pdf(*args, **kwargs):
    pdf_gen = PDFGenerator()
    return pdf_gen.generate_order_list(*args, **kwargs)


def normalize_margins(margins_data, global_settings):
    """
    Returns the single profit margin integer.
    """
    if margins_data is None:
        return int(global_settings.get('profit_margin', 15))
    
    # If it's a dict (old format or just passed as dict), try to get profit_margin
    if isinstance(margins_data, dict):
        return int(margins_data.get('profit_margin', global_settings.get('profit_margin', 15)))
    
    # If it's already a value
    try:
        return int(margins_data)
    except:
        return int(global_settings.get('profit_margin', 15))


def get_advance_percentage(settings):
    """Get advance percentage from settings"""
    return float(settings.get('advance_percentage', 10.0))


def calculate_estimate_details(edf_items_list, days, margins, global_settings, welders=0, helpers=0, labor_details=None):
    """
    Calculates various financial details for an estimate.
    CENTRALIZED calculation - ensures consistency across all tabs.

    Args:
        edf_items_list (list): A list of list items.
        days (float): Labor days.
        margins (dict): Margins.
        global_settings (dict): Global settings.
        welders (int): Legacy welder count.
        helpers (int): Legacy helper count.
        labor_details (list): List of dicts [{'role': name, 'count': val, 'rate': val}]

    Returns:
        dict: Financial details.
    """
    # Normalize margins to standard format
    profit_margin = normalize_margins(margins, global_settings)
    
    mm = 1 + (profit_margin / 100.0)

    def calc_total_item(row):
        try:
            qty = float(row.get('Qty', 0))
            base = float(row.get('Base Rate', 0))
            # unit_name = row.get('Unit', 'pcs')
            # unit_name = row.get('Unit', 'pcs')
            # factor = CONVERSIONS.get(unit_name, 1.0) # Removed factor: Rate is Per Unit
            return base * qty 
        except (ValueError, TypeError):
            return 0.0

    edf_details_df = pd.DataFrame(edf_items_list)
    if not edf_details_df.empty:
        edf_details_df['Total Price'] = edf_details_df.apply(calc_total_item, axis=1)
        # Unit Price should just be Base Rate as per user request
        edf_details_df['Unit Price'] = edf_details_df['Base Rate'].apply(lambda x: float(x) if x else 0.0)
        mat_sell = float(edf_details_df['Total Price'].sum())
    else:
        mat_sell = 0.0

    # Calculate labor cost
    labor_actual_cost = 0.0
    
    if labor_details:
        # New Dynamic System
        for item in labor_details:
            cnt = float(item.get('count', 0))
            rate = float(item.get('rate', 0))
            labor_actual_cost += cnt * rate * float(days)
    else:
        # Legacy Fallback
        welder_rate = float(global_settings.get('welder_daily_rate', 500.0))
        helper_rate = float(global_settings.get('helper_daily_rate', 300.0))
        
        cost_welders = float(welders) * welder_rate * float(days)
        cost_helpers = float(helpers) * helper_rate * float(days)
        labor_actual_cost = cost_welders + cost_helpers

    def calculate_item_base_cost(row):
        qty = float(row.get('Qty', 0))
        base_rate = float(row.get('Base Rate', 0))
        # unit_name = row.get('Unit', 'pcs')
        # factor = CONVERSIONS.get(unit_name, 1.0)
        return base_rate * qty
    
    # Total Material Base Cost
    total_material_base_cost = float(edf_details_df.apply(calculate_item_base_cost, axis=1).sum()) if not edf_details_df.empty else 0.0
    
    # 1. TOTAL COST (Material + Labor)
    total_project_cost = total_material_base_cost + labor_actual_cost
    
    # 2. PROFIT
    # global profit 100% means cost X2 -> Profit = Cost * (margin/100)
    profit_amount = total_project_cost * (profit_margin / 100.0)
    
    # 3. BILL AMOUNT
    # Cost + Profit
    raw_bill_amount = total_project_cost + profit_amount
    # Rounding Bill Amount (User requested no rounding to 100, just integer)
    bill_amount = int(round(raw_bill_amount))
    
    # Profit derived from rounded bill
    final_profit = bill_amount - total_project_cost

    # 4. ADVANCE REQ
    # %adv of bill amt
    adv_margin_pct = float(global_settings.get('advance_percentage', 20.0))
    advance_amount = int(round(bill_amount * (adv_margin_pct / 100.0)))
    
    # Update Item 'Total Price' to reflect Selling Price (Base + Profit Margin)
    # Update Item 'Total Price' to reflect Selling Price (Base + Profit Margin)
    # [REMOVED AS PER USER REQUEST - SHOW COST PRICE ONLY]
    # The dataframe already contains Cost Price from lines 228-230.
    
    # if not edf_details_df.empty:
    #     edf_details_df['Total Price'] = edf_details_df.apply(calc_item_selling_price, axis=1)
    #     edf_details_df['Unit Price'] = edf_details_df['Total Price'] / edf_details_df['Qty'].replace(0, 1)

    return {
        "total_material_base_cost": total_material_base_cost,
        "labor_actual_cost": labor_actual_cost,
        "total_project_cost": total_project_cost,
        "total_profit": final_profit,
        "bill_amount": bill_amount,
        "advance_amount": advance_amount,
        "mat_sell": mat_sell,
        "disp_lt": labor_actual_cost,
        "rounded_grand_total": bill_amount,
        "edf_details_df": edf_details_df
    }

def calculate_profit_row(row):
    """Calculates the profit for a single row in an estimate."""
    qty = float(row.get('Qty', 0))
    base_rate = float(row.get('Base Rate', 0))
    # unit = row.get('Unit', 'pcs')
    total_sell = float(row.get('Total Sell Price', 0))
    # factor = CONVERSIONS.get(unit, 1.0)
    total_cost = base_rate * qty
    return total_sell - total_cost

def create_item_dataframe(items):
    """
    Creates and validates a DataFrame for items.

    Args:
        items (list): A list of item dictionaries.

    Returns:
        pd.DataFrame: A validated DataFrame with the required columns.
    """
    # Normalize keys if needed (handle legacy 'base_rate' vs 'Base Rate')
    normalized_items = []
    for i in items:
        # Create a copy to avoid mutating session state directly here
        ni = i.copy()
        if 'base_rate' in ni and 'Base Rate' not in ni:
            ni['Base Rate'] = ni['base_rate']
        if 'unit' in ni and 'Unit' not in ni:
            ni['Unit'] = ni['unit']
        if 'item' in ni and 'Item' not in ni:
            ni['Item'] = ni['item']
        normalized_items.append(ni)
        
    df = pd.DataFrame(normalized_items)
    for col in ["Qty", "Item", "Unit", "Base Rate", "Total Price", "Unit Price"]:
        if col not in df.columns:
            df[col] = "" if col in ["Item", "Unit"] else 0.0
            
    # Explicitly handle NaNs for numeric columns to avoid 'None' in UI
    for col in ["Qty", "Base Rate", "Total Price", "Unit Price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    column_order = ['Qty', 'Item', 'Unit', 'Base Rate', 'Unit Price', 'Total Price']
    df = df.reindex(columns=column_order, fill_value="")
    return df
