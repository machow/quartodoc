FROM ghcr.io/quarto-dev/quarto:1.4.330

RUN apt-get update && apt-get install -y python3 python3-pip git
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools jupyterlab ipython jupyterlab-quarto
COPY ./ /quartodoc
WORKDIR /quartodoc
RUN pip3 install -e ".[dev]"
