from flask import Flask, render_template, request, redirect, url_for, flash
from manager import (
    get_dashboard_data, 
    get_settings, 
    update_setting_status, 
    get_asset_records, 
    add_asset_record, 
    add_asset_records_bulk,
    get_latest_portfolio_value, 
    delete_asset_record, 
    update_asset_record,
    get_asset_chart_data,
    # Investment functions
    get_investment_records,
    add_investment_record,
    add_investment_records_bulk,
    delete_investment_record,
    update_investment_record,
    get_investment_chart_data
)
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey' # จำเป็นสำหรับการใช้งาน flash messages

# --- 1. หน้า Dashboard (หน้าแรก) ---
@app.route('/')
def index():
    try:
        # 1. จัดการตัวกรองปี (Year Filter)
        current_year = datetime.now().year
        # รับค่าปีจาก URL query parameter (ถ้าไม่มีให้ใช้ปีปัจจุบัน)
        selected_year_arg = request.args.get('year')
        if selected_year_arg:
            selected_year = int(selected_year_arg)
        else:
            selected_year = current_year
        
        # กำหนดวันเริ่มต้น-สิ้นสุดของปีที่เลือก
        start_date = f"{selected_year}-01-01"
        end_date = f"{selected_year}-12-31"
        
        # สร้างตัวเลือกปีสำหรับ Dropdown (ย้อนหลัง 5 ปี ถึง 1 ปีข้างหน้า)
        year_options = list(range(current_year + 1, current_year - 5, -1))

        # 2. ดึงข้อมูล Dashboard จาก manager
        data = get_dashboard_data(start_date_str=start_date, end_date_str=end_date)
        
        # เตรียมตัวแปร Default กัน Error
        summary = {"total_investment": 0, "current_asset": 0, "profit_loss": 0, "start_date": start_date, "end_date": end_date}
        pie_labels, pie_values = [], []
        line_labels, line_values = [], []
        inv_pivot, asset_pivot = [], []
        allocation_table = []
        # กำหนด structure เริ่มต้นให้ครบถ้วน
        main_table = {
            'investment': [0]*12, 
            'asset': [0]*12, 
            'diff': [0]*12, 
            'diff_percent': [0]*12, 
            'total_inv': 0, 
            'total_asset': 0, 
            'total_diff': 0, 
            'total_diff_pct': 0
        }

        if data:
            summary = {
                "total_investment": data.get('total_investment', 0),
                "current_asset": data.get('current_asset', 0),
                "profit_loss": data.get('profit_loss', 0),
                "start_date": start_date,
                "end_date": end_date
            }
            pie_labels = data.get('pie_chart_labels', [])
            pie_values = data.get('pie_chart_data', [])
            line_labels = data.get('line_chart_labels', [])
            line_values = data.get('line_chart_data', [])
            inv_pivot = data.get('inv_pivot_table', [])
            asset_pivot = data.get('asset_pivot_table', [])
            
            # ตารางสรุปหลัก (Investment vs Asset vs Diff)
            # ใช้ get พร้อม default value ที่เราเตรียมไว้
            main_table = data.get('main_summary_table', main_table)
            
            # ตาราง Rebalancing (Target vs Actual)
            allocation_table = data.get('allocation_table', [])

        return render_template('dashboard.html', 
                            summary=summary, 
                            pie_labels=pie_labels, 
                            pie_values=pie_values, 
                            line_labels=line_labels, 
                            line_values=line_values, 
                            inv_pivot=inv_pivot, 
                            asset_pivot=asset_pivot, 
                            main_table=main_table, 
                            allocation_table=allocation_table, 
                            selected_year=selected_year, 
                            year_options=year_options)
                            
    except Exception as e:
        return f"<h3>❌ Error in Index Route: {e}</h3>"

# --- 2. หน้า Current Asset (จัดการสินทรัพย์) ---
@app.route('/assets', methods=['GET', 'POST'])
def assets():
    # --- ส่วนจัดการ POST Request (Add/Edit/Delete) ---
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Action: เพิ่มข้อมูลใหม่ (รายการเดียว)
        if action == 'add':
            date_val = request.form.get('date')
            name_val = request.form.get('name')
            category_val = request.form.get('category')
            amount_val = request.form.get('amount')
            if date_val and name_val and amount_val:
                if add_asset_record(date_val, amount_val, name_val, category_val):
                    flash('บันทึกข้อมูลเรียบร้อย!', 'success')
                else: 
                    flash('บันทึกล้มเหลว', 'danger')
        
        # Action: เพิ่มข้อมูลแบบกลุ่ม (Bulk)
        elif action == 'add_bulk':
            date_val = request.form.get('date') 
            names = request.form.getlist('name[]')
            categories = request.form.getlist('category[]')
            amounts = request.form.getlist('amount[]')
            
            records_to_add = []
            for n, c, a in zip(names, categories, amounts):
                if n.strip() and c.strip() and a.strip(): 
                    records_to_add.append({
                        'date': date_val,
                        'name': n.strip(),
                        'category': c.strip(),
                        'amount': a.strip()
                    })
            
            if records_to_add:
                if add_asset_records_bulk(records_to_add):
                    flash(f'บันทึก {len(records_to_add)} รายการเรียบร้อย!', 'success')
                else:
                    flash('บันทึกข้อมูลกลุ่มล้มเหลว (ตรวจสอบ Terminal)', 'danger')
            else:
                flash('ไม่มีข้อมูลที่ถูกต้องให้บันทึก', 'warning')

        # Action: ลบข้อมูล
        elif action == 'delete':
            record_id = request.form.get('id')
            if delete_asset_record(record_id):
                flash('ลบข้อมูลเรียบร้อย!', 'success')
            else: 
                flash('ลบข้อมูลล้มเหลว', 'danger')

        # Action: แก้ไขข้อมูล
        elif action == 'edit':
            record_id = request.form.get('id')
            new_data = {
                'date': request.form.get('date'),
                'name': request.form.get('name'),
                'amount': request.form.get('amount'),
                'category': request.form.get('category')
            }
            if update_asset_record(request.form.get('id'), new_data):
                flash('แก้ไขข้อมูลเรียบร้อย!', 'success')
            else: 
                flash('แก้ไขข้อมูลล้มเหลว', 'danger')

        return redirect(url_for('assets'))

    # --- ส่วนจัดการ GET Request (แสดงผล & Filter) ---
    
    # 1. จัดการ Filter
    current_year = datetime.now().year
    selected_year_arg = request.args.get('year')
    if selected_year_arg:
        selected_year = int(selected_year_arg)
    else:
        selected_year = current_year
        
    year_options = list(range(current_year + 1, current_year - 5, -1))
    
    filter_name = request.args.get('name')
    filter_category = request.args.get('category')
    
    # 2. ดึงข้อมูลรายการสินทรัพย์ (ส่ง filter ปีไปด้วย)
    records = get_asset_records(filter_name, filter_category, selected_year)
    
    # 3. เตรียมข้อมูลสำหรับกราฟ Line Chart
    chart_data = get_asset_chart_data(records)
    
    # 4. ดึงตัวเลือกสำหรับ Dropdown (เฉพาะที่ Active)
    settings = get_settings(only_active=True)
    
    # 5. ดึงยอดรวมล่าสุด (Latest Snapshot)
    latest_total_value = get_latest_portfolio_value()
    
    return render_template('assets.html', 
                           asset_records=records, 
                           categories=[c['name'] for c in settings['categories']], 
                           assets=[a['name'] for a in settings['assets']], 
                           selected_name=filter_name, 
                           selected_category=filter_category,
                           selected_year=selected_year, 
                           year_options=year_options, 
                           latest_total_value=latest_total_value, 
                           chart_data=chart_data)

# --- 3. หน้า Investments (บันทึกการลงทุน) ---
@app.route('/investments', methods=['GET', 'POST'])
def investments():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            data = {'date': request.form.get('date'), 'action': request.form.get('type'), 'name': request.form.get('name'), 'category': request.form.get('category'), 'qty': request.form.get('quantity'), 'price': request.form.get('price'), 'amount': request.form.get('amount'), 'note': request.form.get('note')}
            if add_investment_record(data): flash('บันทึกสำเร็จ', 'success')
            else: flash('ล้มเหลว', 'danger')
        elif action == 'add_bulk':
            date_val = request.form.get('date')
            records = []
            for t,n,c,q,p,a,nt in zip(request.form.getlist('type[]'), request.form.getlist('name[]'), request.form.getlist('category[]'), request.form.getlist('quantity[]'), request.form.getlist('price[]'), request.form.getlist('amount[]'), request.form.getlist('note[]')):
                if n.strip(): records.append({'date': date_val, 'action': t, 'name': n, 'category': c, 'qty': q, 'price': p, 'amount': a, 'note': nt})
            if records and add_investment_records_bulk(records): flash(f'บันทึก {len(records)} รายการ', 'success')
            else: flash('ล้มเหลว', 'danger')
        elif action == 'delete':
            if delete_investment_record(request.form.get('id')): flash('ลบสำเร็จ', 'success')
            else: flash('ลบล้มเหลว', 'danger')
        elif action == 'edit':
            data = {'date': request.form.get('date'), 'action': request.form.get('type'), 'name': request.form.get('name'), 'category': request.form.get('category'), 'qty': request.form.get('quantity'), 'price': request.form.get('price'), 'amount': request.form.get('amount'), 'note': request.form.get('note')}
            if update_investment_record(request.form.get('id'), data): flash('แก้ไขสำเร็จ', 'success')
            else: flash('แก้ไขล้มเหลว', 'danger')
        return redirect(url_for('investments'))

    current_year = datetime.now().year
    selected_year = int(request.args.get('year') or current_year)
    year_options = list(range(current_year + 1, current_year - 5, -1))
    filter_name = request.args.get('name')
    filter_cat = request.args.get('category')
    filter_action = request.args.get('action')
    
    records = get_investment_records(filter_name, filter_cat, selected_year, filter_action)
    chart_data = get_investment_chart_data(records)
    
    # 🔥 ดึงข้อมูล Settings (Asset List) เพื่อส่งไปหน้าเว็บ 🔥
    settings = get_settings(only_active=True)
    
    return render_template('investments.html', 
                           records=records, 
                           categories=[c['name'] for c in settings['categories']], 
                           # 🔥 ส่ง assets ไปด้วย เพื่อใช้ใน Datalist 🔥
                           assets=[a['name'] for a in settings['assets']], 
                           selected_year=selected_year, 
                           year_options=year_options, 
                           selected_name=filter_name, 
                           selected_category=filter_cat, 
                           selected_action=filter_action, 
                           chart_data=chart_data)

# --- 4. หน้า Settings (ตั้งค่า) ---
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        type_ = request.form.get('type')
        value = request.form.get('value')
        target_val = request.form.get('target_percent')
        
        success = False
        if action == 'update_target': 
            success = update_setting_status(type_, value, action, target_val)
        elif value: 
            success = update_setting_status(type_, value, action)
            
        if success: 
            flash('บันทึกข้อมูลสำเร็จ!', 'success')
        else: 
            flash('เกิดข้อผิดพลาด', 'danger')
        
        return redirect(url_for('settings'))
        
    data = get_settings(only_active=False)
    total_target = sum(c['target'] for c in data['categories'] if c['active'])
    
    return render_template('settings.html', 
                           categories=data['categories'], 
                           assets=data['assets'], 
                           total_target=total_target)

if __name__ == '__main__':
    print("🌍 Starting Server at http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)