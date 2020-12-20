FROM python:3.7
WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .
ENV PYTHONUNBUFFERED 1
CMD ["python", "./n.py"]
