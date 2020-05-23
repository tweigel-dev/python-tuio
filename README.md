# TUIO for Python3 

TUIO protokoll implementation  based on OSC protocol. It is implemented with the `python-osc` libary. 
#### TUIO spezification
http://www.tuio.org/?specification

#### API example of C++ 
https://www.tuio.org/?cpp
## Installation

    pip3 install python-tuio

## Usage
### Cursor example
    
    from tuio import TuioClient
    from tuio import Cursor

    i = 0
    cursor = Cursor()

    cursor.velocity             = (0.2,0.1)
    cursor.motion_acceleration  = 0.1 
    cursor.session_id           = 123

    client.cursors.append(cursor)
    while i < 10:
        i+=1
        cursor.position = (0.5+0.01*i,0.5)

        client.send_bundle()
        time.sleep(0.1)