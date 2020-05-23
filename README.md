# TUIO for Python3 

TUIO protokoll implementation  based on OSC protocol. It is implemented with the `python-osc` libary. 

#### TUIO spezification
http://www.tuio.org/?specification

#### OSC spezification
http://opensoundcontrol.org/spec-1_0 
and 
https://python-osc.readthedocs.io/en/latest/

#### API example of C++ 
https://www.tuio.org/?cpp
## Installation

    pip3 install python-tuio

## Usage
### Cursor example
    
    from pythontuio import TuioClient
    from pythontuio import Cursor


    cursor = Cursor(123) # sets session_id to 123

    cursor.velocity             = (0.2,0.1)
    cursor.motion_acceleration  = 0.1 

    client.cursors.append(cursor)
    i = 0
    while i < 10:
        i+=1
        cursor.position = (0.5+0.01*i,0.5)

        client.send_bundle()
        time.sleep(0.1)