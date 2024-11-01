from .workers import celery
from models import *
from celery.schedules import crontab
from datetime import datetime, timedelta
from .mailer import send_email
from flask import render_template
from sqlalchemy import func

@celery.on_after_finalize.connect
def setup_peridioc_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour = 9, minute = 00), send_daily_email.s(), name = 'Daily Emails')
    sender.add_periodic_task(crontab(day_of_month = 1, hour = 9, minute = 00), send_monthly_email.s(), name = 'Monthly Emails')

@celery.task
def send_daily_email():
    inactive_users = Users.query.filter(Users.last_login_at < (datetime.now() - timedelta(hours =24))).filter(Users.role != 'admin').all()
    message = 'Hey! You are receiving this email since you haven\'t logged into AdVeri for the past 24 hours. Check in to see your progress in your ventures!'
    for user in inactive_users:
        html = render_template('daily_reminder.html', user = user, message = message)
        send_email(user.email, 'Login to Adveri!', html)
    return f'Login reminder sent to {len(inactive_users)} users.'

@celery.task
def send_monthly_email():
    sponsors = Users.query.filter_by(role = 'sponsor').all()
    one_month_ago = datetime.now() - timedelta(days = 30)

    for sponsor in sponsors:
        campaigns = Campaigns.query.filter_by(sponsor_id = sponsor.id).filter_by(Campaigns.start_date < one_month_ago).all()
        campaign_details = []
        total_reach = 0
        expenditure = 0

        for campaign in campaigns:
            expenditure = db.session.query(func.sum(AdRequests.payment_amount)).filter(AdRequests.campaign_id == campaign.id).scalar()

            campaign_details.append({
                'name': campaign.name,
                'description': campaign.description,
                'start_date': campaign.start_date,
                'end_date': campaign.end_date,
                'budget': campaign.budget,
                'visibility': campaign.visibility,
                'goals': campaign.goals,
                'campaign_reach': campaign.campaign_reach,
                'goals_met': campaign.goals_met,
                'expenditure': expenditure

            })

        html = render_template('monthly_report.html', user = sponsor, campaign_details = campaign_details)
        send_email(sponsor.eamil, 'Monthly Report', html)
    return f'Monthly report sent to {len(sponsors)} users.'