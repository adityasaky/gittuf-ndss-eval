FROM alpine:latest

RUN apk update && apk add git openssh go python3 py3-click

WORKDIR /root

ENV PATH="/root/go/bin:$PATH"

RUN go install github.com/gittuf/gittuf@v0.7.0

RUN gittuf version

ADD experiment1.py experiment2.py experiment3.py experiment4.py utils.py /root/

ADD keys /root/keys
