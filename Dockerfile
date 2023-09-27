FROM alexandrpr/alavdeev_bot:v2-nosecure

LABEL author="AlexandrPr" contacts="zakuson2001@inbox.ru"

# ENV BOTCONFIGFILE="settings.ini"
# ENV GOOGLECALENDARFILE="avd-bot-87f99ff81853.json"

WORKDIR /home/botmanager/alavdeev_bot

# ADD /home/botmanager/alavdeev_bot/config/${BOTCONFIGFILE} config/
# ADD /home/botmanager/alavdeev_bot/config/${GOOGLECALENDARFILE} config/

# RUN cd /home/botmanager/alavdeev_bot
EXPOSE 5432
CMD ["pm2-runtime", "start", "ecosystem.config.js"]