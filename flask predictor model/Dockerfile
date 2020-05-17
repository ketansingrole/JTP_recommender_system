FROM python

WORKDIR /prediction/app

COPY requirements.txt .
RUN pip install -r requirements.txt
ENV FLASK_APP=main.py
COPY . .

CMD [ "flask","run", "--host", "0.0.0.0"]