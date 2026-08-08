FROM python:3.12

WORKDIR /emailPrepAI

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["bash", "-lc", "python manage.py migrate && waitress-serve --port=8000 emailPrepAI.wsgi:application"]


