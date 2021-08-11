import jwt

from flask      import request, jsonify, current_app, Response, g, render_template, url_for
from flask.json import JSONEncoder
from functools  import wraps

from werkzeug.utils import redirect

## Default JSON encoder는 set를 JSON으로 변환할 수 없다.
## 그럼으로 커스텀 엔코더를 작성해서 set을 list로 변환하여
## JSON으로 변환 가능하게 해주어야 한다.
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self, obj)

#########################################################
#       Decorators
#########################################################
def login_required(f):      
    @wraps(f)                   
    def decorated_function(*args, **kwargs):
        access_token = request.headers.get('Authorization') 
        if access_token is not None:  
            try:
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256') 
            except jwt.InvalidTokenError:
                 payload = None     

            if payload is None: return Response(status=401)  

            user_id   = payload['user_id']  
            g.user_id = user_id
        else:
            return Response(status = 401)  

        return f(*args, **kwargs)
    return decorated_function

def create_endpoints(app, services):
    app.json_encoder = CustomJSONEncoder

    # add service list
    user_service  = services.user_service
    motion_service = services.motion_service

    @app.route("/ping", methods=['GET'])
    def ping():
        return "pong"
    
    @app.route("/main")
    @login_required
    def main():
        return render_template('main.html')

    @app.route("/sign-up", methods=['POST'])
    def sign_up():
        new_user = request.json
        new_user = user_service.create_new_user(new_user)

        return jsonify(new_user)
        
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method=='GET':
            access_token = request.headers.get('Authorization') 
            if access_token is None:
                return render_template('login.html')
            else:
                return redirect(url_for('main'))
        else:
            credential = request.form
            #print(credential)
            authorized = user_service.login(credential) 

            if authorized:
                user_credential = user_service.get_user_id_and_password(credential['email'])
                user_id         = user_credential['id']
                token           = user_service.generate_access_token(user_id)
                return jsonify({
                    'user_id'      : user_id,
                    'access_token' : token
                })
            else:
                return redirect(url_for('login'))
    
    @app.route('/detected', methods=['POST'])
    @login_required
    def detected():
        dectected = request.json
        
        if motion_service.detected_motion(detected):
            return '움직임이 감지됐습니다.'
        

