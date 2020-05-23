import 

client = TuioClient()

i = 0
cursor = Cursor()

cursor.velocity             = (0.2,0.1)
cursor.motion_acceleration  = 0.1 
cursor.session_id    = 123

client.cursors.append(cursor)
while i < 10:


    i+=1
    cursor.position  = (0.5+0.01*i,0.5)

    client.send_bundle()
    print("sented message")
    time.sleep(0.1)