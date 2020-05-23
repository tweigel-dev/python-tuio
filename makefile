all:
	echo "specify target"

run :
	python3 src/tuio.py

lint :
	python3 -m pylint ./src/ --msg-template='{msg_id}:{line:3d},{column}: {obj}: {msg}'


upload_pip:
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/*