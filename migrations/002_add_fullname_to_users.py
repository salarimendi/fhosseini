from yoyo import step

__depends__ = {'001_initial'}

def apply_step(conn):
    cursor = conn.cursor()
    # Add fullname column
    cursor.execute("""
        ALTER TABLE users 
        ADD COLUMN fullname VARCHAR(40) DEFAULT NULL
    """)
    
    # Update existing users using username as fullname
    cursor.execute("""
        UPDATE users 
        SET fullname = username 
        WHERE fullname IS NULL
    """)
    
    # Make fullname field required for new records
    cursor.execute("""
        ALTER TABLE users 
        ALTER COLUMN fullname SET NOT NULL
    """)

def rollback_step(conn):
    cursor = conn.cursor()
    cursor.execute("""
        ALTER TABLE users 
        DROP COLUMN fullname
    """)

step(apply_step, rollback_step)