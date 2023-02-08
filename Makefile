name ?= codecovcli

lint:
	pip install black==22.3.0 isort==5.10.1
	black .
	isort --profile black .