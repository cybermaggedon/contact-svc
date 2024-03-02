
VERSION=0.0.0

CONTAINER=contact-svc

all: container

container:
	docker build -f Containerfile \
	    -t ${CONTAINER}:${VERSION} .

