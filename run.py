from moneta import app,db
import moneta.models 


with app.app_context():
    db.create_all()
    app.logger.info("Database initialised!")
        
# app.run()