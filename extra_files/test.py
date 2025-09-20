from djitellopy import Tello

tello = Tello()

tello.connect()
tello.takeoff()
tello.move_up(150)
tello.move_forward(100)
tello.move_back(100)
tello.land()