FROM python:3.11

RUN apt-get update && apt-get install -y ffmpeg git

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
ENV COQUI_TOS_AGREED=1

COPY . .

CMD ["python", "main.py"]