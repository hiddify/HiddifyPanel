FROM python:3.7-alpine
COPY . /app
WORKDIR /app
RUN pip install .
RUN hiddifypanel create-db
RUN hiddifypanel populate-db
RUN hiddifypanel add-user -u admin -p admin
EXPOSE 5000
CMD ["hiddifypanel", "run"]
