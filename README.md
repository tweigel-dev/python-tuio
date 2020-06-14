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
### Server example with Cursor
``` python
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

```
### Client example with class and extends
```python
    from pythontuio import TuioServer
    from pythontuio import Cursor
    from pythontuio import TuioListener
    from threading import Thread

    class MyListener(TuioListener):
        def add_tuio_cursor(self, cursor: Cursor):
            print("detect a new Cursor")
        (...)


    client = TuioClient(("localhost",3333))
    t = Thread(target=client.start)
    listener = MyListener()
    client.add_listener(listener)

    t.start()
```
### Client example with lamda
``` python
    from pythontuio import TuioServer
    from pythontuio import Cursor
    from pythontuio import TuioListener
    from threading import Thread

    def _add_tuio_cursor(self, cursor: Cursor):
        print("detect a new Cursor")
    (...)


    client = TuioClient(("localhost",3333))
    t = Thread(target=client.start)
    listener = TuioListener()
    listener.add_tuio_cursor = _add_tuio_cursor
    client.add_listener(listener)

    t.start()
```
## Contribution
Feel free to contribute inputs. Just start a MR with your changes.

[GitHub]( https://github.com/tweigel-dev/python-tuio)
