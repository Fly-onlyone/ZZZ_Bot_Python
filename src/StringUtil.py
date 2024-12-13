import re
from datetime import timedelta, datetime


def extract_number_from_string(input_string):
    # Use regex to find the first sequence of digits in the string
    match = re.search(r"\d+", input_string)
    return int(match.group()) if match else None


def extract_and_convert_duration(input_string):
    # Regex to capture the start and end dates
    match = re.search(r"Duration:\s*(\d+/\d+)\s*–\s*(\d+/\d+)", input_string)
    if match:
        start_date, end_date = match.groups()

        # Convert each date to day/month format
        start_day, start_month = start_date.split("/")
        end_day, end_month = end_date.split("/")

        # Return the result in day/month format
        return {"Start": f"{start_month}/{start_day}", "End": f"{end_month}/{end_day}"}
    return None  # Return None if the pattern doesn't match


def calculate_return_time(input_time_str):
    # Parse the input string (format: "hour:min:sec")
    input_time_parts = list(map(int, input_time_str.split(":")))

    # Extract the hours, minutes, and seconds from the input
    input_hours = input_time_parts[0]
    input_minutes = input_time_parts[1]
    input_seconds = input_time_parts[2]

    # Create a timedelta from the input
    time_delta = timedelta(
        hours=input_hours, minutes=input_minutes, seconds=input_seconds
    )

    # Get the current time
    current_time = datetime.now()

    # Calculate the return time by adding the time delta to the current time
    return_time = current_time + time_delta

    # Format the return time in the format "hour:min dd/mm/yy"
    return return_time.strftime("%H:%M %d/%m/%y")


def extract_price(s):
    match = re.search(r"\d+", s)
    return int(match.group()) if match else None


def extract_number(s, side="left"):
    try:
        left, right = s.split("/")  # Split the string at the slash
        if side == "left":
            return int(left)
        elif side == "right":
            return int(right)
        else:
            raise ValueError("Invalid side parameter. Use 'left' or 'right'.")
    except (ValueError, IndexError):
        return None
