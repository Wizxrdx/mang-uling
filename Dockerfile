FROM python:3.12.5

WORKDIR /home/
COPY  ./app app/
COPY  ./forecasting forecasting/
COPY  requirements.txt run.py populate_data.py ./

RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8001

CMD ["python", "run.py"]