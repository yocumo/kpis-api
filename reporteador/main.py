


from datetime import datetime


def convert_date_format(date_str, input_formats=None, output_format="%d/%m/%Y"):
    
    if not input_formats:
        input_formats = [
            "%Y-%m-%d",  # YYYY-MM-DD (most recent error case)
            "%d-%m-%Y",  # DD-MM-YYYY
            "%m-%d-%Y",  # MM-DD-YYYY
            "%Y/%m/%d",  # YYYY/MM/DD
            "%d/%m/%Y",  # DD/MM/YYYY
        ]
    
    for fmt in input_formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime(output_format)
        except ValueError:
            continue
    
    print(f"Could not convert date: {date_str}")
    return date_str




print(convert_date_format('2024-11-30'))