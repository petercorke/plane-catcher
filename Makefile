planes:
	pyinstaller planes.py
	scp -r dist pipimac:
