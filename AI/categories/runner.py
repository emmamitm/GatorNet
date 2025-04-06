import subprocess
import sys

def main():
    # Mapping of menu options to script filenames
    menu_options = {
        "1": ("Tuition Calculator", "tuition.py"),
        "2": ("Clubs Information", "clubs.py"),
        "3": ("Housing Details", "housing.py"),
        "4": ("Course Catalog", "courses.py"),
        "5": ("Library Services", "library.py"),
        "6": ("Upcoming Events", "events.py"),
        "0": ("Exit", None)
    }

    while True:
        # Display the menu
        print("\nPlease choose an option:")
        for key, (description, _) in menu_options.items():
            print(f"{key}. {description}")

        # Get user input
        choice = input("Enter the number of your choice: ").strip()

        if choice in menu_options:
            description, script = menu_options[choice]
            if script:
                print(f"\nLaunching {description}...\n")
                try:
                    # Execute the selected script
                    subprocess.run(["python3", script], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"An error occurred while running {script}: {e}")
                except FileNotFoundError:
                    print(f"Script {script} not found. Please ensure it exists in the current directory.")
            else:
                print("Exiting the menu. Goodbye!")
                sys.exit(0)
        else:
            print("Invalid selection. Please try again.")

if __name__ == "__main__":
    main()
