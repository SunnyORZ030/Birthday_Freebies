# 🎂 Birthday Freebies - Starbucks 自動更新指南

## ✅ 已完成的設置

### 配置概述
- ✅ **執行時間**：每天 00:00 (午夜/12:00 AM)
- ✅ **執行腳本**：`/Users/sunny/Birthday_Freebies/scripts/watch-starbucks-cron.sh`
- ✅ **日誌位置**：`/Users/sunny/Birthday_Freebies/logs/starbucks-watch.log`
- ✅ **自動更新**：有變化時立即更新數據庫
- ✅ **重試機制**：最多重試 3 次，間隔 60 秒、5 分鐘、15 分鐘

---

## 📋 快速命令

### 查看 Cron 任務
```bash
crontab -l
```

### 查看執行日誌
```bash
# 查看最近 50 行
tail -50 /Users/sunny/Birthday_Freebies/logs/starbucks-watch.log

# 即時監視（持續查看新日誌）
tail -f /Users/sunny/Birthday_Freebies/logs/starbucks-watch.log
```

### 手動執行一次（測試）
```bash
/Users/sunny/Birthday_Freebies/scripts/watch-starbucks-cron.sh
```

### 查看最新狀態
```bash
curl http://localhost:3001/health/ingestion/starbucks | python3 -m json.tool
```

---

## 🔄 工作流程

每天 00:00 執行時：

1. **檢查源**：訪問 Starbucks 官網 `https://www.starbucks.com/rewards/terms/`
2. **對比方式**：使用 HTTP ETag/Last-Modified（節省帶寬）
3. **檢測變化**：SHA256 雜湊對比內容
4. **條件更新**：
   - ✅ **有變化**：提取新數據 → 更新數據庫 → 記錄日誌
   - ✅ **無變化**：略過操作 → 記錄日誌
5. **錯誤處理**：
   - 失敗時自動重試（最多 3 次，間隔遞增）
   - 記錄所有錯誤信息

---

## 🛠️ 進階管理

### 修改執行時間

編輯 crontab：
```bash
crontab -e
```

找到此行：
```
0 0 * * * /Users/sunny/Birthday_Freebies/scripts/watch-starbucks-cron.sh
```

**常見時間表：**
- `0 0 * * *` → 每天 00:00（午夜）
- `0 6 * * *` → 每天 06:00（早上 6 點）
- `0 12 * * *` → 每天 12:00（中午）
- `0 18 * * *` → 每天 18:00（傍晚）
- `*/30 * * * *` → 每 30 分鐘

修改後保存即可生效。

### 添加 Slack 或 Email 告警

編輯 `/Users/sunny/Birthday_Freebies/scripts/watch-starbucks-cron.sh`，取消註釋並設置：

```bash
export STARBUCKS_ALERT_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

當連續失敗 2 次時，會自動發送告警。

### 增加執行頻率

如要每 6 小時檢查一次，編輯 crontab：
```bash
crontab -e
```

改為：
```
0 */6 * * * /Users/sunny/Birthday_Freebies/scripts/watch-starbucks-cron.sh
```

### 臨時禁用任務

```bash
crontab -r
```

重新啟用：
```bash
cd /Users/sunny/Birthday_Freebies
crontab -e
# 添加此行：0 0 * * * /Users/sunny/Birthday_Freebies/scripts/watch-starbucks-cron.sh
```

---

## 📊 監控檢查表

### 每周檢查清單

- [ ] 查看日誌是否有異常：`tail -100 /Users/sunny/Birthday_Freebies/logs/starbucks-watch.log`
- [ ] 確認任務仍在 crontab 中：`crontab -l | grep starbucks`
- [ ] 檢查健康狀態：`curl http://localhost:3001/health/ingestion/starbucks`
- [ ] 驗證數據是否更新

### 異常排查

**症狀：日誌中有錯誤**
```bash
# 查看最新錯誤
grep -i "error\|failed" /Users/sunny/Birthday_Freebies/logs/starbucks-watch.log | tail -10
```

**症狀：任務沒有執行**
1. 檢查 Mac 是否進入睡眠模式（Cron 在睡眠時不執行）
2. 驗證 crontab：`crontab -l`
3. 手動測試腳本：`/Users/sunny/Birthday_Freebies/scripts/watch-starbucks-cron.sh`

**症狀：資料庫沒有更新**
```bash
# 查看最後一次成功時間
curl http://localhost:3001/health/ingestion/starbucks | grep last_success_at
```

---

## 📋 環境配置（自動設置）

Cron 腳本會自動設置以下環境變數：

```bash
STARBUCKS_INGEST_REGION="bay_area"              # 監視區域
STARBUCKS_WATCH_MAX_RETRIES="3"                  # 重試次數
STARBUCKS_WATCH_BACKOFF_SECONDS="60,300,900"    # 重試延遲
STARBUCKS_WATCH_STALE_AFTER_MINUTES="30"         # 陳舊閾值
STARBUCKS_WATCH_ALERT_FAILURE_THRESHOLD="2"      # 告警閾值
```

---

## ✨ 已啟用的功能

- [x] 每天自動檢查 Starbucks 官網
- [x] 智能變更檢測（HTTP 條件請求）
- [x] 自動數據庫更新
- [x] 完整日誌記錄
- [x] 錯誤重試機制
- [x] 冪等設計（不重複）
- [x] 健康檢查端點
- [x] 可選 Webhook 告警

---

## 📞 需要幫助？

**查看腳本內容：**
```bash
cat /Users/sunny/Birthday_Freebies/scripts/watch-starbucks-cron.sh
```

**查看完整日誌：**
```bash
cat /Users/sunny/Birthday_Freebies/logs/starbucks-watch.log
```

**手動測試一次：**
```bash
/Users/sunny/Birthday_Freebies/scripts/watch-starbucks-cron.sh
```

---

**恭喜！您的 Birthday Freebies 現在已經設置了全自動的 Starbucks 數據更新！🎉**
