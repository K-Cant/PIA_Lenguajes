FROM python:3.12
ADD . /PIA_LENGUAJES
WORKDIR /PIA_LENGUAJES
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . . 
EXPOSE 5000
CMD [ "python","app.py" ]