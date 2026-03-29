from connect import connect
import csv

def insert_from_console():
    name = input("Enter name: ")
    phone = input("Enter phone: ")

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO phonebook (name, phone) VALUES (%s, %s)",
        (name, phone)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Contact added")


def insert_from_csv():
    conn = connect()
    cur = conn.cursor()

    with open('contacts.csv', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            cur.execute(
                "INSERT INTO phonebook (name, phone) VALUES (%s, %s)",
                (row[0], row[1])
            )

    conn.commit()
    cur.close()
    conn.close()
    print("CSV data inserted")


def show_all():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM phonebook")
    rows = cur.fetchall()

    for row in rows:
        print(row)

    cur.close()
    conn.close()


def search_by_name():
    name = input("Enter name: ")

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM phonebook WHERE name ILIKE %s",
        ('%' + name + '%',)
    )

    results = cur.fetchall()
    for r in results:
        print(r)

    cur.close()
    conn.close()


def update_contact():
    old_name = input("Who to update: ")
    new_name = input("New name: ")
    new_phone = input("New phone: ")

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "UPDATE phonebook SET name=%s, phone=%s WHERE name=%s",
        (new_name, new_phone, old_name)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Updated")

def delete_contact():
    val = input("Enter name or phone to delete: ")

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM phonebook WHERE name=%s OR phone=%s",
        (val, val)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Deleted")

def menu():
    while True:
        print("\n--- PHONEBOOK ---")
        print("1. Add from console")
        print("2. Add from CSV")
        print("3. Show all")
        print("4. Search by name")
        print("5. Update")
        print("6. Delete")
        print("0. Exit")

        choice = input("Choose: ")

        if choice == "1":
            insert_from_console()
        elif choice == "2":
            insert_from_csv()
        elif choice == "3":
            show_all()
        elif choice == "4":
            search_by_name()
        elif choice == "5":
            update_contact()
        elif choice == "6":
            delete_contact()
        elif choice == "0":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    menu()