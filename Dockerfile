FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["nohup", "python", "-u" ,"main.py", "&"]
CMD ["tail", "-f", "nohup.out"]
