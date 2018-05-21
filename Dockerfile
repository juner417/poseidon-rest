 FROM python:2.7
 ENV PYTHONUNBUFFERED 1
 ADD requirements.txt /
 RUN apt-get update
 RUN apt-get install -y apt-utils
 RUN apt-get install -y vim
 RUN pip install -r requirements.txt
 RUN mkdir /poseidon
 RUN mkdir /tmp/pose
 ADD ./tmp/pose/* /tmp/pose/
 ADD ./poseidon/utils/remote.py /tmp/pose/
 ADD ./poseidon /poseidon
 RUN mkdir /poseidon/logs
 RUN touch /poseidon/logs/logfile
 RUN python /poseidon/manage.py migrate
 WORKDIR /poseidon
 EXPOSE 8000
 CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
