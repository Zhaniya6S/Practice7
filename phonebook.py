from connect import connect
import csv

def init_database():
    """Initialize database: create tables, functions, and procedures"""
    conn = connect()
    cur = conn.cursor()
    try:
        print("\n=== Database Initialization ===")
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS phonebook (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(50) NOT NULL
            )
        """)
        print("Phonebook table created/exists")
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_phonebook_name ON phonebook(name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_phonebook_phone ON phonebook(phone)")
        print("Indexes created")
   
        cur.execute("DROP FUNCTION IF EXISTS get_contacts_by_pattern(TEXT)")
        cur.execute("DROP FUNCTION IF EXISTS get_contacts_paginated(INT, INT)")
        print("Old functions removed")
        
        cur.execute("""
            CREATE OR REPLACE FUNCTION get_contacts_by_pattern(p_pattern TEXT)
            RETURNS TABLE(name VARCHAR, phone VARCHAR) AS $$
            BEGIN
                RETURN QUERY 
                SELECT c.name, c.phone 
                FROM phonebook c
                WHERE c.name ILIKE '%' || p_pattern || '%'
                   OR c.phone ILIKE '%' || p_pattern || '%'
                ORDER BY c.id;
            END;
            $$ LANGUAGE plpgsql
        """)
        print("Function get_contacts_by_pattern created")
     
        cur.execute("""
            CREATE OR REPLACE FUNCTION get_contacts_paginated(p_limit INT, p_offset INT)
            RETURNS TABLE(name VARCHAR, phone VARCHAR) AS $$
            BEGIN
                RETURN QUERY 
                SELECT c.name, c.phone 
                FROM phonebook c
                ORDER BY c.id
                LIMIT p_limit OFFSET p_offset;
            END;
            $$ LANGUAGE plpgsql
        """)
        print("Function get_contacts_paginated created")
        
        cur.execute("DROP PROCEDURE IF EXISTS upsert_contact(VARCHAR, VARCHAR)")
        cur.execute("DROP PROCEDURE IF EXISTS delete_contact_proc(VARCHAR)")
        cur.execute("DROP PROCEDURE IF EXISTS bulk_insert_contacts(VARCHAR[], VARCHAR[])")

        cur.execute("""
            CREATE OR REPLACE PROCEDURE upsert_contact(p_name VARCHAR, p_phone VARCHAR)
            LANGUAGE plpgsql AS $$
            BEGIN
                IF EXISTS (SELECT 1 FROM phonebook WHERE name = p_name) THEN
                    UPDATE phonebook SET phone = p_phone WHERE name = p_name;
                ELSE
                    INSERT INTO phonebook(name, phone) VALUES(p_name, p_phone);
                END IF;
            END;
            $$
        """)
        print("Procedure upsert_contact created")

        cur.execute("""
            CREATE OR REPLACE PROCEDURE delete_contact_proc(p_val VARCHAR)
            LANGUAGE plpgsql AS $$
            BEGIN
                DELETE FROM phonebook WHERE name = p_val OR phone = p_val;
            END;
            $$
        """)
        print("Procedure delete_contact_proc created")
        
        cur.execute("""
            CREATE OR REPLACE PROCEDURE bulk_insert_contacts(p_names VARCHAR[], p_phones VARCHAR[])
            LANGUAGE plpgsql AS $$
            DECLARE
                i INT;
                invalid_phones TEXT := '';
            BEGIN
                FOR i IN 1 .. array_length(p_names, 1) LOOP
                    IF p_phones[i] ~ '^[0-9]+$' THEN
                        CALL upsert_contact(p_names[i], p_phones[i]);
                    ELSE
                        invalid_phones := invalid_phones || format('Name: %s, Phone: %s (invalid format)\\n', p_names[i], p_phones[i]);
                    END IF;
                END LOOP;
                
                IF invalid_phones <> '' THEN
                    RAISE NOTICE 'Invalid phone numbers found:\\n%', invalid_phones;
                END IF;
            END;
            $$
        """)
        print("Procedure bulk_insert_contacts created")
        
        conn.commit()
        print("\n=== Database initialization completed successfully ===\n")
        
    except Exception as e:
        print(f"Initialization error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def insert_or_update():
    """Add or update a contact"""
    try:
        name = input("Enter name: ").strip()
        phone = input("Enter phone: ").strip()
        
        if not name or not phone:
            print("Name and phone cannot be empty!")
            return
        
        conn = connect()
        cur = conn.cursor()
        cur.execute("CALL upsert_contact(%s, %s)", (name, phone))
        conn.commit()
        print(f"Contact '{name}' successfully added/updated")
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def insert_from_csv():
    """Add contacts from CSV file"""
    try:
        conn = connect()
        cur = conn.cursor()
        
        import os
        if not os.path.exists('contacts.csv'):
            print("✗ contacts.csv file not found!")
            return
            
        with open('contacts.csv', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            count = 0
            for row in reader:
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    cur.execute("CALL upsert_contact(%s, %s)", (row[0].strip(), row[1].strip()))
                    count += 1
        conn.commit()
        print(f"Processed contacts from CSV: {count}")
        
    except FileNotFoundError:
        print("contacts.csv file not found!")
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def search_by_pattern():
    """Search contacts by pattern"""
    try:
        pattern = input("Enter name or phone part to search: ").strip()
        if not pattern:
            print("Pattern cannot be empty!")
            return
        
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM get_contacts_by_pattern(%s)", (pattern,))
        results = cur.fetchall()
        
        if results:
            print(f"\nFound {len(results)} contact(s):")
            print("-" * 40)
            for i, r in enumerate(results, 1):
                print(f"{i}. Name: {r[0]}, Phone: {r[1]}")
            print("-" * 40)
        else:
            print("No contacts found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def show_paged():
    """Display contacts with pagination"""
    try:
        limit = int(input("Records per page: "))
        offset = int(input("Offset (how many to skip): "))
        
        if limit <= 0 or offset < 0:
            print("Records per page must be positive, offset must be non-negative")
            return
        
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM get_contacts_paginated(%s, %s)", (limit, offset))
        results = cur.fetchall()
        
        if results:
            print(f"\nShowing {len(results)} contact(s):")
            print("-" * 40)
            for i, r in enumerate(results, 1):
                print(f"{i}. Name: {r[0]}, Phone: {r[1]}")
            print("-" * 40)
        else:
            print("No contacts to display")
            
    except ValueError:
        print("Please enter valid numbers!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def delete_contact():
    """Delete contact by name or phone"""
    try:
        val = input("Enter name or phone to delete: ").strip()
        if not val:
            print("Value cannot be empty!")
            return
        
        conn = connect()
        cur = conn.cursor()
        cur.execute("CALL delete_contact_proc(%s)", (val,))
        conn.commit()
        print(f"Contact(s) with '{val}' successfully deleted")
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def bulk_insert():
    """Bulk insert multiple contacts"""
    try:
        print("\n   Bulk Insert Contacts   ")
        print("Enter contacts in format: name,phone")
        print("Enter empty line to finish")
        
        names = []
        phones = []
        
        while True:
            entry = input("Contact (name,phone): ").strip()
            if not entry:
                break
            
            parts = entry.split(',')
            if len(parts) >= 2:
                names.append(parts[0].strip())
                phones.append(parts[1].strip())
            else:
                print("Invalid format. Use: name,phone")
        
        if names:
            conn = connect()
            cur = conn.cursor()
            cur.execute("CALL bulk_insert_contacts(%s, %s)", (names, phones))
            conn.commit()
            print(f"Bulk insert completed for {len(names)} contact(s)")
        else:
            print("No contacts entered")
            
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def menu():
    """Main menu"""
    init_database()
    
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM phonebook")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    if count == 0:
        print("\n=== Add test data ===")
        print("Select option 1 to add contacts")
        print("Or option 2 to load from CSV")
    
    while True:
        print("\n" + "="*50)
        print(" PHONEBOOK (Practice 8)")
        print("="*50)
        print("1 - Add/Update contact")
        print("2 - Add from CSV file")
        print("3 - Show with pagination")
        print("4 - Search by pattern")
        print("5 - Delete contact")
        print("6 - Bulk insert")
        print("0 - Exit")
        print("-"*50)

        choice = input("Choose an option: ")

        if choice == "1":
            insert_or_update()
        elif choice == "2":
            insert_from_csv()
        elif choice == "3":
            show_paged()
        elif choice == "4":
            search_by_pattern()
        elif choice == "5":
            delete_contact()
        elif choice == "6":
            bulk_insert()
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice, please try again")

if __name__ == "__main__":
    menu()