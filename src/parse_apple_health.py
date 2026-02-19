import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os

def parse_health_data(file_path):
    # Features to extract
    user_info = {'age': 30, 'gender': 'Male'} # Defaults
    sleep_records = []
    heart_rates = []
    
    # Use iterparse for memory efficiency
    context = ET.iterparse(file_path, events=('start', 'end'))
    
    current_night = None
    
    for event, elem in context:
        if event == 'start':
            if elem.tag == 'Me':
                # Extract DOB and Gender
                dob = elem.get('HKCharacteristicTypeIdentifierDateOfBirth')
                if dob:
                    birth_year = int(dob[:4])
                    user_info['age'] = datetime.now().year - birth_year
                gender = elem.get('HKCharacteristicTypeIdentifierBiologicalSex')
                if gender == 'HKBiologicalSexMale': user_info['gender'] = 'Male'
                elif gender == 'HKBiologicalSexFemale': user_info['gender'] = 'Female'
            
            if elem.tag == 'Record':
                record_type = elem.get('type')
                
                # Sleep Analysis
                if record_type == 'HKCategoryTypeIdentifierSleepAnalysis':
                    value = elem.get('value')
                    # HKCategoryValueSleepAnalysisAsleepCore, AsleepDeep, AsleepREM, AsleepUnspecified
                    start = datetime.strptime(elem.get('startDate'), '%Y-%m-%d %H:%M:%S %z')
                    end = datetime.strptime(elem.get('endDate'), '%Y-%m-%d %H:%M:%S %z')
                    sleep_records.append({
                        'type': value,
                        'start': start,
                        'end': end,
                        'duration': (end - start).total_seconds() / 3600
                    })
                
                # Heart Rate
                if record_type == 'HKQuantityTypeIdentifierHeartRate':
                    start = datetime.strptime(elem.get('startDate'), '%Y-%m-%d %H:%M:%S %z')
                    value = float(elem.get('value'))
                    heart_rates.append({'time': start, 'value': value})
        
        if event == 'end':
            elem.clear() # Clear element from memory

    if not sleep_records:
        return None

    # Sort sleep records by start time
    sleep_records.sort(key=lambda x: x['start'])
    
    # Group by night (e.g., records within 12 hours of each other)
    # For simplicity, let's take the most recent group
    latest_end = sleep_records[-1]['end']
    target_night_start = latest_end - timedelta(hours=14)
    
    night_records = [r for r in sleep_records if r['start'] > target_night_start]
    
    # Aggregate Metrics
    total_duration = sum(r['duration'] for r in night_records if 'Asleep' in r['type'])
    rem_duration = sum(r['duration'] for r in night_records if 'REM' in r['type'])
    deep_duration = sum(r['duration'] for r in night_records if 'Deep' in r['type'])
    core_duration = sum(r['duration'] for r in night_records if 'Core' in r['type'] or 'Unspecified' in r['type'])
    
    # Awakenings (estimate by gaps or 'InBed' status)
    # Simple estimate: number of distinct 'Asleep' segments
    awakenings = len([r for r in night_records if 'Asleep' in r['type']]) - 1
    if awakenings < 0: awakenings = 0

    # Heart Rate for that night
    night_hrs = [hr['value'] for hr in heart_rates if target_night_start <= hr['time'] <= latest_end]
    avg_hr = sum(night_hrs) / len(night_hrs) if night_hrs else 65.0
    
    # Calculate percentages
    rem_pct = (rem_duration / total_duration * 100) if total_duration > 0 else 0
    deep_pct = (deep_duration / total_duration * 100) if total_duration > 0 else 0
    
    result = {
        "age": user_info['age'],
        "gender": user_info['gender'],
        "sleep_duration_hr": round(total_duration, 2),
        "heart_rate": round(avg_hr, 1),
        "stress_level": 3.0, # Defaulting stress level
        "rem_percent": round(rem_pct, 1),
        "deep_percent": round(deep_pct, 1),
        "awakenings": float(awakenings),
        "breathing_disturbances_elevated": False
    }
    
    return result

if __name__ == "__main__":
    xml_path = 'data/personal_data/apple_health_export/export.xml'
    if os.path.exists(xml_path):
        data = parse_health_data(xml_path)
        print(json.dumps(data, indent=2))
    else:
        print("Export file not found.")
