import time

def get_formatted_datetime():
    """
    Get the current datetime as a formatted string.

    Returns:
        str: The current datetime in the format "YYYY-MM-DD HH:MM:SS".
    """
    current_datetime = time.localtime()
    return "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(
        current_datetime[0], current_datetime[1], current_datetime[2],
        current_datetime[3], current_datetime[4], current_datetime[5]
    )
