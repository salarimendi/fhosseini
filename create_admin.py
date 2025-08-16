#!/usr/bin/env python3
"""
Script to create admin user for Ferdowsi Hosseini website
Usage: python create_admin.py
"""

import sys
import getpass
from app import create_app, db
from app.models import User

def create_admin():
    """Create admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(role='admin').first()
        if admin:
            print(f"Admin user already exists: {admin.username}")
            response = input("Do you want to create another admin? (y/N): ")
            if response.lower() != 'y':
                return
        
        print("Creating admin user for Ferdowsi Hosseini website")
        print("-" * 50)
        
        # Get admin details
        while True:
            username = input("Enter admin username: ").strip()
            if not username:
                print("Username cannot be empty!")
                continue
            
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"Username '{username}' already exists!")
                continue
            break
        
        while True:
            email = input("Enter admin email: ").strip()
            if not email or '@' not in email:
                print("Please enter a valid email address!")
                continue
            
            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"Email '{email}' already exists!")
                continue
            break
        
        while True:
            password = getpass.getpass("Enter admin password: ")
            if len(password) < 6:
                print("Password must be at least 6 characters long!")
                continue
            
            password_confirm = getpass.getpass("Confirm admin password: ")
            if password != password_confirm:
                print("Passwords do not match!")
                continue
            break
        
        # Create admin user
        try:
            admin_user = User(
                username=username,
                email=email,
                role='admin',
                is_active=True  # اضافه کردن فیلد is_active
            )
            admin_user.set_password(password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"\n✅ Admin user '{username}' created successfully!")
            print(f"Email: {email}")
            print(f"Role: admin")
            print(f"Status: Active")
            print("\nYou can now login to the website using these credentials.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error creating admin user: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    create_admin()