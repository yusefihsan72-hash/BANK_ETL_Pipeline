# 🚀 QUICK START GUIDE - June 8 Presentation

## Current State
✅ Project is **fully configured and ready to run**
✅ All dependencies installed (Python 3.13)
✅ Database warehouse initialized with data
✅ Sample data and visualizations ready

---

## To Run Everything (One Command):

### Open Terminal and run BOTH in separate terminals:

**Terminal 1 - ETL Pipeline** (monitors incoming data)
```powershell
C:/Users/AL-ed/AppData/Local/Programs/Python/Python313/python.exe run.py
```

**Terminal 2 - Streamlit Dashboard** (analytics interface)
```powershell
C:/Users/AL-ed/AppData/Local/Programs/Python/Python313/python.exe -m streamlit run dashboard/app.py --logger.level=error
```

Dashboard will be available at: **http://localhost:8501**

---

## Quick Commands for June 8:

### Generate Fresh Sample Data
```powershell
C:/Users/AL-ed/AppData/Local/Programs/Python/Python313/python.exe generate_sample_data.py
```

### Check Warehouse Status
```powershell
C:/Users/AL-ed/AppData/Local/Programs/Python/Python313/python.exe check_warehouse_stats.py
```

### Generate Data Visualizations
```powershell
C:/Users/AL-ed/AppData/Local/Programs/Python/Python313/python.exe visualize_data.py
```

---

## Current Data Status (May 23, 2026):

| Component | Count |
|-----------|-------|
| Customers | 1,150 |
| Transactions | 9,736 |
| Archive Files | 2026/05/23/ |
| Dashboard Ready | ✅ |
| Warehouse | ✅ Initialized |

---

## Key Files Ready:
- ✅ `run.py` - Main ETL pipeline
- ✅ `dashboard/app.py` - Streamlit dashboard
- ✅ `generate_sample_data.py` - Fresh data generator
- ✅ `visualize_data.py` - Analytics charts
- ✅ `warehouse/bank_warehouse.db` - Populated database
- ✅ `reports/dashboard_visualization.png` - Saved charts

---

## Expected Runtime:
- **Pipeline startup**: ~2-3 seconds
- **Dashboard startup**: ~5-10 seconds
- **Data processing**: Automatic (10-second poll interval)

**Ready to present! 🎉**
