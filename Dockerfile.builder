FROM python:3.9-slim

RUN apt-get update && apt-get install -y binutils libc-bin patchelf
RUN pip install staticx PyInstaller

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
COPY *.py /app/

RUN pyinstaller --onefile --workpath /tmp/build --distpath /app /app/wtf-ds.py
RUN staticx /app/wtf-ds /app/wtf-ds-static
