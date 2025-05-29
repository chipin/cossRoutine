# cossRoutine

一個模組化的電信營運排程與自動化任務平台，支援多業務單元（如 CM、CTI、IP、QOS、INVOICE 等）定期例行作業的整合執行與結果記錄。專案使用 Python 為主要開發語言，搭配部分 PHP 與 Shell 腳本進行介接與任務調度。

---

## 📦 專案結構

```
cossRoutine/
├── ca/          # CA 授權模組
├── cm/          # Cable Modem 資訊與管理
├── cmts/        # CMTS 設備相關作業
├── cnr/         # 客訴與通報記錄處理
├── coss/        # 中心排程核心模組
├── cti/         # 來電顯示與話務系統支援
├── dta/         # 數據傳輸分析與報表
├── dtv/         # 數位電視服務相關作業
├── invoice/     # 營收與發票流程
├── ip/          # 公網 IP 管理與監控
├── isc/         # 設備狀態與線路巡檢
├── oems/        # 外部設備管理系統支援
├── qos/         # 品質監測（SNMP、Ping 等）
├── sms/         # 簡訊發送與事件告警
```

---

## 🚀 功能特性

- 支援多模組任務排程與定時執行（可與 cron 或 supervisor 整合）
- 每個模組可獨立部署與擴充（低耦合）
- 任務結果自動記錄與狀態回報
- 提供 CLI 執行介面，便於與 Jenkins、CI/CD 或後台排程系統整合
- 支援與內部資料庫（如 MariaDB / MSSQL）與設備 SNMP 資料整合

---

## 🔧 安裝方式

```bash
git clone https://github.com/chipin/cossRoutine.git
cd cossRoutine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

如有 PHP 或 Shell 腳本需求，請安裝相關套件：

```bash
sudo apt install php-cli curl jq
```

---

## ⚙️ 使用方式

```bash
# 執行單一模組任務
python3 run_module.py cm            # CM 模組
python3 run_module.py qos           # QOS 品質監控
python3 run_module.py invoice       # 發票作業

# 可搭配 crontab 每日排程
```

---

## 🛠️ 系統相依環境建議

- Python 3.8+
- PHP 7.4+（如有使用 PHP 腳本模組）
- MariaDB / MSSQL ODBC 驅動
- SNMP 網管設備（如 CMTS、Cable Modem）
- Linux/Unix 環境（建議使用 Ubuntu / Debian）

---

## 📈 模組化設計目標

本專案目標是提升跨部門例行作業的執行效率與可監控性，透過模組化與自動化架構，將重複任務統一管理，避免人工操作錯誤，並強化跨系統整合能力（如 Zabbix、Tesseract OCR、地址解析等應用）。

---

## 📄 授權條款

本專案以 MIT License 授權。詳見 [LICENSE](LICENSE)。

---

## 🙋 聯絡方式

由 [陳治平（Chipin Chen）](https://github.com/chipin) 開發與維護。  
若有合作需求或技術交流歡迎提出 issue 或 pull request。