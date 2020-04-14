FROM python:3.8
RUN pip install pipenv
RUN mkdir /app
WORKDIR /app
ENV PYTHONPATH /app
ADD Pipfile /app
ADD Pipfile.lock /app
RUN pipenv install
ADD . /app
CMD ["pipenv", "run", "python", "bot"]
