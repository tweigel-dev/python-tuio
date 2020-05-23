all:
	echo "specify target"

run :
	python3 src/tuio.py

lint :
	python3 -m pylint ./src/ --msg-template='{msg_id}:{line:3d},{column}: {obj}: {msg}'
	
testpython :
	./TuioDemo &		
	python3 -m pytest 				
		
