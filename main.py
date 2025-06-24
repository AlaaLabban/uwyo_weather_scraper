import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import re


def scrape_weather_data_robust(start_date, end_date, station_code="OEJN"):


    print(f"🌤️  Robust Weather Scraper - Handles Missing Values")
    print(f"Station: {station_code}")
    print(f"Date range: {start_date} to {end_date}")
    print("=" * 60)

    # Generate date list
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)

    all_data = []

    for i, date in enumerate(dates, 1):
        print(f"Scraping {date}... ({i}/{len(dates)})")

        try:
            # Build URL
            url = f"https://weather.uwyo.edu/cgi-bin/wyowx.fcgi?TYPE=sflist&DATE={date}&HOUR=24&UNITS=M&STATION={station_code}"

            # Make request
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"  Error: Status {response.status_code}")
                continue

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            pre_tag = soup.find('pre')

            if not pre_tag:
                print(f"  No data found")
                continue

            # Get text content and find header information
            text = pre_tag.get_text()
            lines = text.split('\n')

            # Find the header line to understand column positions
            header_info = find_header_positions(lines)

            # Process each data line individually
            day_records = 0
            filtered_records = 0
            gus_lines = 0
            target_day = date[-2:]  # Last 2 digits of date (day)

            for line in lines:
                line_original = line
                line = line.strip()
                if line.startswith(station_code):
                    # Parse the line using fixed-width positions
                    parsed_record = parse_weather_line_fixed_width(line_original, date, header_info)

                    if parsed_record:
                        # Check if this record belongs to the target date
                        if should_include_record(parsed_record, target_day):
                            all_data.append(parsed_record)
                            day_records += 1
                            if parsed_record.get('Wind_Gust_ms') is not None:
                                gus_lines += 1
                        else:
                            filtered_records += 1

            print(f"  Found {day_records} records ({gus_lines} with gust data), filtered out {filtered_records}")

            # Be nice to the server
            time.sleep(1)

        except Exception as e:
            print(f"  Error for {date}: {e}")
            continue

    # Save to Excel
    if all_data:
        print(f"\n✅ Total records collected: {len(all_data)}")


        df = pd.DataFrame(all_data)

        # Reorder columns for better readability
        column_order = [
            'Date', 'Station', 'Time', 'Pressure_hPa', 'Temperature_C',
            'Dewpoint_C', 'Humidity_percent', 'Wind_Direction_deg',
            'Wind_Speed_ms', 'Wind_Gust_ms', 'Visibility_km', 'Clouds_1', 'Clouds_2',
            'Clouds_3', 'Clouds_4', 'Weather', 'Raw_Line'
        ]

        # Only include columns that exist
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]

        # Create output directory
        os.makedirs('output', exist_ok=True)

        # Save to Excel with proper formatting
        output_file = f'output/weather_data_ROBUST_{station_code}_{start_date}_to_{end_date}.xlsx'

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Weather Data', index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets['Weather Data']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 25)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"📁 Data saved to: {output_file}")

        # Show summary
        print(f"\n📊 Data Summary:")
        print(f"Records: {len(df)}")
        print(f"Temperature range: {df['Temperature_C'].min():.1f}°C to {df['Temperature_C'].max():.1f}°C")
        print(f"Humidity range: {df['Humidity_percent'].min():.1f}% to {df['Humidity_percent'].max():.1f}%")

        # Show missing value statistics
        print(f"\n📋 Missing Value Statistics:")
        for col in ['Pressure_hPa', 'Temperature_C', 'Dewpoint_C', 'Humidity_percent',
                    'Wind_Direction_deg', 'Wind_Speed_ms', 'Wind_Gust_ms', 'Visibility_km']:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                total_count = len(df)
                missing_pct = (missing_count / total_count) * 100
                print(f"  {col}: {missing_count}/{total_count} missing ({missing_pct:.1f}%)")

        # Show wind data summary
        if 'Wind_Gust_ms' in df.columns:
            gust_records = df['Wind_Gust_ms'].notna().sum()
            if gust_records > 0:
                print(f"\nWind gust data: {gust_records} records with gust measurements")
                print(f"Gust range: {df['Wind_Gust_ms'].min():.1f} to {df['Wind_Gust_ms'].max():.1f} m/s")

        # Show cloud and weather data summary
        cloud_cols = [col for col in df.columns if col.startswith('Clouds_')]
        if cloud_cols:
            print(f"\nCloud data summary:")
            for col in cloud_cols:
                non_empty = df[col].notna().sum()
                if non_empty > 0:
                    unique_values = df[col].dropna().unique()[:3]
                    print(f"  {col}: {non_empty} entries, examples: {list(unique_values)}")

        # Show first few records
        print(f"\n📋 Sample data:")
        display_cols = ['Time', 'Temperature_C', 'Wind_Speed_ms', 'Wind_Gust_ms', 'Visibility_km', 'Weather']
        available_cols = [col for col in display_cols if col in df.columns]
        print(df[available_cols].head(8).to_string(index=False))

        return df
    else:
        print("❌ No data collected")
        return None


def find_header_positions(lines):

    header_info = {
        'has_gus': False,
        'positions': {}
    }

    try:
        # Look for header lines
        header_line = None
        units_line = None

        for i, line in enumerate(lines):
            line_upper = line.upper()
            if 'STN' in line_upper and 'TIME' in line_upper and 'TMP' in line_upper:
                header_line = line
                if i + 1 < len(lines):
                    units_line = lines[i + 1]
                break

        if header_line:
            # Check if GUS column is present
            if 'GUS' in header_line.upper():
                header_info['has_gus'] = True

            # Find approximate column positions
            # This is a simplified approach - in practice, you might need more sophisticated parsing
            header_info['positions'] = {
                'STN': (0, 4),
                'TIME': (5, 12),
                'ALTM': (13, 19),
                'TMP': (20, 23),
                'DEW': (24, 27),
                'RH': (28, 31),
                'DIR': (32, 35),
                'SPD': (36, 39),
            }

            if header_info['has_gus']:
                header_info['positions'].update({
                    'GUS': (40, 43),
                    'VIS': (44, 48),
                    'CLOUDS_START': 49
                })
            else:
                header_info['positions'].update({
                    'VIS': (40, 44),
                    'CLOUDS_START': 45
                })

    except Exception as e:
        print(f"  Warning: Could not parse header positions: {e}")

    return header_info


def parse_weather_line_fixed_width(line, date, header_info):

    try:
        # Initialize record
        record = {
            'Date': date,
            'Raw_Line': line.strip()
        }

        # Extract values using fixed positions
        positions = header_info.get('positions', {})

        # Basic fields (always present)
        record['Station'] = extract_field(line, positions.get('STN', (0, 4))).strip()
        record['Time'] = extract_field(line, positions.get('TIME', (5, 12))).strip()
        record['Pressure_hPa'] = safe_float(extract_field(line, positions.get('ALTM', (13, 19))))
        record['Temperature_C'] = safe_float(extract_field(line, positions.get('TMP', (20, 23))))
        record['Dewpoint_C'] = safe_float(extract_field(line, positions.get('DEW', (24, 27))))
        record['Humidity_percent'] = safe_float(extract_field(line, positions.get('RH', (28, 31))))
        record['Wind_Direction_deg'] = safe_float(extract_field(line, positions.get('DIR', (32, 35))))
        record['Wind_Speed_ms'] = safe_float(extract_field(line, positions.get('SPD', (36, 39))))

        # Handle optional GUS column
        if header_info.get('has_gus', False):
            record['Wind_Gust_ms'] = safe_float(extract_field(line, positions.get('GUS', (40, 43))))
            record['Visibility_km'] = safe_float(extract_field(line, positions.get('VIS', (44, 48))))
            clouds_start = positions.get('CLOUDS_START', 49)
        else:
            record['Wind_Gust_ms'] = None
            record['Visibility_km'] = safe_float(extract_field(line, positions.get('VIS', (40, 44))))
            clouds_start = positions.get('CLOUDS_START', 45)

        # Extract clouds and weather from the remaining part
        if len(line) > clouds_start:
            remaining_text = line[clouds_start:].strip()
            if remaining_text:
                # Split remaining text and classify
                remaining_parts = remaining_text.split()

                cloud_data = []
                weather_data = []

                for part in remaining_parts:
                    if is_cloud_code_enhanced(part):
                        cloud_data.append(part)
                    elif is_weather_code_enhanced(part):
                        weather_data.append(part)
                    else:
                        # Default classification
                        if part.isdigit() and len(part) == 3:
                            cloud_data.append(part)
                        else:
                            weather_data.append(part)

                # Assign cloud data to cloud columns (max 4)
                record['Clouds_1'] = cloud_data[0] if len(cloud_data) > 0 else None
                record['Clouds_2'] = cloud_data[1] if len(cloud_data) > 1 else None
                record['Clouds_3'] = cloud_data[2] if len(cloud_data) > 2 else None
                record['Clouds_4'] = cloud_data[3] if len(cloud_data) > 3 else None

                # Combine weather data
                record['Weather'] = ' '.join(weather_data) if weather_data else None
            else:
                # No clouds or weather data
                record['Clouds_1'] = None
                record['Clouds_2'] = None
                record['Clouds_3'] = None
                record['Clouds_4'] = None
                record['Weather'] = None
        else:
            # Line too short for clouds/weather
            record['Clouds_1'] = None
            record['Clouds_2'] = None
            record['Clouds_3'] = None
            record['Clouds_4'] = None
            record['Weather'] = None

        return record

    except Exception as e:
        print(f"    Error parsing line: {line[:50]}... - {e}")
        return None


def extract_field(line, position_tuple):
    """Extract a field from a specific position in the line"""
    try:
        start, end = position_tuple
        if start < len(line):
            if end <= len(line):
                return line[start:end]
            else:
                return line[start:]
        return ""
    except:
        return ""


def is_cloud_code_enhanced(part):
    """Enhanced cloud code detection including prefixed codes"""
    cloud_layer_codes = ['SCT', 'BKN', 'OVC', 'FEW', 'CLR', 'SKC', 'NSC', 'VV']

    # Remove common prefixes and suffixes
    clean_part = part.upper()
    if clean_part.startswith('-'):
        clean_part = clean_part[1:]
    elif clean_part.startswith('+'):
        clean_part = clean_part[1:]

    if clean_part.endswith('***'):
        clean_part = clean_part[:-3]

    # Check if the cleaned part starts with a cloud layer code
    for code in cloud_layer_codes:
        if clean_part.startswith(code):
            return True

    # Pattern matching for cloud codes
    cloud_pattern = r'^[-+]?(SCT|BKN|OVC|FEW|CLR|SKC|NSC|VV)\d*\**$'
    if re.match(cloud_pattern, part.upper()):
        return True

    # Pure 3-digit numbers (cloud heights)
    if part.isdigit() and len(part) == 3:
        return True

    # Special cloud codes
    special_cloud_codes = ['CAVOK', 'NSC', 'NCD']
    if part.upper() in special_cloud_codes:
        return True

    return False


def is_weather_code_enhanced(part):
    """Enhanced weather code detection"""
    weather_codes = [
        'RA', 'SN', 'DZ', 'SG', 'IC', 'PL', 'GR', 'GS', 'UP',
        'FG', 'BR', 'HZ', 'FU', 'VA', 'DU', 'SA', 'PY',
        'SQ', 'FC', 'SS', 'DS', 'PO', 'TS',
        'BLDU', 'BLSA', 'BLSN', 'DRDU', 'DRSA',
        'FZRA', 'FZDZ', 'FZFG', 'SHRA', 'SHSN', 'SHGR', 'SHGS',
        'TSRA', 'TSSN', 'TSGR', 'TSGS', 'MIFG', 'PRFG', 'BCFG',
        'VCSH', 'VCTS', 'VCFG', 'VCPO', 'VCBLDU', 'VCBLSA', 'VCBLSN'
    ]

    # Check exact matches
    if part.upper() in weather_codes:
        return True

    # Check with intensity modifiers
    if len(part) > 1:
        if part.startswith('-') or part.startswith('+'):
            base_code = part[1:].upper()
            if base_code in weather_codes:
                return True

    # Check for vicinity codes
    if part.upper().startswith('VC') and len(part) > 2:
        base_code = part[2:].upper()
        if base_code in [code for code in weather_codes if not code.startswith('VC')]:
            return True

    return False


def should_include_record(record, target_day):
    """Check if a record should be included based on date matching"""
    try:
        time_str = record.get('Time', '')

        if not time_str or '/' not in time_str:
            return True

        day_part = time_str.split('/')[0]
        record_day = day_part.lstrip('0') or '0'
        target_day_clean = target_day.lstrip('0') or '0'

        return record_day == target_day_clean

    except Exception as e:
        return True


def safe_float(value):
    """Safely convert string to float, handling missing values"""
    try:
        if value and value.strip() and value.strip() not in ['-', '', '   ']:
            return float(value.strip())
    except:
        pass
    return None


# Run the scraper
if __name__ == "__main__":
    # Configuration - modify these as needed
    START_DATE = "20150101"
    END_DATE = "20241231"  # A few days for testing
    STATION = "OEJN"

    try:
        result = scrape_weather_data_robust(START_DATE, END_DATE, STATION)
        if result is not None:
            print(f"\n🎉 Success! Robust parsing should handle missing values correctly!")
            print(f"📁 Missing values are now properly handled without shifting other columns.")
        else:
            print(f"\n⚠️  No data found. Try different dates.")
    except Exception as e:
        print(f"❌ Script error: {e}")
