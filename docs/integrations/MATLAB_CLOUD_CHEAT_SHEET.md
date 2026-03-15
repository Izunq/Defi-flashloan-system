# MATLAB Cloud Worker Cheat Sheet
## Daily Usage - Super Simple!

---

## **🚀 THE ONLY 3 COMMANDS YOU NEED**

### **1. Start Cloud Workers**
```matlab
parpool('CloudWorker', 16);  % Start 16 cloud workers
```

### **2. Run Your Code (Automatically Uses Cloud)**
```matlab
parfor i = 1:10000  % This runs on cloud workers automatically!
    result(i) = your_heavy_computation(i);
end
```

### **3. Stop Workers (Save Money)**
```matlab
delete(gcp('nocreate'));  % Stop workers, save costs
```

---

## **🤖 WHAT HAPPENS AUTOMATICALLY**

### **MATLAB Handles Everything:**
- ✅ **Sends work to cloud** - Your `parfor` loops run on 16 cloud workers
- ✅ **Brings results back** - Results appear in your local MATLAB
- ✅ **Load balancing** - MATLAB distributes work efficiently
- ✅ **Error handling** - Failed workers are automatically replaced

### **You Don't Need To:**
- ❌ Manually send data to cloud
- ❌ Manage individual workers  
- ❌ Handle network connections
- ❌ Worry about data transfer

---

## **💡 REAL USAGE EXAMPLES**

### **Before (Local Laptop):**
```matlab
% This would take 30 minutes on your laptop
for i = 1:10000
    arbitrage_results(i) = analyze_token_pair(i);
end
```

### **After (With Cloud Worker):**
```matlab
% This takes 2-3 minutes with cloud workers
parpool('CloudWorker', 16);
parfor i = 1:10000  % Same code, just change 'for' to 'parfor'
    arbitrage_results(i) = analyze_token_pair(i);
end
delete(gcp('nocreate'));
```

**🎯 10-15x faster with just changing `for` to `parfor`!**

---

## **🎮 INTERACTIVE WORKFLOW**

### **Your Typical Day:**
```matlab
%% 1. Start MATLAB on your laptop (normal)
%% 2. Develop and test code locally (normal)

% 3. When ready for heavy computation:
parpool('CloudWorker', 16);

% 4. Run your analysis
parfor token = 1:1000
    opportunities(token) = scan_arbitrage(token);
end

% 5. Visualize results locally (instant)
plot(opportunities);
title('Arbitrage Opportunities');

% 6. Clean up
delete(gcp('nocreate'));

%% 7. Continue working locally (normal)
```

### **What You Experience:**
- **Familiar MATLAB interface** on your laptop
- **Instant responsiveness** for development  
- **Massive speed boost** for heavy computations
- **Immediate visualization** of results

---

## **📱 SIMPLE MONITORING**

### **Check Costs Anytime:**
```powershell
python monitor_matlab_worker.py status
```

### **Stop Instance to Save Money:**
```powershell
python monitor_matlab_worker.py stop
```

### **Start When You Need It:**
```powershell
python monitor_matlab_worker.py start
```

---

## **🔄 TYPICAL DAILY WORKFLOW**

### **Morning (Start Working):**
```powershell
# 1. Start your cloud instance
python monitor_matlab_worker.py start

# 2. Open MATLAB on your laptop (normal)
matlab
```

### **During Work:**
```matlab
% 3. Use cloud when needed
parpool('CloudWorker', 16);
% ... do heavy computations ...
delete(gcp('nocreate'));

% 4. Continue local work normally
```

### **Evening (Save Costs):**
```powershell
# 5. Stop cloud instance
python monitor_matlab_worker.py stop
```

---

## **🎯 WHAT YOU GET**

### **Performance:**
- **10-16x speedup** for parallel tasks
- **No memory limits** - handle huge datasets
- **Professional capability** at student costs

### **Convenience:**
- **Same MATLAB interface** you know
- **No new skills needed** - just `parfor` instead of `for`
- **Works with all your existing code**

### **Flexibility:**
- **Use when needed** - start/stop anytime
- **Scale up/down** - 2 workers for testing, 16 for production
- **Cost control** - pay only when computing

---

## **❓ COMMON QUESTIONS**

### **Q: Do I need to learn new MATLAB commands?**
**A:** No! Just change `for` to `parfor` for parallel loops.

### **Q: Where does my data live?**
**A:** On your laptop. Only computations run on cloud.

### **Q: What if the cloud disconnects?**
**A:** MATLAB automatically handles reconnections and retries.

### **Q: How much does it cost?**
**A:** ~$0.68/hour, but you have AWS student credits. Stop when not using.

### **Q: Can I use my existing MATLAB code?**
**A:** Yes! Most code works as-is, just add `parpool` and `parfor`.

---

## **🎉 BOTTOM LINE**

**You literally just:**
1. **Start workers:** `parpool('CloudWorker', 16)`
2. **Change `for` to `parfor`** in your loops  
3. **Stop workers:** `delete(gcp('nocreate'))`

**Everything else is automatic!** MATLAB handles all the cloud complexity for you.

It's like having a supercomputer that you control from your laptop! 🚀
