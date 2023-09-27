FROM alexandrpr/alavdeev_bot:v2-nosecure

# ENV BOTCONFIGFILE="settings.ini"
# ENV GOOGLECALENDARFILE="avd-bot-87f99ff81853.json"

WORKDIR /home/botmanager/alavdeev_bot

# ADD /home/botmanager/alavdeev_bot/config/${BOTCONFIGFILE} config/
# ADD /home/botmanager/alavdeev_bot/config/${GOOGLECALENDARFILE} config/

# RUN cd /home/botmanager/alavdeev_bot
EXPOSE 5432
CMD ["pm2", "start", "ecosystem.config.js"]