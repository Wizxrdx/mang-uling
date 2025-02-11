FROM python:3.12.5

WORKDIR /home/
COPY  ./app src/
COPY  requirements.txt run.py ./

RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8001

CMD ["python", "run.py"]