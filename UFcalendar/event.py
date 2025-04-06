import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import datetime
from tkcalendar import Calendar

class EventCalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Event Calendar")
        self.root.geometry("800x600")
        
        # Set theme and style
        style = ttk.Style()
        style.theme_use('clam')  # You can try different themes like 'alt', 'default', 'classic'
        
        # Create a sample JSON file if it doesn't exist
        self.events_file = 'events.json'
        self.create_sample_events_file()
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create split view
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True)
        
        # Left side - Calendar
        self.calendar_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.calendar_frame, weight=1)
        
        # Right side - Event list and details
        self.event_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.event_frame, weight=1)
        
        # Set up calendar
        self.setup_calendar()
        
        # Set up event display
        self.setup_event_display()
        
        # Set up buttons
        self.setup_buttons()
        
        # Load and display events
        self.load_and_display_events()

    def create_sample_events_file(self):
        """Create a sample events file if it doesn't exist"""
        if not os.path.exists(self.events_file):
            sample_events = {
                "events": [
                    {
                        "name": "AI Image Generators Workshop",
                        "date": "2025-04-15",
                        "time": "14:00",
                        "location": "Online",
                        "description": "Learn about AI image generation technologies"
                    },
                    {
                        "name": "Florida Gators Basketball Game",
                        "date": "2025-04-20",
                        "time": "19:30",
                        "location": "O'Connell Center",
                        "description": "Home game against rival team"
                    }
                ]
            }
            
            try:
                with open(self.events_file, 'w') as file:
                    json.dump(sample_events, file, indent=2)
            except Exception as e:
                print(f"Error creating sample file: {e}")

    def setup_calendar(self):
        """Set up the calendar widget"""
        today = datetime.date.today()
        self.cal = Calendar(
            self.calendar_frame, 
            selectmode='day',
            year=today.year, 
            month=today.month, 
            day=today.day,
            background='#f0f0f0',
            foreground='#333333',
            bordercolor='#cccccc',
            headersbackground='#e6e6e6',
            headersforeground='#333333',
            selectbackground='#4a6984',
            weekendbackground='#f5f5f5',
            weekendforeground='#666666',
            othermonthforeground='#999999',
            othermonthbackground='#f8f8f8',
            othermonthweforeground='#b3b3b3',
            othermonthwebackground='#f8f8f8',
            font=("Arial", 10)
        )
        self.cal.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind calendar selection
        self.cal.bind("<<CalendarSelected>>", self.on_date_selected)

    def setup_event_display(self):
        """Set up the event display area"""
        # Date label
        self.date_label = ttk.Label(
            self.event_frame, 
            text="Selected Date: None", 
            font=("Arial", 12, "bold")
        )
        self.date_label.pack(pady=(10, 5), anchor="w")
        
        # Events for selected date label
        self.events_label = ttk.Label(
            self.event_frame, 
            text="Events:", 
            font=("Arial", 11)
        )
        self.events_label.pack(pady=(5, 0), anchor="w")
        
        # Events listbox with scrollbar
        list_frame = ttk.Frame(self.event_frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        self.event_listbox = tk.Listbox(
            list_frame,
            font=("Arial", 10),
            activestyle="none",
            selectbackground="#4a6984",
            selectforeground="white"
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.event_listbox.yview)
        self.event_listbox.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.event_listbox.pack(side="left", fill="both", expand=True)
        
        # Bind listbox selection
        self.event_listbox.bind("<<ListboxSelect>>", self.on_event_selected)
        
        # Event details frame
        self.details_frame = ttk.LabelFrame(self.event_frame, text="Event Details")
        self.details_frame.pack(fill="both", expand=True, pady=10)
        
        # Event details
        self.detail_text = tk.Text(
            self.details_frame, 
            height=10, 
            wrap=tk.WORD,
            font=("Arial", 10),
            state="disabled"
        )
        self.detail_text.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_buttons(self):
        """Set up action buttons"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill="x", pady=10)
        
        # Add event button
        self.add_button = ttk.Button(
            button_frame, 
            text="Add Event",
            command=self.add_event
        )
        self.add_button.pack(side="left", padx=5)
        
        # Edit event button
        self.edit_button = ttk.Button(
            button_frame, 
            text="Edit Event",
            command=self.edit_event,
            state="disabled"
        )
        self.edit_button.pack(side="left", padx=5)
        
        # Delete event button
        self.delete_button = ttk.Button(
            button_frame, 
            text="Delete Event",
            command=self.delete_event,
            state="disabled"
        )
        self.delete_button.pack(side="left", padx=5)
        
        # Refresh button
        self.refresh_button = ttk.Button(
            button_frame, 
            text="Refresh",
            command=self.load_and_display_events
        )
        self.refresh_button.pack(side="right", padx=5)

    def load_events(self):
        """Load events from the JSON file with robust error handling"""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r') as file:
                    try:
                        # Attempt to load as a standard JSON file
                        data = json.load(file)
                        
                        # Check if it's already in the expected format
                        if isinstance(data, dict) and "events" in data:
                            return data["events"]
                        # If it's a list already, return it
                        elif isinstance(data, list):
                            return data
                        # Otherwise, wrap it in a list
                        else:
                            return [data]
                    
                    except json.JSONDecodeError:
                        # If standard loading fails, try to fix the format
                        file.seek(0)  # Go back to start of file
                        content = file.read()
                        
                        # Try to fix various common JSON issues
                        # 1. Missing outer brackets
                        if not content.strip().startswith('['):
                            content = '[' + content
                        if not content.strip().endswith(']'):
                            content = content + ']'
                        
                        # 2. Remove trailing commas
                        content = content.replace(',]', ']')
                        content = content.replace(',}', '}')
                        
                        # Try to parse the fixed content
                        try:
                            events = json.loads(content)
                            
                            # Write the fixed JSON back to the file
                            with open(self.events_file, 'w') as fix_file:
                                json.dump(events, fix_file, indent=2)
                                
                            return events if isinstance(events, list) else [events]
                        
                        except Exception as e:
                            messagebox.showerror("JSON Error", f"Could not parse the events file: {str(e)}")
                            return []
            else:
                return []
                
        except Exception as e:
            messagebox.showerror("File Error", f"Error loading events file: {str(e)}")
            return []

    def save_events(self, events):
        """Save events to the JSON file"""
        try:
            with open(self.events_file, 'w') as file:
                json.dump({"events": events}, file, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save events: {str(e)}")

    def load_and_display_events(self):
        """Load events and display them on the calendar"""
        # Clear existing calendar events
        for event_id in self.cal.get_calevents():
            self.cal.calevent_remove(event_id)
        
        # Load events
        self.events_data = self.load_events()
        
        # Add events to calendar
        for event in self.events_data:
            if isinstance(event, dict) and 'date' in event and 'name' in event:
                try:
                    event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d').date()
                    event_id = self.cal.calevent_create(
                        event_date, 
                        event['name'], 
                        'event'
                    )
                except Exception as e:
                    print(f"Error adding event to calendar: {str(e)}")
        
        # Configure tag
        self.cal.tag_config('event', background='#4a6984', foreground='white')
        
        # Update displayed events if a date is selected
        self.update_event_list()

    def update_event_list(self):
        """Update the event list for the selected date"""
        try:
            selected_date = self.cal.selection_get()
            date_str = selected_date.strftime('%Y-%m-%d')
            self.date_label.config(text=f"Selected Date: {selected_date.strftime('%B %d, %Y')}")
            
            # Filter events for the selected date
            filtered_events = [
                e for e in self.events_data 
                if isinstance(e, dict) and 'date' in e and e['date'] == date_str
            ]
            
            # Clear listbox
            self.event_listbox.delete(0, tk.END)
            
            # Add events to listbox
            if filtered_events:
                for event in filtered_events:
                    time_str = f" @ {event.get('time', 'All day')}" if event.get('time') else ""
                    self.event_listbox.insert(tk.END, f"{event['name']}{time_str}")
            else:
                self.event_listbox.insert(tk.END, "No events for this date")
                
            # Clear details
            self.clear_event_details()
            
        except Exception as e:
            print(f"Error updating event list: {str(e)}")

    def on_date_selected(self, event):
        """Handle date selection"""
        self.update_event_list()
        
    def on_event_selected(self, event):
        """Handle event selection from listbox"""
        try:
            # Get selected indices
            selection = self.event_listbox.curselection()
            
            if selection:
                index = selection[0]
                selected_date = self.cal.selection_get()
                date_str = selected_date.strftime('%Y-%m-%d')
                
                # Filter events for the selected date
                filtered_events = [
                    e for e in self.events_data 
                    if isinstance(e, dict) and 'date' in e and e['date'] == date_str
                ]
                
                if filtered_events and index < len(filtered_events):
                    # Enable edit and delete buttons
                    self.edit_button.config(state="normal")
                    self.delete_button.config(state="normal")
                    
                    # Show event details
                    self.show_event_details(filtered_events[index])
                else:
                    self.clear_event_details()
            else:
                self.clear_event_details()
                
        except Exception as e:
            print(f"Error on event selection: {str(e)}")
            
    def show_event_details(self, event):
        """Display event details"""
        # Enable text widget for editing
        self.detail_text.config(state="normal")
        
        # Clear previous content
        self.detail_text.delete(1.0, tk.END)
        
        # Add details
        detail_str = f"Event: {event['name']}\n\n"
        detail_str += f"Date: {event['date']}\n"
        
        if 'time' in event and event['time']:
            detail_str += f"Time: {event['time']}\n"
            
        if 'location' in event and event['location']:
            detail_str += f"Location: {event['location']}\n"
            
        if 'description' in event and event['description']:
            detail_str += f"\nDescription:\n{event['description']}\n"
            
        if 'link' in event and event['link']:
            detail_str += f"\nLink: {event['link']}\n"
            
        self.detail_text.insert(1.0, detail_str)
        
        # Disable text widget again
        self.detail_text.config(state="disabled")
        
    def clear_event_details(self):
        """Clear event details and disable edit/delete buttons"""
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.config(state="disabled")
        
        self.edit_button.config(state="disabled")
        self.delete_button.config(state="disabled")

    def add_event(self):
        """Add a new event"""
        try:
            # Get the selected date or default to today
            try:
                selected_date = self.cal.selection_get()
            except:
                selected_date = datetime.date.today()
                
            date_str = selected_date.strftime('%Y-%m-%d')
            
            # Create dialog for new event
            event_dialog = EventDialog(self.root, "Add New Event", date_str)
            
            if event_dialog.result:
                # Add new event to the events list
                self.events_data.append(event_dialog.result)
                
                # Save events
                self.save_events(self.events_data)
                
                # Refresh the display
                self.load_and_display_events()
                
                # Select the date for the new event
                new_date = datetime.datetime.strptime(event_dialog.result['date'], '%Y-%m-%d').date()
                self.cal.selection_set(new_date)
                
                # Update event list
                self.update_event_list()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not add event: {str(e)}")

    def edit_event(self):
        """Edit selected event"""
        try:
            selection = self.event_listbox.curselection()
            
            if selection:
                index = selection[0]
                selected_date = self.cal.selection_get()
                date_str = selected_date.strftime('%Y-%m-%d')
                
                # Filter events for the selected date
                filtered_events = [
                    e for e in self.events_data 
                    if isinstance(e, dict) and 'date' in e and e['date'] == date_str
                ]
                
                if filtered_events and index < len(filtered_events):
                    event = filtered_events[index]
                    
                    # Find this event in the main events list
                    main_index = self.events_data.index(event)
                    
                    # Create dialog for editing
                    event_dialog = EventDialog(self.root, "Edit Event", date_str, event)
                    
                    if event_dialog.result:
                        # Update event in the events list
                        self.events_data[main_index] = event_dialog.result
                        
                        # Save events
                        self.save_events(self.events_data)
                        
                        # Refresh the display
                        self.load_and_display_events()
                        
                        # Select the date for the edited event
                        new_date = datetime.datetime.strptime(event_dialog.result['date'], '%Y-%m-%d').date()
                        self.cal.selection_set(new_date)
                        
                        # Update event list
                        self.update_event_list()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not edit event: {str(e)}")

    def delete_event(self):
        """Delete selected event"""
        try:
            selection = self.event_listbox.curselection()
            
            if selection:
                index = selection[0]
                selected_date = self.cal.selection_get()
                date_str = selected_date.strftime('%Y-%m-%d')
                
                # Filter events for the selected date
                filtered_events = [
                    e for e in self.events_data 
                    if isinstance(e, dict) and 'date' in e and e['date'] == date_str
                ]
                
                if filtered_events and index < len(filtered_events):
                    event = filtered_events[index]
                    
                    # Confirm deletion
                    if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{event['name']}'?"):
                        # Remove event from the events list
                        self.events_data.remove(event)
                        
                        # Save events
                        self.save_events(self.events_data)
                        
                        # Refresh the display
                        self.load_and_display_events()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete event: {str(e)}")


class EventDialog:
    """Dialog for adding or editing events"""
    def __init__(self, parent, title, date_str, event=None):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_window(self.dialog, parent)
        
        # Create form
        self.create_form(date_str, event)
        
        # Wait for dialog to close
        parent.wait_window(self.dialog)
        
    def center_window(self, window, parent):
        """Center a window relative to its parent"""
        parent.update_idletasks()
        window.update_idletasks()
        
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        window.geometry(f"+{x}+{y}")
        
    def create_form(self, date_str, event=None):
        """Create the event form"""
        form_frame = ttk.Frame(self.dialog, padding="20 20 20 20")
        form_frame.pack(fill="both", expand=True)
        
        # Event name
        ttk.Label(form_frame, text="Event Name:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.name_var = tk.StringVar(value=event['name'] if event else "")
        ttk.Entry(form_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew", pady=(0, 5))
        
        # Event date
        ttk.Label(form_frame, text="Date:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.date_var = tk.StringVar(value=event['date'] if event else date_str)
        date_entry = ttk.Entry(form_frame, textvariable=self.date_var, width=30)
        date_entry.grid(row=1, column=1, sticky="w", pady=(0, 5))
        ttk.Button(form_frame, text="Pick", command=lambda: self.pick_date(date_entry)).grid(row=1, column=1, sticky="e", pady=(0, 5))
        
        # Event time
        ttk.Label(form_frame, text="Time:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.time_var = tk.StringVar(value=event['time'] if event and 'time' in event else "")
        time_entry = ttk.Entry(form_frame, textvariable=self.time_var, width=30)
        time_entry.grid(row=2, column=1, sticky="w", pady=(0, 5))
        ttk.Label(form_frame, text="(hh:mm)").grid(row=2, column=1, sticky="e", pady=(0, 5))
        
        # Location
        ttk.Label(form_frame, text="Location:").grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.location_var = tk.StringVar(value=event['location'] if event and 'location' in event else "")
        ttk.Entry(form_frame, textvariable=self.location_var, width=40).grid(row=3, column=1, sticky="ew", pady=(0, 5))
        
        # Link
        ttk.Label(form_frame, text="Link:").grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.link_var = tk.StringVar(value=event['link'] if event and 'link' in event else "")
        ttk.Entry(form_frame, textvariable=self.link_var, width=40).grid(row=4, column=1, sticky="ew", pady=(0, 5))
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=5, column=0, sticky="nw", pady=(5, 5))
        self.description_text = tk.Text(form_frame, width=30, height=10, wrap=tk.WORD)
        self.description_text.grid(row=5, column=1, sticky="ew", pady=(5, 5))
        
        # Add scrollbar to description
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=self.description_text.yview)
        scrollbar.grid(row=5, column=2, sticky="ns", pady=(5, 5))
        self.description_text.configure(yscrollcommand=scrollbar.set)
        
        # Set description text
        if event and 'description' in event:
            self.description_text.insert(1.0, event['description'])
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save_event).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side="left", padx=5)
        
    def pick_date(self, entry):
        """Show a calendar to pick a date"""
        top = tk.Toplevel(self.dialog)
        top.title("Pick a date")
        
        cal = Calendar(top, selectmode='day')
        cal.pack(padx=10, pady=10)
        
        # Try to set the calendar to the current date in the entry
        try:
            current_date = datetime.datetime.strptime(self.date_var.get(), '%Y-%m-%d').date()
            cal.selection_set(current_date)
        except:
            pass
        
        def on_select():
            selected_date = cal.selection_get()
            self.date_var.set(selected_date.strftime('%Y-%m-%d'))
            top.destroy()
            
        ttk.Button(top, text="Select", command=on_select).pack(pady=10)
        
    def save_event(self):
        """Save the event data"""
        # Validate inputs
        name = self.name_var.get().strip()
        date = self.date_var.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Event name is required")
            return
            
        if not date:
            messagebox.showerror("Error", "Event date is required")
            return
            
        try:
            # Validate date format
            datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return
            
        # Create event dict
        event = {
            "name": name,
            "date": date,
            "time": self.time_var.get().strip(),
            "location": self.location_var.get().strip(),
            "link": self.link_var.get().strip(),
            "description": self.description_text.get(1.0, tk.END).strip()
        }
        
        # Set result and close dialog
        self.result = event
        self.dialog.destroy()


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = EventCalendarApp(root)
    root.mainloop()