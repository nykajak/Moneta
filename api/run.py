from api import app,db
import api.models 


with app.app_context():
    db.create_all()
    app.logger.info("Database initialised!")
        
# app.run()