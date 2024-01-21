from moneta import app,db
import moneta.models 

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()