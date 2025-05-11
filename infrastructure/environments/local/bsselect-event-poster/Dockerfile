FROM python:3

# WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# COPY event_posting.py .

CMD [ "python", "./infrastructure/environments/local/bsselect-event-poster/event_poster.py" ]
