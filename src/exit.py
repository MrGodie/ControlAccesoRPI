import RPi.GPIO as GPIO
import time
from config import BOCINA
from gpio_handler import pwm_servo

def reproducir_audio_exito():
    GPIO.output(BOCINA, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(BOCINA, GPIO.LOW)

def activar_actuador():
    pwm_servo.ChangeDutyCycle(7)   # posición abierta
    time.sleep(2)
    pwm_servo.ChangeDutyCycle(2)   # posición cerrada