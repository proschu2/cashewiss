# Cashewiss 🇨🇭
**Swiss Finance Integration Engine for Cashew Budgeting**  
*Securely transform Swiss banking data for Cashew imports*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features ✨
✅ **Currently Supported**  
- **Viseca ONE Credit Cards** (API integration)  
- **SwissCards Credit Cards** (CSV file processing)  

🔜 **Coming Soon**  
- Migros Bank (CSV support)  
- Yuh (CSV support)  

## Installation 📦
```bash
uv add cashewiss
```

## Configuration ⚙️
Create config.yml:

```yaml
credentials:
  viseca:
    client_id: YOUR_CLIENT_ID
    client_secret: YOUR_CLIENT_SECRET

paths:
  csv_directory: ./statements/
```
## Set up environment:


## Data Transformation 🔄
Transactions are converted to Cashew's required [format](https://github.com/jameskokoska/Cashew?tab=readme-ov-file#parameters):

License 📄
MIT License - See LICENSE for details

Disclaimer: This project is not affiliated with Visa, SwissCards, Migros Bank, Yuh, or the Cashew team. Always keep your financial credentials secure.