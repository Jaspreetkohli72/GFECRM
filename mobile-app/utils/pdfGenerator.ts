import { EstimateItem, CalculationResult } from '../types';

export const generateInvoiceHTML = (
    clientName: string,
    result: CalculationResult,
    isFinal: boolean
): string => {
    const { items_with_totals, labor_actual_cost, rounded_grand_total, advance_amount, total_material_base_cost } = result;
    
    // Generating rows
    const rows = items_with_totals.map(item => `
        <tr class="item-row">
            <td class="desc">${item.Item}</td>
            <td class="qty">${item.Qty}</td>
            <td class="unit">${item.Unit}</td>
            <td class="amt">₹${item["Total Price"]?.toFixed(2)}</td>
        </tr>
    `).join('');

    const title = isFinal ? "INVOICE" : "ESTIMATE";
    const date = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

    return `
<html>
<head>
    <style>
        body { font-family: 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif; padding: 40px; color: #333; }
        .header { margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .company { font-size: 24px; font-weight: bold; color: #000; }
        .meta { margin-top: 10px; font-size: 14px; color: #555; display: flex; justify-content: space-between; }
        .title { font-size: 18px; font-weight: bold; margin-top: 20px; text-transform: uppercase; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }
        th { background: #f3f3f3; padding: 10px; border: 1px solid #ddd; text-align: left; font-weight: bold; }
        td { padding: 10px; border: 1px solid #ddd; }
        .qty, .unit, .amt { text-align: center; }
        .amt { text-align: right; }
        .totals { margin-top: 20px; text-align: right; font-size: 14px; }
        .grand-total { font-size: 18px; font-weight: bold; margin-top: 10px; }
        .footer { margin-top: 40px; font-size: 12px; color: #777; font-style: italic; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="company">Galaxy Fabrication Experts</div>
        <div class="meta">
            <span>Client: <strong>${clientName}</strong></span>
            <span>Date: ${date}</span>
        </div>
        <div class="title">${title}</div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 50%">Description</th>
                <th style="width: 15%">Qty</th>
                <th style="width: 15%">Unit</th>
                <th style="width: 20%">Amount (INR)</th>
            </tr>
        </thead>
        <tbody>
            ${rows}
        </tbody>
    </table>

    <div class="totals">
        <p>Material Cost: ₹${total_material_base_cost.toFixed(2)}</p>
        <p>Labor / Installation: ₹${labor_actual_cost.toFixed(2)}</p>
        <div class="grand-total">Grand Total: ₹${rounded_grand_total.toLocaleString('en-IN')}</div>
        ${!isFinal ? `<p style="color: #666; margin-top: 5px;">Advance Required: ₹${advance_amount.toLocaleString('en-IN')}</p>` : ''}
    </div>

    <div class="footer">
        ${isFinal ? "Thank you for your business!" : "NOTE: This is an estimate only. Final rates may vary based on actual site conditions. Valid for 7 days."}
    </div>
</body>
</html>
    `;
};
