FROM alexandrpr/system-for-bot:v1.1

LABEL author="AlexandrPr" contacts="zakuson2001@inbox.ru"

WORKDIR /home/botmanager/alavdeev_bot

ADD . .

RUN ["python3", "-m", "venv", "venv"]
RUN . ./venv/bin/activate && pip3 install -r requirements.txt

CMD ["pm2-runtime", "start", "ecosystem.config.js"]
