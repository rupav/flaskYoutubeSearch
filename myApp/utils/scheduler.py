from apscheduler.schedulers.background import BackgroundScheduler

def schedule(method):
  # init BackgroundScheduler job
  scheduler = BackgroundScheduler()
  scheduler.add_job(method, trigger='interval', seconds=20)
  scheduler.start()
