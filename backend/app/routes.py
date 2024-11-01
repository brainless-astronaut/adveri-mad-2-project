from flask import request, jsonify, make_response, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from .models import *
from datetime import date, datetime
import matplotlib.pyplot as plt

@app.route('/')
def home():
    return jsonify({"message": "Welcome to AdVeri!"}), 200
    
@app.route('/register', methods = ['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not all([username, email, password, role]):
        return jsonify({"message": "All fields are required!"}), 400
    
    user = Users.query.filter_by(username == username, email == email).first()

    if user:
        return jsonify({"error": "User with already exists!"}), 409
    
    try:
        if role == "sponsor":
            try:
                new_user = Users(username = username, email = email, password = password, role = role, approved = False)
                db.session.add(new_user)
                db.session.commit()

                entity_name = data.get('entity_name')
                industry = data.get('industry')
                budget = data.get('budget')
                new_sponsor = Sponsors(user_id = new_user.user_id, entity_name = entity_name, industry = industry, budget = budget)
                db.session.add(new_sponsor)
                db.session.commit()
                return jsonify({"message": "New sponsor added successfully!"}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": f"Some error occured while registering the sponsor. {str(e)}"}), 500

        if role == "influencer":
            try:
                new_user = Users(username = username, email = email, password = password, role = role)
                db.session.add(new_user)
                db.session.commit()

                first_name = data.get('first_name')
                last_name = data.get('last_name')
                dob = data.get('dob')
                gender = data.get('gender')
                niche = data.get('niche')
                industry = data.get('industry')
                new_influencer = Influencers(user_id = new_user.user_id, first_name = first_name, last_name = last_name, 
                                             dob = dob, gender = gender, industry = industry, niche = niche)
                db.session.add(new_influencer)
                db.session.commit()
                return jsonify({"message": "New influencer added successfully!"}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": f"Some error occured while registering the influencer. {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Some error occured: {str(e)}"}), 500

@app.route('/login', methods = ['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = Users.query.filter_by(username = username).first()
    if not user:
        return jsonify({"error": "User not found, try registering as a new user!"}), 404
    
    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Incorrect password!"}), 401
    
    if user.role == 'sponsor' and user.approved == False:\
        return jsonify({"error": "Sponsor application is not yet approved."}), 401
    
    access_token = create_access_token(identity = {
        'id': user.id,
        'role': user.role,
        'verified': user.verified
    })

    user.last_login_at = datetime.now()

    return jsonify({"message": "Login successful!", "access_token": access_token}), 200

@app.route('/logout', methods = ['POST'])
def logout():
    response = jsonify({'message': 'Logout successful!'})
    unset_jwt_cookies(response)
    return response, 200

'''------------------------ADMIN-ROUTES------------------------'''

@app.route('/admin/sponsor_applications', methods = ['GET'])
@jwt_required
def view_sponsor_applications():
    current_user = get_jwt_identity()
    if not current_user.role == 'admin':
        return jsonify({"error": "You are not authorized to access this page!"}), 401
    
    sponsor_appltns = Sponsors.query.join(Users).filter(Users.id == Sponsors.user_id, Users.approved == False).all()

    sponsor_applications = [
        {
            'id': sponsor.id,
            'username': sponsor.username,
            'email': sponsor.email,
            'entity_name': sponsor.entity_name,
            'industry': sponsor.industry,
            'budget': sponsor.budget
        }
        for sponsor in sponsor_appltns
    ]
    return jsonify({'sponsor_applications': sponsor_applications}), 200

@app.route('/admin/approve_sponsor/<int:sponsor_id>', methods = ['PUT', 'DELETE'])
@jwt_required()
def approve_sponsor(sponsor_id):
    current_user = get_jwt_identity()
    if current_user.role == 'admin':
        return jsonify({'error': 'You are not authorised to access the page.'}), 401
    
    try:
        sponsor = Users.query.get(sponsor_id)

        if not sponsor:
            return jsonify({'error': 'Sponsor not found.'}), 404
    
        if request.method == 'PUT':
            sponsor.approved = True
            message = 'Sponsor approved.'
        
        if request.method =='DELETE':
            db.session.delete(sponsor)
            message = 'Sponsor deleted.'
        
        db.session.commit()
        return jsonify({'message': message}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Some error occured. {str(e)}'}), 400
    
'''------------------------SPONSOR-ROUTES------------------------'''

@app.route('/sponsor/create_campaign', methods = ['POST'])
@jwt_required()
def create_campaign():
    current_user = get_jwt_identity()
    if current_user.role == 'sponsor':
        return jsonify({'error': 'You are not authorised to access the page.'}), 401

    data = request.json
    name = data.get('name')
    description = data.get('description')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    budget = data.get('budget')
    goals = data.get('goals')
    visibility = data.get('visibility')

    existing_campaign = Campaigns.query.filter_by(name = name).first()
    if existing_campaign:
        return jsonify({'error': f'Campaign with the name \'{name}\' already exists.'}), 409
    
    if not all([name, description, start_date, end_date, budget, goals, visibility]):
        return jsonify({'error': 'All fields are required!'}), 400

    try:
        new_campaign = Campaigns(name = name, description = description, start_date = start_date,
                                    end_date = end_date, budget = budget, goals = goals,
                                    visibility = visibility)
        db.session.add(new_campaign)
        db.session.commit()
        return jsonify({'message': 'Campaign created successfully!'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Some error occured. {str(e)}'}), 400

@app.route('/sponsor/edit_campaign/<int:campaign_id>', methods = ['GET', 'PUT', 'DELETE'])
@jwt_required
def edit_campaign(campaign_id):
    current_user = get_jwt_identity()
    if not current_user.role == 'sponsor':
         return jsonify({'error': 'You are not authorized to access the page!'}), 401
    
    if request.method == 'GET':
        campaigns = Campaigns.query.filter_by(sponsor_id = current_user.id).all()

        if not campaigns: 
            return jsonify({'error': 'Campaign not found.'})

        
        return jsonify({'campaigns': [campaign.to_dict() for campaign in campaigns]}), 200

    if request.method == 'PUT':
        campaign = Campaigns.query.get(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        try:
            data = request.json
            campaign.description = data.get('description', campaign.description)
            campaign.start_date = data.get('start_date', campaign.start_date)
            campaign.end_date = data.get('end_date', campaign.end_date)
            campaign.budget = data.get('budget', campaign.budget)
            campaign.goals = data.get('goals', campaign.goals)
            campaign.visibility = data.get('visibility', campaign.visibility)

            db.session.commit()
            return jsonify({'message': 'Campaign updated successfully!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Some error occured. {str(e)}'}), 400
    
    if request.method == 'DELETE':
        try:
            campaign = Campaigns.query.get(campaign_id)
            if not campaign:
                return jsonify({"error": "Campaign not found"}), 404
            db.session.delete(campaign)
            db.session.commit()
            return jsonify({"message": "Campaign deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Some error occured. {str(e)}'}), 400

'''------------------------INFLUENCER-ROUTES-------------------'''

'''---------------------COMMON-ROUTES--------------------------'''
@app.route('/<int:campaign_id>/send_request', methods = ['POST'])
@jwt_required
def spn_send_request(campaign_id):
    current_user = get_jwt_identity()
    if not current_user.role == 'sponsor':
        return jsonify({'error': 'You are not authorised to access this page!'}), 401
    
    data = request.json
    receiver_id = data.get('receiver_id')
    sender_id = current_user.id
    sent_by = current_user.role
    message = data.get('message')
    requirements = data.get('requirements')
    payment_amount = data.get('payment_amount')

    if not all([receiver_id, sender_id, sent_by, message, requirements, payment_amount]):
        return jsonify({'error': 'All fields are required.'}), 401
    
    exisiting_request = AdRequests.query.filter_by(campaign_id = campaign_id, receiver_id = receiver_id).first()

    if exisiting_request:
        return jsonify({'message': f'Request already exists between this campaign and receiver'}), 409
    
    new_request = AdRequests(campaign_id = campaign_id, sender_id = sender_id, receiver_id = receiver_id, sender_id = sender_id,
                             sent_by = sent_by, message = message, requirements = requirements, payment_amount = payment_amount)
    db.session.add(new_request)
    db.session.commit()
    return jsonify({'message': 'Request sent successfully!'}), 200

@app.route('/edit_request/<int:request_id>', methods = ['GET', 'PUT', 'DELETE'])
@jwt_required
def spn_edit_request(request_id):
    current_user = get_jwt_identity()
    if not current_user.role == 'sponsor':
        return jsonify({'error': 'You are nto authorized to access this page!'}), 403
    
    try: 
        if request.method == 'GET':
            sent_requests = AdRequests.query.filter_by(sender_id = current_user.id).all()
            received_requests = AdRequests.query.filter_by(receiver_id = current_user.id).all()

            message = ''

            if not sent_requests:
                message = make_response(jsonify({'message': 'You haven\'t received any requests.'}), 200)
            if not received_requests:
                message = make_response(jsonify({'message': 'You haven\'t sent any requests.'}), 200)
            if not all([sent_requests, received_requests]):
                message = make_response(jsonify({'error': 'No request found.'}), 409)

            message = make_response(jsonify({'sent_requests': sent_requests, 'received_requests': received_requests}), 200)

            return message
        
        if request.method == 'PUT':
            ad_request = AdRequests.query.get(request_id)
            if not ad_request:
                return jsonify({'error': 'Request not found.'}), 404

            data = request.json
            ad_request.message = data.get('message', ad_request.message)
            ad_request.requirement = data.get('requirement', ad_request.requirement)
            ad_request.payment_amount = data.get('payment_amount', ad_request.payment_amount)
            ad_request.status = data.get('status', ad_request.status)

            if ad_request.status == 'accept':
                if ad_request.sent_by == 'sponsor':
                    influencer = Users.query.join(Influencers).filter_by(Users.id == Influencers.user_id, Users.id == ad_request.receiver_id).first()
                    influencer.earnings += ad_request.negotiated_amount if ad_request.negotiated_amount else ad_request.payment_amount

                if ad_request.sent_by == 'influencer':
                    influencer = Users.query.join(Influencers).filter_by(Users.id == Influencers.user_id, Users.id == ad_request.sender_id).first()
                    influencer.earnings += ad_request.negotiated_amount if ad_request.negotiated_amount else ad_request.payment_amount
        
            db.session.commit()
            return jsonify({'message': 'Request updated successfullly!'}), 200
        
        if request.method == 'DELETE':
            ad_request = AdRequests.query.get(request_id)
            if not ad_request:
                return jsonify({'error': 'Request not found.'}), 404
            
            db.session.delete(ad_request)
            db.session.commit()
            return jsonify({'message': 'Request delelted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Some error occured. {str(e)}'}), 400

@app.route('/negotiate_payment_amount/<int:request_id>', methods = ['PUT'])
@jwt_required
def negotiate_payment_amount(request_id):
    current_user = get_jwt_identity()
    if not current_user.role in ['sponsor', 'influencer'] or not current_user.approved:
        return jsonify({'error': 'You are not authorized to access this page!'}), 401
    
    try:
        ad_request = AdRequests.query.get(request_id)

        if not ad_request:
            return jsonify({'error': 'Request not found.'}), 404
            
        data = request.json
        ad_request.negotiated_amount = data.get('negotiated_amount', ad_request.negotiated_amount)
        ad_request.status = 'negotiation' if  ad_request.negotiated_amount else ad_request.status

        db.session.commit()
        return jsonify({'message': 'Request status updated successfully!'}), 200        


    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Some error occured {str(e)}'})

