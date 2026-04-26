"""
init_db.py
──────────
Initialize MySQL database with schema and create default admin user.

Run once before starting the Flask app:
    python init_db.py
"""

import sys
import io

# Fix Windows console encoding (cp1252 cannot print Unicode box-drawing/emoji chars)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app, db
from models import User, Country, EmissionData, ModelMetrics, Forecast, Insight, DataUploadLog
from datetime import datetime

def init_database():
    """Create all database tables and default admin user."""
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Carbon Dashboard — Database Initialization               ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    try:
        print("  ⏳ Creating database tables...")
        with app.app_context():
            # Drop all tables (WARNING: This deletes all data!)
            db.drop_all()
            print("  ✅ Dropped existing tables")
            
            # Create all tables
            db.create_all()
            print("  ✅ Created all tables:")
            print("      • users")
            print("      • countries")
            print("      • emission_data")
            print("      • model_metrics")
            print("      • forecasts")
            print("      • insights")
            print("      • upload_logs")
            
            # Create default admin user
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', is_admin=True)
                admin.set_password('admin123')  # CHANGE THIS IN PRODUCTION
                db.session.add(admin)
                db.session.commit()
                print("\n  ✅ Created default admin user:")
                print("      Username: admin")
                print("      Password: admin123")
                print("      ⚠️  IMPORTANT: Change this password in production!")
            else:
                print("\n  ℹ️  Admin user already exists")
            
            print("\n╔════════════════════════════════════════════════════════════╗")
            print("║  ✅ Database initialization complete!                      ║")
            print("╚════════════════════════════════════════════════════════════╝\n")
            print("Next steps:")
            print("  1. Run the Flask app: python app.py")
            print("  2. Visit: http://localhost:5000")
            print("  3. Login with admin / admin123")
            print("  4. Upload CSV data from Admin Panel\n")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  • Make sure MySQL is running")
        print("  • Check database connection settings in config.py")
        print("  • Verify database user has CREATE/DROP permissions")
        print("  • Create database manually: CREATE DATABASE carbon_emissions;")
        sys.exit(1)


if __name__ == '__main__':
    init_database()
