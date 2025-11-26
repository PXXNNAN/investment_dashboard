from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

# Import services
from services.dashboard_service import DashboardService
from services.settings_service import SettingsService
from services.asset_service import AssetService
from services.investment_service import InvestmentService
from services.dividend_service import DividendService

# Initialize services
dashboard_service = DashboardService()
settings_service = SettingsService()
asset_service = AssetService()
investment_service = InvestmentService()
dividend_service = DividendService()

app = Flask(__name__)
app.secret_key = 'supersecretkey' 

@app.route('/')
def index():
    try:
        current_year = datetime.now().year
        selected_year_arg = request.args.get('year')
        selected_year = int(selected_year_arg) if selected_year_arg else current_year
        start_date = f"{selected_year}-01-01"
        end_date = f"{selected_year}-12-31"
        year_options = list(range(current_year + 1, current_year - 5, -1))
        data = dashboard_service.get_dashboard_data(start_date_str=start_date, end_date_str=end_date)
        summary = {"total_investment": 0, "current_asset": 0, "profit_loss": 0, "start_date": start_date, "end_date": end_date}
        pie_labels, pie_values, line_labels, line_values, inv_pivot, asset_pivot, allocation_table = [], [], [], [], [], [], []
        main_table = {'investment': [0]*12, 'asset': [0]*12, 'diff': [0]*12, 'diff_percent': [0]*12, 'total_inv': 0, 'total_asset': 0, 'total_diff': 0, 'total_diff_pct': 0}
        if data:
            summary = {"total_investment": data.get('total_investment', 0), "current_asset": data.get('current_asset', 0), "profit_loss": data.get('profit_loss', 0), "start_date": start_date, "end_date": end_date}
            pie_labels = data.get('pie_chart_labels', [])
            pie_values = data.get('pie_chart_data', [])
            line_labels = data.get('line_chart_labels', [])
            line_values = data.get('line_chart_data', [])
            inv_pivot = data.get('inv_pivot_table', [])
            asset_pivot = data.get('asset_pivot_table', [])
            main_table = data.get('main_summary_table', main_table)
            allocation_table = data.get('allocation_table', [])
        return render_template('dashboard.html', summary=summary, pie_labels=pie_labels, pie_values=pie_values, line_labels=line_labels, line_values=line_values, inv_pivot=inv_pivot, asset_pivot=asset_pivot, main_table=main_table, allocation_table=allocation_table, selected_year=selected_year, year_options=year_options)
    except Exception as e: 
        return f"<h3>❌ Error in Index: {e}</h3>"

@app.route('/assets', methods=['GET', 'POST'])
def assets():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            data = {'date': request.form.get('date'), 'name': request.form.get('name'), 'amount': request.form.get('amount'), 'category': request.form.get('category')}
            if asset_service.add_record(data): 
                flash('บันทึกสำเร็จ', 'success')
            else: 
                flash('ล้มเหลว', 'danger')
        elif action == 'add_bulk':
            records = []
            for n, c, a in zip(request.form.getlist('name[]'), request.form.getlist('category[]'), request.form.getlist('amount[]')):
                if n.strip(): 
                    records.append({'date': request.form.get('date'), 'name': n.strip(), 'category': c.strip(), 'amount': a.strip()})
            if records and asset_service.add_records_bulk(records): 
                flash(f'บันทึก {len(records)} รายการ', 'success')
            else: 
                flash('ล้มเหลว', 'danger')
        elif action == 'delete':
            if asset_service.delete_record(request.form.get('id')): 
                flash('ลบสำเร็จ', 'success')
            else: 
                flash('ลบล้มเหลว', 'danger')
        elif action == 'edit':
            data = {'date': request.form.get('date'), 'name': request.form.get('name'), 'amount': request.form.get('amount'), 'category': request.form.get('category')}
            if asset_service.update_record(request.form.get('id'), data): 
                flash('แก้ไขสำเร็จ', 'success')
            else: 
                flash('แก้ไขล้มเหลว', 'danger')
        return redirect(url_for('assets'))
    
    current_year = datetime.now().year
    selected_year = int(request.args.get('year') or current_year)
    year_options = list(range(current_year + 1, current_year - 5, -1))
    filter_name = request.args.get('name')
    filter_cat = request.args.get('category')
    records = asset_service.get_records(filter_name, filter_cat, selected_year)
    chart_data = asset_service.get_chart_data(records)
    settings = settings_service.get_settings(only_active=True)
    latest_total_value = asset_service.get_latest_portfolio_value()
    return render_template('assets.html', asset_records=records, categories=[c['name'] for c in settings['categories']], assets=[a['name'] for a in settings['assets']], selected_name=filter_name, selected_category=filter_cat, selected_year=selected_year, year_options=year_options, latest_total_value=latest_total_value, chart_data=chart_data)

@app.route('/investments', methods=['GET', 'POST'])
def investments():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            data = {'date': request.form.get('date'), 'action': request.form.get('type'), 'name': request.form.get('name'), 'category': request.form.get('category'), 'qty': request.form.get('quantity'), 'price': request.form.get('price'), 'amount': request.form.get('amount'), 'note': request.form.get('note')}
            if investment_service.add_record(data): 
                flash('บันทึกสำเร็จ', 'success')
            else: 
                flash('ล้มเหลว', 'danger')
        elif action == 'add_bulk':
            date_val = request.form.get('date')
            records = []
            for t,n,c,q,p,a,nt in zip(request.form.getlist('type[]'), request.form.getlist('name[]'), request.form.getlist('category[]'), request.form.getlist('quantity[]'), request.form.getlist('price[]'), request.form.getlist('amount[]'), request.form.getlist('note[]')):
                if n.strip(): 
                    records.append({'date': date_val, 'action': t, 'name': n, 'category': c, 'qty': q, 'price': p, 'amount': a, 'note': nt})
            if records and investment_service.add_records_bulk(records): 
                flash(f'บันทึก {len(records)} รายการ', 'success')
            else: 
                flash('ล้มเหลว', 'danger')
        elif action == 'delete':
            if investment_service.delete_record(request.form.get('id')): 
                flash('ลบสำเร็จ', 'success')
            else: 
                flash('ลบล้มเหลว', 'danger')
        elif action == 'edit':
            data = {'date': request.form.get('date'), 'action': request.form.get('type'), 'name': request.form.get('name'), 'category': request.form.get('category'), 'qty': request.form.get('quantity'), 'price': request.form.get('price'), 'amount': request.form.get('amount'), 'note': request.form.get('note')}
            if investment_service.update_record(request.form.get('id'), data): 
                flash('แก้ไขสำเร็จ', 'success')
            else: 
                flash('แก้ไขล้มเหลว', 'danger')
        return redirect(url_for('investments'))
    
    current_year = datetime.now().year
    selected_year = int(request.args.get('year') or current_year)
    year_options = list(range(current_year + 1, current_year - 5, -1))
    filter_name = request.args.get('name')
    filter_cat = request.args.get('category')
    filter_action = request.args.get('action')
    records = investment_service.get_records(filter_name, filter_cat, selected_year, filter_action)
    chart_data = investment_service.get_chart_data(records)
    settings = settings_service.get_settings(only_active=True)
    return render_template('investments.html', records=records, categories=[c['name'] for c in settings['categories']], assets=[a['name'] for a in settings['assets']], selected_year=selected_year, year_options=year_options, selected_name=filter_name, selected_category=filter_cat, selected_action=filter_action, chart_data=chart_data)

@app.route('/dividends', methods=['GET', 'POST'])
def dividends():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            data = {'date': request.form.get('date'), 'name': request.form.get('name'), 'category': request.form.get('category'), 'amount': request.form.get('amount'), 'reinvested': 'Yes' if request.form.get('reinvested') else 'No', 'note': request.form.get('note')}
            if dividend_service.add_record(data): 
                flash('บันทึกสำเร็จ', 'success')
            else: 
                flash('ล้มเหลว', 'danger')
        return redirect(url_for('dividends'))
    
    current_year = datetime.now().year
    selected_year = int(request.args.get('year') or current_year)
    year_options = list(range(current_year + 1, current_year - 5, -1))
    filter_name = request.args.get('name')
    records = dividend_service.get_records(filter_name, selected_year)
    chart_data = dividend_service.get_chart_data(records)
    settings = settings_service.get_settings(only_active=True)
    total_div = sum(r['amount'] for r in records)
    avg_div = total_div / 12 if total_div > 0 else 0
    return render_template('dividends.html', records=records, chart_data=chart_data, settings=settings, categories=[c['name'] for c in settings['categories']], assets=[a['name'] for a in settings['assets']], selected_year=selected_year, year_options=year_options, selected_name=filter_name, total_div=total_div, avg_div=avg_div)

@app.route('/dashboard/dividend-yoy')
def dashboard_dividend_yoy():
    mode = request.args.get('mode', 'yearly')
    filter_name = request.args.get('name')
    
    chart_data = dividend_service.get_analysis_data(mode, filter_name)
    
    # ดึง Assets เพื่อทำ Dropdown
    settings = settings_service.get_settings(only_active=True)
    assets = [a['name'] for a in settings['assets']]
    
    return render_template('dashboard_dividend.html', 
                           chart_data=chart_data, 
                           selected_mode=mode,
                           selected_name=filter_name,
                           assets=assets)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        type_ = request.form.get('type')
        value = request.form.get('value')
        target_val = request.form.get('target_percent')
        success = False
        if action == 'update_target': 
            success = settings_service.update_setting_status(type_, value, action, target_val)
        elif value: 
            success = settings_service.update_setting_status(type_, value, action)
        if success: 
            flash('บันทึกสำเร็จ', 'success')
        else: 
            flash('ล้มเหลว', 'danger')
        return redirect(url_for('settings'))
    
    data = settings_service.get_settings(only_active=False)
    total_target = sum(c['target'] for c in data['categories'] if c['active'])
    return render_template('settings.html', categories=data['categories'], assets=data['assets'], total_target=total_target)

if __name__ == '__main__':
    print("🌍 Starting Server at http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)