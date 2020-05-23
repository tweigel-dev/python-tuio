from src.tuio import TuioClient
from src.tuio import Cursor
from src.tuio import Blob
from src.tuio import Object







def test_cursor():

    client = TuioClient()

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

# def test_blob():

#     client = TuioClient()

#     i = 0
#     blob = Blob(13)

#     blob.velocity             = (0.2,0.1)
#     blob.motion_acceleration  = 0.1 

#     client.blobs.append(blob)
#     while i < 10:


#         i+=1
#         blob.position  = (0.1+0.01*i,0.2)

#         client.send_bundle()
#         print("sented message")
#     assert True

def test_object():
    client = TuioClient()

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