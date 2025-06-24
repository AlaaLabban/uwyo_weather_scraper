# uwyo_surface_weather_data_scraper
Python script that scrapes hourly Surface weather data from the University of Wyoming's weather database and exports it to Excel format.

*Created by [Alaa Labban](https://github.com/AlaaLabban)*

University of Wyoming's Surface weather Data database link: https://weather.uwyo.edu/surface/meteorogram/index.shtml

note: this script was tested on OEJN station from 20150101 to 20241231 and given perfect results 

## 🌤️ Features

- **Robust Data Parsing**: Handles missing values without column misalignment
- **Flexible Column Detection**: Automatically detects optional wind gust (GUS) column
- **Enhanced Cloud/Weather Classification**: Properly separates cloud data from weather phenomena
- **Date Filtering**: Filters out previous day records from 25-hour datasets
- **Excel Export**: Clean, formatted Excel output with auto-adjusted column widths
- **Comprehensive Error Handling**: Graceful handling of network issues and parsing errors

## 📋 Requirements

Install the required Python packages:

\`\`\`bash
pip install requests beautifulsoup4 pandas openpyxl
\`\`\`
## 🚀 Quick Start

1. **Basic Usage**:
   ```python
   python scripts/uwyo_weather_scraper.py
   \`\`\`

2. **Configure Date Range and Station**:
   Edit the configuration section in the script:
   ```python
   START_DATE = "20200327"  # YYYYMMDD format
   END_DATE = "20200329"    # YYYYMMDD format
   STATION = "OEJN"         # Station code
   \`\`\`

## 📊 Output Format

The script generates an Excel file with the following columns:

| Column | Description | Unit |
|--------|-------------|------|
| Date | Date of observation | YYYYMMDD |
| Station | Weather station code | - |
| Time | Time of observation | DD/HHMM |
| Pressure_hPa | Atmospheric pressure | hPa |
| Temperature_C | Air temperature | °C |
| Dewpoint_C | Dew point temperature | °C |
| Humidity_percent | Relative humidity | % |
| Wind_Direction_deg | Wind direction | degrees |
| Wind_Speed_ms | Wind speed | m/s |
| Wind_Gust_ms | Wind gust speed (optional) | m/s |
| Visibility_km | Visibility | km |
| Clouds_1-4 | Cloud layer information | - |
| Weather | Weather phenomena | - |

## 🔧 Key Features Explained

### Missing Value Handling
The scraper uses fixed-width parsing to handle missing values correctly:
- Missing values don't cause column misalignment
- Each field is extracted from its designated position
- Missing data is marked as `None` in the output

### Cloud vs Weather Classification
Enhanced detection algorithms properly classify:
- **Cloud codes**: SCT, BKN, OVC, FEW, CLR, -OVC***, etc.
- **Weather phenomena**: RA, SN, FG, HZ, TS, BLSN, etc.
- **Cloud heights**: 3-digit numbers (015, 040, 100, etc.)

### Optional GUS Column Detection
Automatically detects when wind gust data is available:
- Analyzes header structure for each date
- Adjusts column positions accordingly
- Maintains data integrity across different formats

### Date Filtering
Filters out previous day records from 25-hour datasets:
- University of Wyoming includes last hour of previous day
- Script filters to show only records from target date
- Prevents duplicate or misaligned time series data

## 📁 Output Files

Generated files are saved in the `output/` directory:
- **Filename format**: `weather_data_ROBUST_{STATION}_{START_DATE}_to_{END_DATE}.xlsx`
- **Example**: `weather_data_ROBUST_OEJN_20200327_to_20200329.xlsx`

## 📈 Data Quality Features

## 📝 Data Source

Data is sourced from the University of Wyoming Department of Atmospheric Science:
- **URL**: https://weather.uwyo.edu/
- **Data Type**: Surface meteorological observations
- **Update Frequency**: Hourly
- **Coverage**: Global weather stations

## 🔄 Version History

- **v1.0**: Basic weather data scraping
- **v2.0**: Added cloud/weather separation
- **v3.0**: Enhanced missing value handling
- **v4.0**: Robust fixed-width parsing (current)

---

**Note**: Always verify the scraped data against the original source for critical applications. Weather data accuracy is essential for safety-related decisions.


