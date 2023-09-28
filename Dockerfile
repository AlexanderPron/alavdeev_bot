FROM alexandrpr/alavdeev_bot:v2-nosecure

LABEL author="AlexandrPr" contacts="zakuson2001@inbox.ru"

WORKDIR /home/botmanager/alavdeev_bot

EXPOSE 5432

CMD ["pm2-runtime", "start", "ecosystem.config.js"]