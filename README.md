# Fan Control

I had a problem: I would forget to turn on the fan at the start of my spin bike
workout, and when I realized I wanted it on I would have to stop, get off the
bike, and turn on the fan.

This project is a solution to that problem.

The code monitors the output from the gyroscope sensors on an [MPU6050](), and
when it detects movement it turns on the fan. It turns off the fan when motion
is no longer detected.

[MPU6050]: https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/

This project is written in [MicroPython][] and runs on an [ESP8266][]. The fan is controlled using the HTTP API available on a [Tasmota][]-enabled [Sonoff S31][] switch.

[micropython]: https://micropython.org/
[esp8266]: https://en.wikipedia.org/wiki/ESP8266
[tasmota]: https://tasmota.github.io/docs/
[sonoff s31]: https://sonoff.tech/product/smart-plug/s31-s31lite/
