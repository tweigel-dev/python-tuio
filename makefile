all:
	echo "specify target"

run :
	python3 pythontuio/tuio.py

lint :
	python3 -m pylint ./pythontuio/ --msg-template='{msg_id}:{line:3d},{column}: {obj}: {msg}'
	
testpython :
	./TuioDemo &		
	python3 -m pytest 				
		


upload_pip:
	rm -f -r ./dist
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/*
	
