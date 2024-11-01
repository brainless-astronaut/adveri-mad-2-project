from .extensions import db, bcrypt
from datetime import datetime, timedelta

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    username = db.Column(db.String(80), nullable = False, unique = True)
    email = db.Column(db.String(120), nullable = False, unique = True)
    password = db.Column(db.String(), nullable = False)
    role = db.Column(db.String(), nullable = False)
    approved = db.Column(db.Boolean, default = False, nullable = False)
    is_flagged = db.Column(db.Boolean, default = False, nullable = False)
    last_login_at = db.Column(db.DateTime, default = datetime.now)
    __mapper_args__ = {
        'polymorphic_on': role,
        'polymorphic_identity': 'user'
    }

    sent_requests = db.relationship('AdRequests', foreign_keys='AdRequests.sender_id', backref='sender')
    received_requests = db.relationship('AdRequests', foreign_keys='AdRequests.receiver_id', backref='receiver')
    
    def __init__(self, username, email, password, role):
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.email = email
        self.role = role

class Admin(Users):
    __tablename__ = 'admin'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }

class Sponsors(Users):
    __tablename__ = 'sponsors'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    entity_name = db.Column(db.String, nullable = False, unique = True)
    industry = db.Column(db.String, nullable = False)
    budget = db.Column(db.Float, nullable = False)
    __mapper_args__ = {
        'polymorphic_identity': 'sponsor'
    }

class Influencers(Users):
    __tablename__ = 'influencers'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    first_name = db.Column(db.String(25), nullable = False)
    last_name = db.Column(db.String(25), nullable = False)
    dob = db.Column(db.DateTime, nullable = False)
    gender = db.Column(db.String(1), nullable = False)
    niche = db.Column(db.String, nullable = False)
    industry = db.Column(db.String, nullable = False)

    __mapper_args__ = {
        'polymorphic_identity': 'influencer'
    }

    # platforms = db.relationship('InfluencerPlatform', back_populates = 'influencer', cascade = 'all, delete-orphan')
    # ad_requests = db.relationship('AdRequests', back_populates = 'influencer', cascade = 'all, delete-orphan')

class InfluencerPlatform(db.Model):
    __tablename__ = 'inf_platforms'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey('influencers.user_id'), nullable = False)
    platform = db.Column(db.String(), nullable = False)
    reach = db.Column(db.Integer(), nullable = False, default = 0)

    # influencer = db.relationship('Influencer', back_populates = 'platform', uselist = False)

class Campaigns(db.Model):
    __tablename__ = 'campaigns'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.user_id'))
    name = db.Column(db.String(), nullable=False, unique=True)
    description = db.Column(db.String(), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    end_date = db.Column(db.DateTime, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    goals = db.Column(db.Integer, nullable=False)
    visibility = db.Column(db.String, nullable=False, default='public')
    campaign_reach = db.Column(db.Integer, nullable=False, default=0)
    goals_met = db.Column(db.Boolean, default=False)

    ad_requests = db.relationship('AdRequests', back_populates='campaign', cascade='all, delete-orphan')
    joined_influencers = db.relationship('JoinedInfluencers', back_populates='campaign', cascade='all, delete-orphan')

    def __init__(self):
        self.goals_met = self.goals == self.campaign_reach

class AdRequests(db.Model):
    __tablename__ = 'ad_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sent_by = db.Column(db.String, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    message = db.Column(db.String, nullable=False)
    requirements = db.Column(db.String, nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    negotiated_amount = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String, nullable=False)

    campaign = db.relationship('Campaigns', back_populates='ad_requests')
    joined_influencers = db.relationship('JoinedInfluencers', back_populates='ad_request', cascade='all, delete-orphan')

class JoinedInfluencers(db.Model):
    __tablename__ = 'joined_influencers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('influencers.user_id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('ad_requests.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)

    campaign = db.relationship('Campaigns', back_populates='joined_influencers')
    ad_request = db.relationship('AdRequests', back_populates='joined_influencers')
