import time
from DroneBlocksTelloSimulator import SimulatedDrone

# Initialize the drone (replace with your simulator key)
drone = SimulatedDrone("3cb58c8e-f0b2-4d65-95ca-4ad3e4681983")

# Takeoff
drone.takeoff()
time.sleep(1)

# Fly in a square pattern:
drone.fly_forward(20, 'in')
time.sleep(1)
drone.fly_right(20, 'in')
time.sleep(1)
drone.fly_backward(20, 'in')
time.sleep(1)
drone.fly_left(20, 'in')
time.sleep(1)




# Land the drone
drone.land()