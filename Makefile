.PHONY: venv format
venv:
	# Create virtual environment.
	python3.11 -m venv venv
	./venv/bin/pip3 install -q --upgrade pip setuptools wheel
	./venv/bin/pip3 install  -r dev.requirements.txt

format: venv
	# Run checking and formatting sources.
	./venv/bin/bandit -q -r src/
	./venv/bin/pre-commit run -a

clean:
	# Reset all containers and volumes.
	docker compose -f local.compose.yml down --remove-orphans --volumes --timeout 1

build: clean
	# Build image all services.
	docker build -q -t deribit_postgres:dev ./postgres
	docker build -q -t deribit_backend:dev .
	docker compose -f ./local.compose.yml build

run: build
	# Run all containers.
	docker compose -f local.compose.yml up --abort-on-container-exit

test:
	# Run containers with db`s and other common services.
	make -C ../ build
	docker compose -f ../local.compose.yml --profile collector up -d
