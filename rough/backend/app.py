from flask import Flask, jsonify, request
from config import Config
from models import *
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
# from werkzeug.utils import secure_filename
import os, io, csv
import matplotlib.pyplot as plt
from flask_caching import Cache
from tools import workers, tasks, mailer

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)
cache = Cache(app)
mailer.init_app(app)

# Celery configuration
celery = workers.celery
celery.conf.update(
    broker_url = app.config['CELERY_BROKER_URL'],
    result_backend = app.config['CELERY_RESULT_BACKEND'],
)

celery.Task = workers.ContextTask
app.app_context().push()

def create_admin(): 
    existing_admin = Users.query.filter_by(role="admin").first()
    if existing_admin: 
        return jsonify({"message": "Admin already exists"}), 200  
    try: 
        admin = Users(username="admin", email="admin@adveri.com", role="admin", password="1")
        db.session.add(admin)
        db.session.commit()
        return jsonify({"message": "Admin created successfully"}), 201
    except Exception as e: 
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

with app.app_context(): 
    db.create_all()
    create_admin()

CORS(app, supports_credentials=True)
@app.route('/')
def hello(): 
    return "Hello World!"
@app.route('/register', methods=["POST"])
def register(): 
    data = request.json
    username = data.get("username")
    email = data.get("email")
    role = data.get("role")
    password = data.get("password")

    if not username or not email or not role or not password: 
        return jsonify({"error": "All fields are required"}), 400
    
    existing_user = Users.query.filter_by(email=email, username=username).first()

    if existing_user: 
        return jsonify({"error": "Users already exists"}), 400
    
    try: 
        user = Users(username=username, email=email, role=role, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Users created successfully"}), 201

    except Exception as e: 
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=["POST"])
def login(): 
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password: 
        return jsonify({"error": "All fields are required"}), 400
    
    user = Users.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password, password): 
        return jsonify({"error": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity={
        "username": user.username,
        "role": user.role,
        "id": user.id
    })

    user.last_login_at = datetime.now()
    db.session.commit()

    return jsonify({"message": "Login successful", "access_token": access_token}), 200

@app.route('/logout', methods=["POST"])
@jwt_required()
def logout(): 
    response = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(response)
    return response, 200

"""_____________________________ADMIN_ROUTES_____________________________"""

@app.route('/admin/dashboard', methods = ['GET'])
@jwt_required
def admin_1():
    current_user = get_jwt_identity()
    if current_user.role != 'admin':
        return jsonify({"error": "You are not authorized to access this page!"}), 401

    sponsors_count = Users.query.filter_by(role='sponsor', is_flagged=False).count()
    influencers_count = Users.query.filter_by(role='influencers', is_flagged=False).count()
    campaigns_count = Campaigns.query.filter_by(is_flagged=False).count()
    flagged_sponsors_count = Users.query.filter_by(role='sponsor', is_flagged=True).count()
    flagged_influencers_count = Users.query.filter_by(role='influencers', is_flagged=True).count()
    flagged_campaigns_count = Campaigns.query.filter_by(is_flagged=True).count()
    sponsors_by_industry = (
        db.session.query(Sponsors.entity_name, Sponsors.industry)
        .join(Users, Users.id == Sponsors.user_id)
        .filter_by(Users.is_flagged == False)
        .group_by(Sponsors.industry)
        .all()
    )
    influencers_by_industry = (
        db.session.query(Influencers)
        .join(Users, Users.id == Influencers.user_id)
        .filter_by(Users.is_flagged == False)
        .group_by(Influencers.industry)
        .all()
    )
    campaigns_by_industry = (
        db.session.query(Campaigns)
        .join(Sponsors, Campaigns.sponsors_id == Sponsors.user_id)
        .filter_by(Campaigns.is_flagged == False)
        .group_by(Sponsors.industry)
        .all()
    )
    flagged_sponsors = Users.query.filter_by(role='sponsor', is_flagged=True).all()
    flagged_influencers = Users.query.filter_by(role='influencers', is_flagged=True).all()
    flagged_campaigns = Campaigns.query.filter_by(is_flagged=True).all()

    return jsonify({'sponsors_count': sponsors_count, 'influencers_count': influencers_count, 'campaigns_count': campaigns_count,
                    'flagged_sponsors_count': flagged_sponsors_count, 'flagged_influencers_count': flagged_influencers_count, 'flagged_campaigns_count': flagged_campaigns_count,
                    'sponsors_by_industry': sponsors_by_industry, 'influencers_by_industry': influencers_by_industry, 'campaigns_by_industry': campaigns_by_industry,
                    'flagged_sponsors': flagged_sponsors, 'flagged_influencers': flagged_influencers, 'flagged_campaigns': flagged_campaigns
    })

@app.route('/admin/aprove_sponsors/<int:sponsor_id>', methods = ["GET", "PUT", "DELETE"])
@jwt_required()
def admin_2(sponsor_id): 
    current_user = get_jwt_identity()
    if current_user.role != "admin": 
        return jsonify({"error": "You are not authorised to access this page!"}), 401
    
    if request.method == "GET": 
        sponsor_applications = Users.query.filter_by(role = "sponsor", approved = False).all()

        if not sponsor_applications: 
            return jsonify({"error": "No sponsor applications has been found."}), 404

        sponsor = Users.query.get(sponsor_id)

        if not sponsor: 
            return jsonify({"error": "Sponsor not found."}), 404
        
    if request.method == "PUT": 
        try: 
            sponsor.approved = True
            db.session.commit()
            return jsonify({"message": "Sponsor approved successfully!"}), 201
        except  Exception as e: 
            db.session.rollback()
            return jsonify({"error": f"Some error occured in approving the sponsor. str{e}"}), 404

    if request.method =="DELETE": 
        try: 
            db.session.delete(sponsor)
            db.session.commit()
            return jsonify({"message": "Sponsor deleted successfully!"}), 201
        except Exception as e: 
            db.session.rollback()
            return jsonify({"error": "Some error occured in delelting sponsor!"}), 404

@app.route('/admin/manage_users', methods = ["GET", "POST"])
@jwt_required()
def admin_3(): 
    current_user = get_jwt_identity()
    if current_user.role != "admin": 
        return jsonify({"error": "You are not authorised to access this page!"}), 401

    if request.method == "GET": 
        users = Users.query.filter_by(Users.role != "admin").all()
        if not users: 
            return jsonify({"error": "No user found."}), 404
        
        return jsonify([user.to_dict() for user in users]), 200
    
    if request.method == "PUT": 
        data = request.json
        user_id = data.get("user_id")
        action = data.get("action")
        reason = data.get("reason")

        user = Users.query.get(user_id)
        if not user: 
            return jsonify({"error": "User not found."}), 404

        try:
            if action == "flag":
                user.is_flagged = True
                flagged_user = Flagged(item_type = "user", item_id = user.id, reason = reason)
                db.session.add(flagged_user)
            elif action == "unflag":
                user.is_flagged = False
                flagged_user = Flagged.query.filter_by(item_type = "user", item_id = user.id).first()
                if flagged_user:
                    db.session.delete(flagged_user)
            
            db.session.commit()
            return jsonify({"message": f"User {'flagged' if action == 'flag' else 'unflagged'} successfully."}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Some error occured while {'flagging' if action == 'flag' else 'unflagging'} the user. str{e}"}), 404

    if request.method == "DELETE":
        data = request.get_json()
        user_id = data.get("user_id")
        action = data.get("action")  # unflag or delete

        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404

        try: 
            if action == "unflag":
                flagged_user = Flagged.query.filter_by(item_type = "user", item_id=user.id).first()
                if flagged_user:
                    db.session.delete(flagged_user)
                user.is_flagged = False
            elif action == "delete":
                flagged_user = Flagged.query.filter_by(item_type = "user", item_id=user.id).first()
                if flagged_user:
                    db.session.delete(flagged_user)
                db.session.delete(user)

            db.session.commit()
            return jsonify({"message": f"User {'deleted' if action == 'delete' else 'unflagged'} successfully."}), 200
        
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Some error occured while {'flagging' if action == 'flag' else 'unflagging'} the user. str{e}"}), 404

    return jsonify({"error": "Invalid request method."}), 405

@app.route('/admin/manage_campaigns', methods = ["GET", "POST", "PUT", "DELETE"])
@jwt_required
def admin_4():
    current_user = get_jwt_identity()
    if current_user.role != "admin":
        return jsonify({"error": "You are not authorised to access this page!"}), 401 
    
    if request.method == "GET":
        campaigns = Campaigns.query.filter(Campaigns.end_date >= datetime.now()).group_by(Campaigns.sponsor_id).all()

        if not campaigns:
            return jsonify({"error": "No campaign found."}), 404
        
        return jsonify([campaign.to_dict() for campaign in campaigns]), 200

    if request.method == "PUT":
        data = request.json
        campaign_id = data.get("campaign_id")
        action = data.get("action")
        reason = data.get("reason")

        campaign = Campaigns.query.get(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaigns not found."}), 404

        try:
            if action == "flag":
                campaign.is_flagged = True
                flagged_campaign = Flagged(item_type = "campaign", item_id = campaign.id, reason = reason)
                db.session.add(flagged_campaign)
            elif action == "unflag":
                campaign.is_flagged = False
                flagged_campaign = Flagged.query.filter_by(item_type = "campaign", item_id = campaign.id).first()
                if flagged_campaign:
                    db.session.delete(flagged_campaign)
            
            db.session.commit()
            return jsonify({"message": f"User {'flagged' if action == 'flag' else 'unflagged'} successfully."}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Some error occured while {'flagging' if action == 'flag' else 'unflagging'} the campaign. str{e}"}), 404

    if request.method == "DELETE":
        data = request.get_json()
        campaign_id = data.get("campaign_id")
        action = data.get("action")  # unflag or delete

        campaign = Users.query.get(campaign_id)
        if not campaign:
            return jsonify({"error": "User not found."}), 404

        try: 
            if action == "unflag":
                flagged_campaign = Flagged.query.filter_by(item_type = "campaign", item_id=campaign.id).first()
                if flagged_campaign:
                    db.session.delete(flagged_campaign)
                campaign.is_flagged = False
            elif action == "delete":
                flagged_campaign = Flagged.query.filter_by(item_type = "campaign", item_id=campaign.id).first()
                if flagged_campaign:
                    db.session.delete(flagged_campaign)
                db.session.delete(campaign)

            db.session.commit()
            return jsonify({"message": f"Campaigns {'deleted' if action == 'delete' else 'unflagged'} successfully."}), 200
        
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Some error occured while {'flagging' if action == 'flag' else 'unflagging'} the campaign. str{e}"}), 404

    return jsonify({"error": "Invalid request method."}), 405

"""__________________________SPONSOR_ROUTES____________________________"""
@app.route('/sponsor/create_campaign', methods=["POST"])
@jwt_required()
def sponsor_1():
    # Ensure the sponsor is authorized and handle data creation
    current_user = get_jwt_identity()
    if current_user.role != "sponsor":
        return jsonify({"error": "You are not authorized to access this page!"}), 401

    data = request.json
    sponsor_id = current_user["id"]
    name = data.get("name")
    description = data.get("description")
    start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d") if data.get("start_date") else None
    end_date = datetime.strptime(data.get("end_date"), "%Y-%m-%d") if data.get("end_date") else None
    budget = data.get("budget")
    goals = data.get("goals")
    visibility = data.get("visibility")

    existing_campaign_check = Campaigns.query.filter_by(name=name).first()

    if existing_campaign_check:
        return jsonify({"error": f"Campaigns with name {name} already exists."}), 400

    if not all([name, description, start_date, end_date, budget, goals]):
        return jsonify({"error": "All fields are required!"}), 400

    try:
        new_campaign = Campaigns(sponsor_id=sponsor_id, name=name, description=description,
                                 start_date=start_date, end_date=end_date, budget=budget,
                                 goals=goals, visibility=visibility)
        db.session.add(new_campaign)
        db.session.commit()
        return jsonify({"message": "Campaigns created successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Some error occurred while creating the new campaign. {str(e)}"}), 500

    pass

@app.route('/sponsor/campaign_management', methods = ["GET", "PUT", "DELETE"])
@jwt_required
def sponsor_2():
    current_user = get_jwt_identity()
    
    if current_user.role != "sponsor" and current_user.approved == True:
        return jsonify({"error": "You are not authorized to access this page!"}), 403

    if request.method == "GET":
        search_query = request.args.get("search", "")
        sponsor_id = current_user["id"]

        if search_query:
            campaigns = Campaigns.query.filter(
                Campaigns.name.ilike(f"%{search_query}%") |
                Campaigns.description.ilike(f"%{search_query}%")
            ).all()
        else:
            campaigns = Campaigns.query.filter_by(sponsor_id=sponsor_id).all()

        if not campaigns:
            return jsonify({"error": "No campaigns found."}), 404

        campaign_details = []
        today = datetime.today().date()

        for campaign in campaigns:
            days_passed = (today - campaign.start_date).days
            total_days = (campaign.end_date - campaign.start_date).days
            progress = (days_passed / total_days) * 100 if total_days > 0 else 0
            if progress >= 100:
                progress = f"Completed on {campaign.end_date}"

            joined_influencers = db.session.query(Influencers.name).join(
                AdRequests, Influencers.user_id == AdRequests.influencer_id
            ).filter(
                AdRequests.campaign_id == campaign.id,
                AdRequests.status == "Accepted"
            ).all()

            campaign_details.append({
                "campaign": campaign.to_dict(),
                "progress": progress or 0,
                "joined_influencers": [name for name, in joined_influencers] or []
            })

        return jsonify(campaign_details), 200

    if request.method == "PUT":
        data = request.json
        campaign = Campaigns.query.get_or_404('campaign_id')

        if campaign.sponsor_id != current_user["id"]:
            return jsonify({"error": "You are not authorized to update this campaign!"}), 403

        campaign.name = data.get("name", campaign.name)
        campaign.description = data.get("description", campaign.description)
        campaign.start_date = data.get("start_date", campaign.start_date)
        campaign.end_date = data.get("end_date", campaign.end_date)
        campaign.budget = data.get("budget", campaign.budget)
        campaign.goals = data.get("goals", campaign.goals)
        campaign.visibility = data.get("visibility", campaign.goals)

        db.session.commit()
        return jsonify({"message": "Campaigns updated successfully!"}), 200

    if request.method == "DELETE":
        campaign = Campaigns.query.get_or_404('campaign_id')

        if campaign.sponsor_id != current_user["id"]:
            return jsonify({"error": "You are not authorized to delete this campaign!"}), 403

        db.session.delete(campaign)
        db.session.commit()
        return jsonify({"message": "Campaigns deleted successfully!"}), 200

@app.route('/sponsor/send_request', methods=['GET', 'POST'])
@jwt_required() 
def sponsor_3():
    sponsor_id = get_jwt_identity()
    sponsor = Sponsors.query.filter_by(user_id=sponsor_id).first()
    if not sponsor:
        return jsonify({"error": "Sponsor not found."}), 404

    if request.method == 'POST':
        data = request.get_json()
        campaign_id = data.get('campaign_id')
        influencer_ids = data.get('influencer_ids')
        
        if not campaign_id or not influencer_ids:
            return jsonify({"error": "Please select a campaign and at least one influencer."}), 400

        errors = []
        for influencer_id in influencer_ids:
            influencer = Influencers.query.get(influencer_id)
            messages = data.get(f'messages_{influencer_id}', '').strip()
            requirements = data.get(f'requirements_{influencer_id}', '').strip()
            payment_amount = data.get(f'payment_amount_{influencer_id}', '').strip()
            
            if not influencer:
                errors.append(f'Influencers with ID {influencer_id} not found.')
                continue
            
            if not all([messages, requirements, payment_amount]):
                errors.append(f'All fields are required for influencer {influencer.name}.')
                continue

            # Check if the influencer is already added to the campaign
            existing_request = AdRequests.query.filter_by(campaign_id=campaign_id, influencer_id=influencer_id).first()
            if existing_request:
                errors.append(f'Influencers {influencer.name} is already added to this campaign.')
                continue

            ad_request = AdRequests(
                sender_id=sponsor_id,
                campaign_id=campaign_id,
                receiver_id=influencer.user_id,
                messages=messages,
                requirements=requirements,
                payment_amount=payment_amount,
                status='Pending'
            )
            db.session.add(ad_request)

        if errors:
            return jsonify({"errors": errors}), 400
        
        db.session.commit()
        return jsonify({"success": "Requests sent successfully!"}), 200

    ## For GET request: return campaign details and influencers
    campaigns = Campaigns.query.filter_by(sponsor_id=sponsor.user_id).all()
    if not campaigns:
        return jsonify({"error": "No campaigns found."}), 404

    influencers = Influencers.query.filter(Influencers.category == sponsor.industry).all()

    # Prepare campaign details
    campaign_details = []
    today = datetime.today().date()
    for campaign in campaigns:
        days_passed = (today - campaign.start_date).days
        total_days = (campaign.end_date - campaign.start_date).days
        progress = (days_passed / total_days) * 100 if total_days > 0 else 0
        if progress >= 100:
            progress = f'Completed on {campaign.end_date}'

        joined_influencers = db.session.query(Influencers.name).join(
            AdRequests, Influencers.user_id == AdRequests.influencer_id
        ).filter(
            AdRequests.campaign_id == campaign.id,
            AdRequests.status == 'Accepted'
        ).all()

        campaign_details.append({
            'id': campaign.id,
            'name': campaign.name,
            'description': campaign.description,
            'progress': progress,
            'joined_influencers': [name for name, in joined_influencers] or []
        })

    return jsonify({
        "campaigns": campaign_details,
        "influencers": [{"id": inf.id, "name": inf.name, "category": inf.category} for inf in influencers]
    }), 200

@app.route('/sponsor/request_management', methods = ['GET', 'PUT', 'DELETE'])
@jwt_required
def sponsor_4():
    pass

if __name__ == "__main__": 
    app.run(debug=True)