export interface InventoryItem {
  id?: number;
  item_name: string;
  base_rate: number;
  unit: string;
}

export interface EstimateItem {
  Item: string;
  Qty: number;
  Unit: string;
  "Base Rate": number;
  "Total Price"?: number;
  "Unit Price"?: number;
}

export interface LaborRole {
  role: string;
  count: number;
  rate: number;
}

export interface EstimateData {
  items: EstimateItem[];
  days: number;
  margins: number | { profit_margin: number }; // Simplify
  labor_details: LaborRole[];
  welders?: number; // Legacy
  helpers?: number; // Legacy
}

export interface CalculationResult {
  total_material_base_cost: number;
  labor_actual_cost: number;
  total_project_cost: number;
  total_profit: number;
  bill_amount: number;
  advance_amount: number;
  mat_sell: number;
  rounded_grand_total: number;
  items_with_totals: EstimateItem[];
}

export interface Settings {
    profit_margin?: number;
    daily_labor_cost?: number;
    welder_daily_rate?: number;
    helper_daily_rate?: number;
    advance_percentage?: number;
}
