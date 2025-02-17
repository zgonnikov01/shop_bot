FROM python:3.11

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /shop_bot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./ ./

#RUN chmod -R 777 ./

CMD ["python", "-u", "bot.py"]