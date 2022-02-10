FROM continuumio/miniconda3

COPY ./environment.yaml .
RUN conda env create -f environment.yaml