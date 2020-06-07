all:
	echo "specify target"

run :
	python3 -m pythontuio.tuio

lint :
	python3 -m pylint ./pythontuio/ --msg-template='{msg_id}:{line:3d},{column}: {obj}: {msg}'
	
testpython :
	./TuioDemo &		
	python3 -m pytest 				
		
install_req :
	pip3 install -r pip_requirements.txt
	pip3 install -r pip_test_requirements.txt

upload_pip:
	rm -f -r ./dist
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/*
	
