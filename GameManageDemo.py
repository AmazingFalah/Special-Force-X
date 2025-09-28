import mysql.connector
import bcrypt

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="SFX"
    )

def register_user(conn):
    cursor = conn.cursor()
    print("\n=== Registration ===")
    full_name = input("Enter Full Name: ")
    username = input("Enter Username: ")
    email = input("Enter Email: ")
    password = input("Enter Password: ")
    dob = input("Enter Date of Birth (YYYY-MM-DD): ")

    # Hash the password with bcrypt
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # bytes
    hashed_str = hashed.decode('utf-8')  # store as text in VARCHAR

    try:
        cursor.execute("""
            INSERT INTO Register (Full_Name, Username, Email, Password, Date_Of_Birth)
            VALUES (%s, %s, %s, %s, %s)
        """, (full_name, username, email, hashed_str, dob))
        conn.commit()
        print("Registration successful!")
    except mysql.connector.Error as e:
        print(f"Registration failed: {e}")

def login_user(conn):
    cursor = conn.cursor()
    print("\n=== Login ===")
    username = input("Enter Username: ")
    if username.lower() in ["admin", "administrator"]:
        print("What do you think you're doing :3")
        return
    password = input("Enter Password: ")

    cursor.execute("SELECT Reg_id, Full_Name, Password FROM Register WHERE Username=%s", (username,))
    user = cursor.fetchone()

    if user:
        reg_id, full_name, stored_hash = user[0], user[1], user[2]
        # stored_hash is text: convert to bytes for bcrypt
        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                print(f"Login successful! Welcome, {full_name}")
                after_login_menu(conn, reg_id)
            else:
                print("Incorrect username or password.")
        except ValueError:
            # In case stored_hash is not a valid bcrypt hash
            print("Login failed due to invalid stored password format. Please reset your password.")
    else:
        print("Incorrect username or password.")

def create_server(conn):
    cursor = conn.cursor()
    print("\n=== Create New Server ===")
    svr_name = input("Server Name: ")
    svr_code = input("Server Code: ")

    # mode options
    modes = ["1v1", "2v2", "FFA", "Deathmatch"]
    print("\nChoose Server Mode:")
    for i, mode in enumerate(modes, 1):
        print(f"{i}. {mode}")

    while True:
        try:
            choice = int(input("Choose option (1-4): "))
            if 1 <= choice <= len(modes):
                svr_mode = modes[choice - 1]
                break
            else:
                print("Please choose a number between 1-4.")
        except ValueError:
            print("Input must be a number.")

    print("\nDescription is optional.")
    svr_desc = input("Server Description (press Enter to skip): ")
    if svr_desc.strip() == "":
        svr_desc = None

    try:
        cursor.execute("""
            INSERT INTO Server (SVR_Name, SVR_Code, SVR_Mode, SVR_Description)
            VALUES (%s, %s, %s, %s)
        """, (svr_name, svr_code, svr_mode, svr_desc))
        conn.commit()
        print("Server created successfully.\n")
        play = input("Do you want to start the game? (y/n): ")
        if play == "y":
            print("The game starting, and you won the game because you are the server owner :D")
        else:
            return
    except mysql.connector.Error as err:
        print(f"Failed to create server: {err}")

def join_server(conn):
    cursor = conn.cursor()
    svr_name = input("Enter Server Name: ").strip()
    svr_code = input("Enter Server Code: ").strip()

    cursor.execute("""
        SELECT 1 FROM Server 
        WHERE SVR_Name = %s AND SVR_Code = %s
    """, (svr_name, svr_code))
    server = cursor.fetchone()

    if server:
        print(f"Successfully joined server '{svr_name}'.")
        play = input("Do you want to start the game? (y/n): ")
        if play == "y":
            print("The game starting, and you lost the game because you are not the server owner ;-;")
        else:
            return
    else:
        print("Server not found or code is incorrect.")

def inventory_menu(conn, reg_id):
    cursor = conn.cursor()
    cursor.execute("SELECT Inv_id, Inv_Name FROM Inventory")
    items = cursor.fetchall()

    print("\n=== Inventory ===")
    for idx, (inv_id, inv_name) in enumerate(items, start=1):
        print(f"{idx}. {inv_name}")

    choice = input("\nDo you want to change weapon? Choose 1-3, or 0 to cancel: ").strip()

    if not choice.isdigit():
        print("Invalid input, only numbers are allowed.")
        return

    choice = int(choice)

    if choice == 0:
        print("Cancelled weapon change.")
        return

    if 1 <= choice <= len(items):
        selected_item = items[choice - 1]
        inv_id = selected_item[0]
        inv_name = selected_item[1]

        cursor.execute("SELECT * FROM Equipment WHERE Reg_id = %s", (reg_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("UPDATE Equipment SET Inv_id = %s WHERE Reg_id = %s", (inv_id, reg_id))
            print(f"Weapon changed to {inv_name}")
        else:
            cursor.execute("INSERT INTO Equipment (Reg_id, Inv_id) VALUES (%s, %s)", (reg_id, inv_id))
            print(f"Weapon selected: {inv_name}")

        conn.commit()
    else:
        print("Invalid option.")

def account_menu(conn, reg_id):
    cursor = conn.cursor()
    cursor.execute("SELECT Username, Email FROM Register WHERE Reg_id = %s", (reg_id,))
    account = cursor.fetchone()

    if not account:
        print("Account not found.")
        return

    username, email = account
    print("\n=== Account Menu ===")
    print(f"Username : {username}")
    print(f"Email    : {email}")

    print("\nOptions:")
    print("1. Update Username")
    print("2. Delete Account")
    print("3. Advanced Settings")
    print("0. Back")

    choice = input("Choose option: ").strip()

    if choice == "1":
        new_username = input("Enter new username: ").strip()
        try:
            cursor.execute("UPDATE Register SET Username = %s WHERE Reg_id = %s", (new_username, reg_id))
            conn.commit()
            print(f"Username updated to {new_username}")
        except Exception as e:
            print(f"Failed to update username: {e}")

    elif choice == "2":
        confirm = input("Are you sure you want to delete this account? (y/n): ").lower()
        if confirm == "y":
            try:
                cursor.execute("DELETE FROM Register WHERE Reg_id = %s", (reg_id,))
                conn.commit()
                print("Account deleted successfully.")
                return "deleted"
            except Exception as e:
                print(f"Failed to delete account: {e}")
        else:
            print("Account deletion cancelled.")
    elif choice == "3":
        advanced_settings(conn, reg_id)
    elif choice == "0":
        print("Back to previous menu.")
    else:
        print("Invalid choice.")

def advanced_settings(conn, reg_id):
    cursor = conn.cursor()

    while True:
        print("\n=== Advanced Settings ===")
        print("1. Change Password")
        print("2. Change Email")
        print("0. Back")

        choice = input("Choose option: ").strip()

        if choice == "1":
            new_password = input("Enter new password: ").strip()
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            try:
                cursor.execute("UPDATE Register SET Password = %s WHERE Reg_id = %s", (hashed, reg_id))
                conn.commit()
                print("Password successfully updated.")
            except Exception as e:
                print(f"Failed to update password: {e}")

        elif choice == "2":
            new_email = input("Enter new email: ").strip()
            try:
                cursor.execute("UPDATE Register SET Email = %s WHERE Reg_id = %s", (new_email, reg_id))
                conn.commit()
                print("Email successfully updated.")
            except Exception as e:
                print(f"Failed to update email: {e}")

        elif choice == "0":
            print("Back to Menu.")
            break
        else:
            print("Invalid choice.")

def after_login_menu(conn, reg_id):
    while True:
        print("\n=== After Login Menu ===")
        print("1. Create Server")
        print("2. Join Server")
        print("3. Inventory")
        print("4. Account")
        print("5. Logout")
        choice = input("Choose menu: ")

        if choice == "1":
            create_server(conn)
        elif choice == "2":
            join_server(conn)
        elif choice == "3":
            inventory_menu(conn, reg_id)
        elif choice == "4":
            result = account_menu(conn, reg_id)
            if result == "deleted":
                print("You have been logged out automatically.")
                break
        elif choice == "5":
            print("Logged out successfully.")
            break
        else:
            print("Invalid option. Try again.")

def main():
    conn = connect_db()
    while True:
        print("\n=== Main Menu ===")
        print("1. Login")
        print("2. Registration")
        print("3. Exit")
        choice = input("Choose menu: ")

        if choice == "1":
            login_user(conn)
        elif choice == "2":
            register_user(conn)
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid option. Try again.")

    conn.close()

if __name__ == "__main__":
    main()
