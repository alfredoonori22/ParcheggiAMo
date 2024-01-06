# ParcheggiAMo
This project's purpose is to build and manage a real-time map of the parking situation in the city, helping citizens to park more easily.

<p align="center">
  <img width="630" height="360" src="https://github.com/alfredoonori22/ParcheggiAMo/assets/62024453/02ea687a-b1f4-4a66-9e73-f3453b7c3898">
</p>

It is implemented via a Telegram bot, called ParcheggiAMo, that allows you to access the map of available parking spots, with an indication of their prices and distances. You can also book and pay the spot online, avoiding the hassle of looking for coins or tickets.

Other than that, there's a website that can be used as an interface and a cloud database useful for tracking data and predict future trends.

This toy-project wants to contribute in improving the quality of life of citizens, reducing the stress, time, and money spent for parking. Moreover, it wants to promote a more sustainable mobility, decreasing traffic and pollution.

<p align="center">
  <img width="720" height="360" src="https://github.com/alfredoonori22/ParcheggiAMo/assets/62024453/049c51fb-4404-430f-a637-03af5e273c09">
</p>

## Telegram Bot
There are three main functionality:
-  Searching for a parking lot without having a reservation
-  Booking a parking lot online and then make use of the reservation code to access it
-  Checking the status of an already parked car
  
<p align="center">
  <img width="600" height="380" src="https://github.com/alfredoonori22/ParcheggiAMo/assets/62024453/aaf20a2c-0cce-4183-9c51-9ae8f0b8777c">
</p>

<p align="center">
  <img width="720" height="360" src="https://github.com/alfredoonori22/ParcheggiAMo/assets/62024453/be54150f-a3f2-44b9-9e2f-b1e3c9ca800c">
</p>

## Parking lot simulation
The parking lot sensor and its led, the display at the parking entrance and the motor used to raise the bar were all simulated by an Arduino as showed in the figure below:

<p align="center">
  <img width="630" height="360" src="https://github.com/alfredoonori22/ParcheggiAMo/assets/62024453/d3ff2234-583a-4e7b-a45a-1fd5ab5af3fa">
</p>

# Web interface and Cloud Database
The web interface is useful to represent graphically the real-time situation of the different parking scattered throughout the city.
It is intended as an administrator-side tool, that allows the admin to change some variables, like the parkings fare.

The cloud database is an admin-tool too and it is serviceable for:
-  Tracking and analyzing data
-  Optimizing target variable
-  Forecasting future trends
  
<p align="center">
  <img width="350" height="280" src="https://github.com/alfredoonori22/ParcheggiAMo/assets/62024453/7918ee96-073e-4952-a7c4-3e3bc4d327d5">
  <img width="500" height="280" src="https://github.com/alfredoonori22/ParcheggiAMo/assets/62024453/27244d79-550e-4f35-b458-3210d9103725">
</p> 
