name ?= codecovcli

lint:
	pip install black==22.3.0 isort==5.10.1
	black codecov_cli/**
	isort --profile black codecov_cli/**
	black tests/**
	isort --profile black tests/**