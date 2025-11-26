import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict
from datetime import datetime
import uuid 

# --- Config ---
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds_file = 'credentials/service_account.json'
SHEET_NAME = "Investment_Db"

def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client

def parse_amount(amount_str):
    if isinstance(amount_str, (int, float)): return float(amount_str)
    try: return float(str(amount_str).replace(',', '').replace('฿', '').strip())
    except: return 0.0

def clean_key(key): return str(key).strip()

def parse_date(date_val):
    if not date_val: return None
    try:
        date_str = str(date_val).strip()
        if '-' in date_str: return datetime.strptime(date_str, "%Y-%m-%d")
        else: return datetime.strptime(date_str, "%d/%m/%Y")
    except: return None

# --- Settings Functions ---
def get_settings(only_active=False):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Settings")
        all_values = ws.get_all_values()
        categories, assets = [], []
        for row in all_values[1:]:
            # Category
            if len(row) >= 1 and row[0].strip():
                name = row[0].strip()
                is_active = str(row[1]).upper() == 'TRUE' if len(row) >= 2 else True
                target_percent = 0.0
                if len(row) >= 3 and row[2].strip():
                    try: target_percent = float(row[2].strip())
                    except: target_percent = 0.0
                if not only_active or is_active:
                    categories.append({'name': name, 'active': is_active, 'target': target_percent})
            # Asset
            if len(row) >= 4 and row[3].strip():
                name = row[3].strip()
                is_active = str(row[4]).upper() == 'TRUE' if len(row) >= 5 else True
                if not only_active or is_active: assets.append({'name': name, 'active': is_active})
        return {'categories': categories, 'assets': assets}
    except: return {'categories': [], 'assets': []}

def update_setting_status(setting_type, name, action, value=None):
    try:
        client = get_client()
        ws = client.open(SHEET_NAME).worksheet("Settings")
        all_values = ws.get_all_values()
        name_idx = 0 if setting_type == 'category' else 3
        active_idx = 1 if setting_type == 'category' else 4
        target_idx = 2
        search_name = str(name).strip().lower()
        
        if action == 'add':
            row_to_write = len(all_values) + 1
            for i, row in enumerate(all_values):
                if i == 0: continue
                if len(row) <= name_idx or row[name_idx] == "":
                    row_to_write = i + 1
                    break
            ws.update_cell(row_to_write, name_idx + 1, name)
            ws.update_cell(row_to_write, active_idx + 1, "TRUE")
            if setting_type == 'category': ws.update_cell(row_to_write, target_idx + 1, 0)
        elif action == 'toggle':
            for i, row in enumerate(all_values):
                curr_name = str(row[name_idx]).strip().lower() if len(row) > name_idx else ""
                if curr_name == search_name:
                    current_status = str(row[active_idx]).upper() == 'TRUE' if len(row) > active_idx else True
                    new_status = "FALSE" if current_status else "TRUE"
                    ws.update_cell(i + 1, active_idx + 1, new_status)
                    break
        elif action == 'update_target' and setting_type == 'category':
            for i, row in enumerate(all_values):
                curr_name = str(row[name_idx]).strip().lower() if len(row) > name_idx else ""
                if curr_name == search_name:
                    ws.update_cell(i + 1, target_idx + 1, value)
                    break
        return True
    except: return False

# --- Asset Records Functions ---
def get_asset_records(filter_name=None, filter_category=None, filter_year=None):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Current Asset")
        raw_data = ws.get_all_records()
        records = []
        for item in raw_data:
            clean_item = {clean_key(k): v for k, v in item.items()}
            record_id = str(clean_item.get('ID') or '').strip()
            name = str(clean_item.get('Description') or clean_item.get('Asset') or clean_item.get('Asset Name') or '').strip()
            category = str(clean_item.get('Category') or '').strip()
            date_val = str(clean_item.get('Date') or clean_item.get('date') or '').strip()
            amount = parse_amount(clean_item.get('Amount', 0))
            dt_obj = parse_date(date_val)
            if filter_name and filter_name.lower() not in name.lower(): continue
            if filter_category and filter_category != "" and filter_category != category: continue
            if filter_year and dt_obj:
                if dt_obj.year != int(filter_year): continue
            if filter_year and not dt_obj: continue
            display_date = date_val
            if dt_obj: display_date = dt_obj.strftime("%d/%m/%Y")
            records.append({'id': record_id, 'date': display_date, 'name': name, 'category': category, 'amount': amount, 'dt_obj': dt_obj})
        records.sort(key=lambda x: x['dt_obj'] if x['dt_obj'] else datetime.min, reverse=True)
        for r in records: 
            if 'dt_obj' in r: del r['dt_obj']
        return records
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def get_asset_chart_data(records):
    try:
        asset_data = defaultdict(lambda: defaultdict(float))
        all_assets = set()
        for rec in records:
            try: dt = datetime.strptime(rec['date'], "%d/%m/%Y")
            except: continue
            month_idx = dt.strftime("%m")
            name = rec['name']
            if asset_data[name][month_idx] == 0:
                asset_data[name][month_idx] = rec['amount']
                all_assets.add(name)
        datasets = []
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_keys = [f"{i:02d}" for i in range(1, 13)]
        colors = ['#4285F4', '#DB4437', '#F4B400', '#0F9D58', '#ab47bc', '#00acc1', '#ff7043', '#9e9e9e', '#5c6bc0', '#8d6e63']
        for i, asset_name in enumerate(sorted(list(all_assets))):
            data_points = []
            for m_key in month_keys:
                val = asset_data[asset_name][m_key]
                data_points.append(val if val != 0 else None) 
            datasets.append({'label': asset_name, 'data': data_points, 'borderColor': colors[i % len(colors)], 'backgroundColor': colors[i % len(colors)], 'fill': False, 'tension': 0.4})
        return {'labels': months, 'datasets': datasets}
    except Exception as e:
        return {'labels': [], 'datasets': []}

def add_asset_record(date, amount, description, category):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Current Asset")
        new_id = str(uuid.uuid4())
        row = [new_id, date, amount, description, category]
        ws.append_row(row)
        return True
    except Exception as e:
        print(f"❌ Error adding asset: {e}")
        return False

def add_asset_records_bulk(records):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Current Asset")
        rows_to_add = []
        for rec in records:
            new_id = str(uuid.uuid4())
            rows_to_add.append([new_id, rec['date'], rec['amount'], rec['name'], rec['category']])
        try: ws.append_rows(rows_to_add); return True
        except:
            for row in rows_to_add: ws.append_row(row)
            return True
    except: return False

def delete_asset_record(record_id):
    try:
        client = get_client()
        ws = client.open(SHEET_NAME).worksheet("Current Asset")
        cell = ws.find(record_id, in_column=1)
        if cell: ws.delete_rows(cell.row); return True
        return False
    except: return False

def update_asset_record(record_id, new_data):
    try:
        client = get_client()
        ws = client.open(SHEET_NAME).worksheet("Current Asset")
        cell = ws.find(record_id, in_column=1)
        if cell:
            row_num = cell.row
            ws.update_cell(row_num, 2, new_data['date'])
            ws.update_cell(row_num, 3, new_data['amount'])
            ws.update_cell(row_num, 4, new_data['name'])
            ws.update_cell(row_num, 5, new_data['category'])
            return True
        return False
    except: return False

def get_latest_portfolio_value():
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Current Asset")
        raw_data = ws.get_all_records()
        latest_assets = {}
        for item in raw_data:
            clean_item = {clean_key(k): v for k, v in item.items()}
            name = str(clean_item.get('Description') or clean_item.get('Asset') or clean_item.get('Asset Name') or '').strip()
            amount = parse_amount(clean_item.get('Amount', 0))
            date_val = parse_date(clean_item.get('Date') or clean_item.get('date'))
            if not name or not date_val: continue
            if name not in latest_assets or date_val > latest_assets[name]['date']:
                latest_assets[name] = {'date': date_val, 'amount': amount}
        total_value = sum(item['amount'] for item in latest_assets.values())
        return total_value
    except: return 0.0

# --- Investment Records Functions ---
def get_investment_records(filter_name=None, filter_category=None, filter_year=None, filter_action=None):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Investment")
        raw_data = ws.get_all_records()
        records = []
        for item in raw_data:
            clean_item = {clean_key(k): v for k, v in item.items()}
            record_id = str(clean_item.get('ID') or '').strip()
            date_val = str(clean_item.get('Date') or clean_item.get('date') or '').strip()
            action = str(clean_item.get('Action') or '').strip()
            name = str(clean_item.get('Asset') or clean_item.get('Description') or '').strip()
            category = str(clean_item.get('Category') or '').strip()
            qty = clean_item.get('Quantity')
            price = clean_item.get('Unit Price')
            amount = parse_amount(clean_item.get('Total Amount', 0))
            note = str(clean_item.get('Note') or '').strip()
            dt_obj = parse_date(date_val)
            if filter_name and filter_name.lower() not in name.lower(): continue
            if filter_category and filter_category != "" and filter_category != category: continue
            if filter_action and filter_action != "" and filter_action != action: continue
            if filter_year and dt_obj:
                if dt_obj.year != int(filter_year): continue
            if filter_year and not dt_obj: continue
            display_date = date_val
            if dt_obj: display_date = dt_obj.strftime("%d/%m/%Y")
            records.append({'id': record_id, 'date': display_date, 'action': action, 'name': name, 'category': category, 'qty': qty, 'price': price, 'amount': amount, 'note': note, 'dt_obj': dt_obj})
        records.sort(key=lambda x: x['dt_obj'] if x['dt_obj'] else datetime.min, reverse=True)
        for r in records: 
            if 'dt_obj' in r: del r['dt_obj']
        return records
    except Exception as e:
        print(f"❌ Error getting investments: {e}")
        return []

def get_investment_chart_data(records):
    try:
        monthly_deposit = defaultdict(float)
        monthly_withdraw = defaultdict(float)
        monthly_buy = defaultdict(float)
        for rec in records:
            try: dt = datetime.strptime(rec['date'], "%d/%m/%Y")
            except: continue
            month_idx = dt.strftime("%m")
            amount = rec['amount']
            action = rec['action'].lower()
            if action == 'deposit': monthly_deposit[month_idx] += abs(amount)
            elif action == 'withdraw': monthly_withdraw[month_idx] += abs(amount)
            elif action == 'buy': monthly_buy[month_idx] += abs(amount)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_keys = [f"{i:02d}" for i in range(1, 13)]
        data_deposit = [monthly_deposit[m] for m in month_keys]
        data_withdraw = [-monthly_withdraw[m] for m in month_keys] 
        data_buy = [monthly_buy[m] for m in month_keys]
        return {'labels': months, 'datasets': [{'type': 'bar', 'label': 'Deposit', 'data': data_deposit, 'backgroundColor': 'rgba(25, 135, 84, 0.7)', 'borderColor': '#198754', 'borderWidth': 1}, {'type': 'bar', 'label': 'Withdraw', 'data': data_withdraw, 'backgroundColor': 'rgba(220, 53, 69, 0.7)', 'borderColor': '#dc3545', 'borderWidth': 1}, {'type': 'line', 'label': 'Buy Volume', 'data': data_buy, 'borderColor': '#0d6efd', 'borderWidth': 2, 'fill': False, 'tension': 0.4}]}
    except: return {'labels': [], 'datasets': []}

def add_investment_record(data):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Investment")
        new_id = str(uuid.uuid4())
        row = [new_id, data['date'], data['action'], data['name'], data['category'], data['qty'], data['price'], data['amount'], data['note']]
        ws.append_row(row)
        return True
    except: return False

def add_investment_records_bulk(records):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Investment")
        rows_to_add = []
        for rec in records:
            new_id = str(uuid.uuid4())
            rows_to_add.append([new_id, rec['date'], rec['action'], rec['name'], rec['category'], rec['qty'], rec['price'], rec['amount'], rec['note']])
        try: ws.append_rows(rows_to_add); return True
        except: 
            for row in rows_to_add: ws.append_row(row)
            return True
    except Exception as e:
        print(f"❌ Error bulk adding investment: {e}")
        return False

def delete_investment_record(record_id):
    try:
        client = get_client()
        ws = client.open(SHEET_NAME).worksheet("Investment")
        cell = ws.find(record_id, in_column=1)
        if cell: ws.delete_rows(cell.row); return True
        return False
    except: return False

def update_investment_record(record_id, data):
    try:
        client = get_client()
        ws = client.open(SHEET_NAME).worksheet("Investment")
        cell = ws.find(record_id, in_column=1)
        if cell:
            row_num = cell.row
            updates = [{'range': f'B{row_num}', 'values': [[data['date']]]}, {'range': f'C{row_num}', 'values': [[data['action']]]}, {'range': f'D{row_num}', 'values': [[data['name']]]}, {'range': f'E{row_num}', 'values': [[data['category']]]}, {'range': f'F{row_num}', 'values': [[data['qty']]]}, {'range': f'G{row_num}', 'values': [[data['price']]]}, {'range': f'H{row_num}', 'values': [[data['amount']]]}, {'range': f'I{row_num}', 'values': [[data['note']]]}]
            ws.batch_update(updates)
            return True
        return False
    except: return False

# --- 🔥 Dividends Functions (เติมกลับมาให้แล้วครับ) 🔥 ---
def get_dividend_records(filter_name=None, filter_year=None):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Dividends")
        raw_data = ws.get_all_records()
        records = []
        for item in raw_data:
            clean_item = {clean_key(k): v for k, v in item.items()}
            record_id = str(clean_item.get('ID') or '').strip()
            date_val = str(clean_item.get('Date') or clean_item.get('date') or '').strip()
            name = str(clean_item.get('Asset Name') or clean_item.get('Asset') or '').strip()
            category = str(clean_item.get('Category') or '').strip()
            amount = parse_amount(clean_item.get('Dividend Amount') or clean_item.get('Amount'))
            reinvested = str(clean_item.get('Reinvested') or 'No').strip()
            note = str(clean_item.get('Note') or '').strip()
            dt_obj = parse_date(date_val)
            
            if filter_name and filter_name.lower() not in name.lower(): continue
            if filter_year and dt_obj:
                if dt_obj.year != int(filter_year): continue
            if filter_year and not dt_obj: continue

            display_date = date_val
            if dt_obj: display_date = dt_obj.strftime("%d/%m/%Y")
            
            records.append({'id': record_id, 'date': display_date, 'name': name, 'category': category, 'amount': amount, 'reinvested': reinvested, 'note': note, 'dt_obj': dt_obj})
        
        records.sort(key=lambda x: x['dt_obj'] if x['dt_obj'] else datetime.min, reverse=True)
        for r in records: 
            if 'dt_obj' in r: del r['dt_obj']
        return records
    except: return []

def add_dividend_record(data):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Dividends")
        new_id = str(uuid.uuid4())
        row = [new_id, data['date'], data['name'], data['category'], data['amount'], data['reinvested'], data['note']]
        ws.append_row(row)
        return True
    except: return False

def get_dividend_chart_data(records):
    try:
        monthly_div = defaultdict(float)
        for rec in records:
            try: dt = datetime.strptime(rec['date'], "%d/%m/%Y")
            except: continue
            month_idx = dt.strftime("%m")
            monthly_div[month_idx] += rec['amount']
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_keys = [f"{i:02d}" for i in range(1, 13)]
        data = [monthly_div[m] for m in month_keys]
        return {'labels': months, 'datasets': [{'label': 'Dividend Income', 'data': data, 'backgroundColor': 'rgba(255, 193, 7, 0.7)', 'borderColor': '#ffc107', 'borderWidth': 1}]}
    except: return {'labels': [], 'datasets': []}

# --- Dashboard Logic ---
def get_dashboard_data(start_date_str=None, end_date_str=None):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        filter_start = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        filter_end = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None

        active_settings = get_settings(only_active=True)
        category_targets = {c['name']: c['target'] for c in active_settings['categories']}
        active_asset_names = [a['name'] for a in active_settings['assets']]
        active_cat_names = [c['name'] for c in active_settings['categories']]

        # 1. Current Asset Logic
        ws_asset = sheet.worksheet("Current Asset")
        raw_assets = ws_asset.get_all_records()
        
        latest_assets_snapshot = {}
        category_current_value = defaultdict(float)
        asset_name_pivot_data = defaultdict(lambda: defaultdict(float)) 
        category_pivot_data = defaultdict(lambda: defaultdict(float)) 
        monthly_asset_total = defaultdict(float)

        for item in raw_assets:
            clean_item = {clean_key(k): v for k, v in item.items()}
            date_obj = parse_date(clean_item.get('Date') or clean_item.get('date'))
            if date_obj and filter_start and filter_end:
                if not (filter_start <= date_obj <= filter_end): continue

            amount = parse_amount(clean_item.get('Amount', 0))
            cat = str(clean_item.get('Category', 'Uncategorized')).strip()
            asset_name = str(clean_item.get('Description') or clean_item.get('Asset') or 'Unknown').strip()
            
            if date_obj:
                # Snapshot ล่าสุด
                if asset_name not in latest_assets_snapshot or date_obj > latest_assets_snapshot[asset_name]['date']:
                    latest_assets_snapshot[asset_name] = {'date': date_obj, 'amount': amount, 'category': cat}
                
                month_idx = date_obj.strftime("%m")
                asset_name_pivot_data[asset_name][month_idx] += amount
                category_pivot_data[cat][month_idx] += amount 
                monthly_asset_total[month_idx] += amount

        current_asset_value = sum(item['amount'] for item in latest_assets_snapshot.values())
        for item in latest_assets_snapshot.values():
            category_current_value[item['category']] += item['amount']

        allocation_table = []
        for cat_name, target_pct in category_targets.items():
            actual_val = category_current_value.get(cat_name, 0)
            actual_pct = (actual_val / current_asset_value * 100) if current_asset_value > 0 else 0
            diff_pct = actual_pct - target_pct
            target_val_thb = (target_pct / 100) * current_asset_value
            action_amount = target_val_thb - actual_val
            allocation_table.append({'category': cat_name, 'actual_val': actual_val, 'target_pct': target_pct, 'actual_pct': actual_pct, 'diff_pct': diff_pct, 'action_amount': action_amount, 'target_val': target_val_thb})
        
        inv_pivot_rows = []
        for cat in active_cat_names:
            row_data = {'name': cat, 'months': [], 'total': 0, 'avg': 0}
            cat_total = 0
            cat_latest_val = 0
            for item in latest_assets_snapshot.values():
                if item['category'] == cat:
                    cat_latest_val += item['amount']
            for i in range(1, 13):
                m_idx = f"{i:02d}"
                val = category_pivot_data[cat][m_idx]
                row_data['months'].append(val)
                cat_total += val
            row_data['total'] = cat_latest_val 
            row_data['avg'] = cat_total / 12 
            inv_pivot_rows.append(row_data)

        asset_pivot_rows = []
        for asset in active_asset_names:
            row_data = {'name': asset, 'months': [], 'total': 0, 'avg': 0}
            asset_total = 0
            latest_asset_val = latest_assets_snapshot.get(asset, {}).get('amount', 0)
            for i in range(1, 13):
                m_idx = f"{i:02d}"
                val = asset_name_pivot_data[asset][m_idx]
                row_data['months'].append(val)
                asset_total += val
            row_data['total'] = latest_asset_val 
            row_data['avg'] = asset_total / 12 
            asset_pivot_rows.append(row_data)

        ws_inv = sheet.worksheet("Investment")
        raw_txs = ws_inv.get_all_records()
        total_invested = 0
        monthly_invest_flow = defaultdict(float)
        
        for tx in raw_txs:
            clean_tx = {clean_key(k): v for k, v in tx.items()}
            date_obj = parse_date(clean_tx.get('Date') or clean_tx.get('date'))
            if date_obj and filter_start and filter_end:
                if not (filter_start <= date_obj <= filter_end): continue
            amount = parse_amount(clean_tx.get('Total Amount', 0))
            action = str(clean_tx.get('Action', '')).strip().lower()
            
            flow_amount = 0
            if action == 'deposit': flow_amount = abs(amount)
            elif action == 'withdraw': flow_amount = -abs(amount)
            total_invested += flow_amount
            
            if date_obj:
                month_idx = date_obj.strftime("%m")
                monthly_invest_flow[month_idx] += flow_amount

        summary_table_data = {'investment': [], 'asset': [], 'diff': [], 'diff_percent': [], 'total_inv': 0, 'total_asset': 0, 'total_diff': 0, 'total_diff_pct': 0}
        running_inv = 0
        for i in range(1, 13):
            m_idx = f"{i:02d}"
            running_inv += monthly_invest_flow[m_idx]
            curr_asset = monthly_asset_total[m_idx]
            if curr_asset == 0 and monthly_invest_flow[m_idx] == 0:
                display_inv = 0; display_diff = 0; display_diff_pct = 0
            else:
                display_inv = running_inv
                display_diff = curr_asset - running_inv
                display_diff_pct = (display_diff / running_inv) * 100 if running_inv > 0 else 0.0
            summary_table_data['investment'].append(display_inv)
            summary_table_data['asset'].append(curr_asset)
            summary_table_data['diff'].append(display_diff)
            summary_table_data['diff_percent'].append(display_diff_pct)

        summary_table_data['total_inv'] = running_inv
        summary_table_data['total_asset'] = current_asset_value
        summary_table_data['total_diff'] = current_asset_value - running_inv
        if running_inv > 0: summary_table_data['total_diff_pct'] = (summary_table_data['total_diff'] / running_inv) * 100
        else: summary_table_data['total_diff_pct'] = 0.0
        profit_loss = current_asset_value - total_invested

        return {
            "total_investment": total_invested,
            "current_asset": current_asset_value,
            "profit_loss": profit_loss,
            "pie_chart_labels": list(category_current_value.keys()),
            "pie_chart_data": list(category_current_value.values()),
            "line_chart_labels": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
            "line_chart_data": summary_table_data['investment'],
            "inv_pivot_table": inv_pivot_rows,
            "asset_pivot_table": asset_pivot_rows,
            "main_summary_table": summary_table_data,
            "allocation_table": allocation_table
        }
    except Exception as e:
        print(f"❌ Error in manager.py: {e}")
        return None
    
# 🔥 ฟังก์ชันใหม่: วิเคราะห์ปันผล (รายปี / รายเดือน) 🔥
def get_dividend_analysis_data(mode='yearly'):
    try:
        client = get_client()
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet("Dividends")
        raw_data = ws.get_all_records()
        
        data_map = defaultdict(float)
        
        for item in raw_data:
            clean_item = {clean_key(k): v for k, v in item.items()}
            amount = parse_amount(clean_item.get('Dividend Amount') or clean_item.get('Amount'))
            date_val = parse_date(clean_item.get('Date') or clean_item.get('date'))
            
            if date_val:
                if mode == 'monthly':
                    # Group by Month-Year (e.g., "2023-01") เพื่อดูไทม์ไลน์
                    key = date_val.strftime("%Y-%m")
                else:
                    # Group by Year (e.g., "2023") เพื่อดูภาพรวม
                    key = date_val.strftime("%Y")
                
                data_map[key] += amount
        
        # เรียงลำดับข้อมูลตามเวลา
        sorted_keys = sorted(data_map.keys())
        
        labels = []
        data = []
        
        for k in sorted_keys:
            if mode == 'monthly':
                # แปลง 2023-01 -> Jan 2023
                dt = datetime.strptime(k, "%Y-%m")
                labels.append(dt.strftime("%b %Y"))
            else:
                labels.append(k)
            
            data.append(data_map[k])
        
        # กำหนดสี
        if mode == 'monthly':
            # รายเดือน: แท่งสีทองเส้นขอบชัด
            bg_color = 'rgba(255, 193, 7, 0.6)'
            border_color = '#ffc107'
        else:
            # รายปี: ไล่เฉดสีสวยๆ
            bg_color = [
                'rgba(255, 99, 132, 0.7)', 'rgba(54, 162, 235, 0.7)', 'rgba(255, 206, 86, 0.7)',
                'rgba(75, 192, 192, 0.7)', 'rgba(153, 102, 255, 0.7)', 'rgba(255, 159, 64, 0.7)'
            ]
            border_color = '#fff'

        return {
            'labels': labels,
            'datasets': [{
                'label': 'Dividend Income',
                'data': data,
                'backgroundColor': bg_color,
                'borderColor': border_color,
                'borderWidth': 1
            }]
        }
    except Exception as e:
        print(f"❌ Error analyzing dividends: {e}")
        return {'labels': [], 'datasets': []}