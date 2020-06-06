
from pythontuio import TuioServer
from pythontuio import Cursor
from pythontuio import Blob
from pythontuio import Object

from pythontuio import TuioClient





def test_cursor():

    client = TuioServer()

    i = 0
    cursor = Cursor(1213)

    cursor.velocity             = (0.2,0.1)
    cursor.motion_acceleration  = 0.1 

    client.cursors.append(cursor)
    while i < 10:


        i+=1
        cursor.position  = (0.5+0.01*i,0.5)

        client.send_bundle()
        print("sented message")
    assert True

def test_blob():

    client = TuioServer()

    i = 0
    blob = Blob(13)

    blob.velocity             = (0.2,0.1)
    blob.motion_acceleration  = 0.1 

    client.blobs.append(blob)
    while i < 10:


        i+=1
        blob.position  = (0.1+0.01*i,0.2)

        client.send_bundle()
        print("sented message")
    assert True

def test_object():
    client = TuioServer()

    i = 0
    ob = Object(13)

    ob.velocity             = (0.2,0.1)
    ob.motion_acceleration  = 0.1 

    client.objects.append(ob)
    while i < 10:


        i+=1
        ob.position  = (0.1+0.01*i,0.2)

        client.send_bundle()
        print("sented message")
    assert True

def test_client_starts():
    client = TuioClient(("localhost",3333))
    client.start()


if __name__ == "__main__":
    test_cursor()
    test_client_starts()