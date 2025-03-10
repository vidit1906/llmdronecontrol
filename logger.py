import time
import csv
from djitellopy import Tello

# Open a CSV file to log all sensor data after each command.
csv_file = open("drone_data_log.csv", "w", newline="")
csv_writer = csv.writer(csv_file)
# CSV header: timestamp, command, speed, battery, flight_time, height, temperature, attitude, barometer, tof_distance
csv_writer.writerow(["timestamp", "command", "speed", "battery", "flight_time", "height", "temperature", "attitude", "barometer", "tof_distance"])

# Initialize the Tello drone and connect.
tello = Tello()
tello.connect()
time.sleep(1)

# Instead of using the built-in query_* methods (which try to convert values to int),
# we override them to simply call send_read_command and return the raw string.
tello.query_speed = lambda: tello.send_read_command("speed?")
tello.query_flight_time = lambda: tello.send_read_command("time?")
tello.query_height = lambda: tello.send_read_command("height?")
tello.query_temperature = lambda: tello.send_read_command("temp?")
tello.query_battery = lambda: tello.send_read_command("battery?")
tello.query_barometer = lambda: tello.send_read_command("baro?")
tello.query_distance_tof = lambda: tello.send_read_command("tof?")
# Leave query_attitude unchanged (it returns a dictionary) 
# or alternatively, you could override it to return a raw string:
# tello.query_attitude = lambda: tello.send_read_command("attitude?")

# Command 1: takeoff
tello.takeoff()
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "takeoff",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 2: move_up(50)
tello.move_up(50)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_up(50)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 3: move_forward(100)
tello.move_forward(100)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_forward(100)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 4: move_left(50)
tello.move_left(50)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_left(50)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 5: move_right(50)
tello.move_right(50)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_right(50)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 6: move_down(50)
tello.move_down(50)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_down(50)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 7: rotate_clockwise(90)
tello.rotate_clockwise(90)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "rotate_clockwise(90)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 8: move_back(100)
tello.move_back(100)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_back(100)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 9: flip_forward()
tello.flip_forward()
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "flip_forward()",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 10: flip_left()
tello.flip_left()
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "flip_left()",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 11: flip_right()
tello.flip_right()
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "flip_right()",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 12: flip_back()
tello.flip_back()
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "flip_back()",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 13: move_up(30)
tello.move_up(30)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_up(30)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 14: move_forward(30)
tello.move_forward(30)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_forward(30)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 15: move_down(30)
tello.move_down(30)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_down(30)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 16: rotate_counter_clockwise(45)
tello.rotate_counter_clockwise(45)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "rotate_counter_clockwise(45)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 17: move_right(40)
tello.move_right(40)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_right(40)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 18: move_left(40)
tello.move_left(40)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_left(40)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 19: move_back(30)
tello.move_back(30)
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "move_back(30)",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

# Command 20: land
tello.land()
time.sleep(2)
csv_writer.writerow([
    time.time(),
    "land",
    tello.query_speed(),
    tello.query_battery(),
    tello.query_flight_time(),
    tello.query_height(),
    tello.query_temperature(),
    str(tello.query_attitude()),
    tello.query_barometer(),
    tello.query_distance_tof()
])

csv_file.close()