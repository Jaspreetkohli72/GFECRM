import { EstimateItem, EstimateData, CalculationResult, Settings, LaborRole } from '../types';

export const normalize_margins = (margins: any, global_settings: Settings): number => {
    if (margins === null || margins === undefined) {
        return Number(global_settings.profit_margin ?? 15);
    }
    if (typeof margins === 'object') {
        return Number(margins.profit_margin ?? global_settings.profit_margin ?? 15);
    }
    return Number(margins);
};

export const calculate_estimate_details = (
    items: EstimateItem[],
    days: number,
    margins: any,
    global_settings: Settings,
    labor_details: LaborRole[] = [],
    welders = 0,
    helpers = 0
): CalculationResult => {
    const profit_margin = normalize_margins(margins, global_settings);
    
    // Calculate Material Cost (Base)
    let total_material_base_cost = 0;
    const items_with_totals = items.map(item => {
        const qty = Number(item.Qty || 0);
        const base = Number(item['Base Rate'] || 0);
        const total = qty * base;
        total_material_base_cost += total;
        
        return {
            ...item,
            "Total Price": total,
            "Unit Price": base // As per python logic: unit price is just base rate
        };
    });

    const mat_sell = total_material_base_cost; // Selling price sum (if we applied margin per item, but Python code sums cost)

    // Calculate Labor Cost
    let labor_actual_cost = 0;
    
    if (labor_details && labor_details.length > 0) {
        labor_details.forEach(role => {
            labor_actual_cost += (role.count * role.rate * days);
        });
    } else {
        // Legacy
        const welder_rate = Number(global_settings.welder_daily_rate ?? 500.0);
        const helper_rate = Number(global_settings.helper_daily_rate ?? 300.0);
        labor_actual_cost = (welders * welder_rate * days) + (helpers * helper_rate * days);
    }

    // Total Project Cost
    const total_project_cost = total_material_base_cost + labor_actual_cost;

    // Profit
    const profit_amount = total_project_cost * (profit_margin / 100.0);

    // Bill Amount
    const raw_bill_amount = total_project_cost + profit_amount;
    const bill_amount = Math.round(raw_bill_amount);

    // Final Profit (derived from rounded bill)
    const final_profit = bill_amount - total_project_cost;

    // Advance
    const adv_pct = Number(global_settings.advance_percentage ?? 10.0);
    const advance_amount = Math.round(bill_amount * (adv_pct / 100.0));

    return {
        total_material_base_cost,
        labor_actual_cost,
        total_project_cost,
        total_profit: final_profit,
        bill_amount,
        advance_amount,
        mat_sell,
        rounded_grand_total: bill_amount,
        items_with_totals
    };
};
