FROM python:latest

LABEL authors="paleblank"

ENTRYPOINT ["top", "-b"]

ADD . /Dorm6HelperBot_app

WORKDIR /Dorm6HelperBot_app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python manage.py runserver & python bot/main.py"]