import sqlite3 as sql, tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfile
import re
from datetime import timedelta, datetime, time, date
from functools import partial

class Application(tk.Frame):

	def __init__(self, master  = None):
		# Create Main Window
		self.root = tk.Tk()
		self.root.title("Vaccine Clinic Time Keeper")

		# When the user goes to close the program, run the on_close function to save the database before closing
		self.root.protocol("WM_DELETE_WINDOW", self.on_close)

		# Assign the root window as the master
		master = self.root
		super().__init__(master)

		# Load the time keeper database
		self.database = Vaccine_Time_Log()

		# Calls the build_page method to build the main application page.
		self.pack()
		self.build_page()

		# Applies the menu created in build_page to the menu bar
		self.root.config(menu = self.menu_bar)

	def on_close(self):
		''' When the user closes the program initiates the database.close() method to commit all changes to the database
			before closing the connection and terminating the application window.'''

		# If yes, call the database.close() method and destroy the root.
		self.database.close()
		self.root.destroy()

	def build_page(self):
		''' Creates the widgets for the main application page.
			The application has:
			 	1) A dropdown menu at the top to select the role
				2) A drowdown menu below that to select the user
				3) A set of spinboxs to select the hour and minutes of the check in
				4) A set of spinboxs to select the hour and minutes of the check out
				5) A button to check in
				6) A menu at the top with
					a) option to add a user
					b) option to save the database
					c) option to remove a user ***
					d) option to reset the database
		'''
		# Builds the file menu
		self.build_menu()

		# creates a frame for the two dropdown selection widgets
		self.selection_frame = tk.Frame(self)
		self.selection_frame.grid(row = 0, column = 0, sticky = 'w')

		# Creates the two dropdown selection widgets. One for the role and one for the name
		self.role_selection = Drop_Down_Selection(container = self.selection_frame, row = 0, title = "Role", func = self.role_selected)
		self.name_selection = Drop_Down_Selection(container = self.selection_frame, row = 1, title = "Name", func = self.name_selected, state = 'disabled')

		# Retrieves the roles from the database and adds them to the role dropdown
		self.get_roles()

		# Creates a frame for the four spinboxs
		self.time_frame = tk.Frame(self)
		self.time_frame.grid(row = 2, column = 0, sticky = 'w')

		# Creates the two sets of spinboxs, one for the in time and one for the out time.
		self.in_time = Time_Entry(self.time_frame, row = 0, column = 0, title = "In", padding = (5,27))
		self.out_time = Time_Entry(self.time_frame, row = 0, column = 3, title = "Out", padding = (50,5))

		# Sets up the check-in button - the button is initially disabled until a name is selected
		self.button_frame = tk.Frame(self)
		self.button_frame.grid(row = 3, column = 0)
		self.check_in_button = tk.Button(self.button_frame, text = "Check In", width = 20, command = self.check_in)
		self.check_in_button.grid(row = 0, column = 0, pady = 5)
		self.check_in_button.configure(state = 'disabled')

	def build_menu(self):
		''' builds the menu bar for the application and adds all the options to the bar'''

		# Set up the menu bar for the main application
		self.menu_bar = tk.Menu(self.root)

		# Creates a new menu cascade for file/user actions
		self.file_menu = tk.Menu(self.menu_bar, tearoff = 0)

		# Adds commands for saving, clearing the form, and activating and deactivating a user to the file menu tab
		self.file_menu.add_command(label = "Save", command = self.save_database)
		self.file_menu.add_command(label = "Clear Form", command = self.reset_form)
		self.file_menu.add_command(label = "Add User", command = self.add_user_window)
		self.file_menu.add_command(label = "Activate User", command = partial(self.change_user_status, 1))
		self.file_menu.add_command(label = "Deactivate User", command = partial(self.change_user_status, 0))
		self.file_menu.add_command(label = "Export Time Data", command = self.database.export_time)

		# Names the cascade 'File' and and adds it to the menu bar
		self.menu_bar.add_cascade(label = "File", menu=self.file_menu)

	def get_roles(self):
		'''Updates the values in the role selection dropdown with the list of roles
			returned by the database.get_role function'''

		self.role_selection.update_values(self.database.get_role())

	def role_selected(self, event):
		'''Once a role is selected, enables the name selection dropdown and
			updates the values in the name selection dropdown with the list of names
			returned by the database.get_names function'''

		# Enables the name selection drop down
		self.name_selection.enable()

		# Stores a list of User objects for matching selected names to tablenames
		self.users = self.database.get_names("role LIKE '{}' AND status = 1".format(self.role_selection.get()))

		# Retrieves a list of the user labels from the user objects and updates the name selection
		# dropdown with that list of names
		self.name_selection.update_values([i.get_label() for i in self.users])

	def name_selected(self, event):
		'''Once a name is selected, enables the time entry spinboxs and the check-in button'''

		self.in_time.enable()
		self.out_time.enable()
		self.check_in_button.configure(state = 'normal')

	def check_in(self):
		''' This runs when the check-in button is pressed
			checks that the entered times denote a positive time frame and if so
			matches the user to the table name and calls the database.check_in function
			to update the users log'''

		# Retrieves the times from the two sets of spinboxs
		in_time = time.fromisoformat(self.in_time.get())
		out_time = time.fromisoformat(self.out_time.get())

		# checks to see if the out time is after the in time
		if out_time <= in_time:

		# If it is not, notifies the user that the checkout must be after the check in
			self.error_window("Check out time must be after check in")

		# Otherwise, retrieves the name from the name selection dropdown
		else:
			name = self.name_selection.get()

		# Steps through the stored list of users
			for i in self.users:

		# Checks if the retrieved name matches the label for the user
				if name == i.get_label():

		# Once a match is found, it retrieves the name from the user object and exits the loop
					table_name = i.get_table_name()
					break

		# Calls the database.check-in function to log the date, in time,
		#	and out time to the table_name for that user
			self.database.check_in(table_name, date.today(), in_time.isoformat('minutes'), out_time.isoformat('minutes'))

		# Resets the information in the form and notifies the user that they have been checked in
			self.reset_form()
			self.error_window("Checked In", "")

	def reset_database(self):
		''' This function allows the user to reset the database. Calls the database.clear_database function '''

		#This needs to have a check to confirm that you really want to do it.
		self.database.clear_database()

	def save_database(self):
		''' Calls the database.save function to save the database'''
		self.database.save()

	def add_user_window(self):
		''' Creates a pop-out window for the user to enter the information to add a user
				This window has:
					1) An entry box for the first name
					2) An entry box for the last name
					3) A drop down menu to select the users role
					4) An entry box for the users email
					5) An entry box for the users phone Number
					6) A button to add the user'''

		# Creates a new window, with the title add user
		self.new_user_window = tk.Toplevel()
		self.new_user_window.title("Add User")

		# Creates a frame within this window to hold the entry widgets
		self.entry_frame = tk.Frame(self.new_user_window)
		self.entry_frame.grid(row = 0, column = 0)

		# Creates the labels for all the entry widgets
		tk.Label(self.entry_frame, text = "First Name (Required)").grid(row = 0, column = 0, padx = 5, stick = "w")
		tk.Label(self.entry_frame, text = "Last Name (Required)").grid(row = 1, column = 0, padx = 5, stick = "w")
		tk.Label(self.entry_frame, text = "Role (Required)").grid(row = 2, column = 0, padx = 5, stick = "w")
		tk.Label(self.entry_frame, text = "Email").grid(row = 3, column = 0, padx = 5, stick = "w")
		tk.Label(self.entry_frame, text = "Phone Number").grid(row = 4, column = 0, padx = 5, stick = "w")

		# Creates the two name entry widgets
		self.new_user_first_name = tk.Entry(self.entry_frame, width = 35)
		self.new_user_last_name = tk.Entry(self.entry_frame, width = 35)

		# Creates a variable and the combobox for the role, populates the combobox with all possible roles
		self.new_user_role_variable = tk.StringVar()
		self.new_user_role = ttk.Combobox(self.entry_frame, textvariable = self.new_user_role_variable, width = 33)
		self.new_user_role['values'] = ['OMS', 'Staff', 'Public Health Services', 'Volunteer']

		# Creates two entry widgets for the email and phone number
		self.new_user_email = tk.Entry(self.entry_frame, width = 35)
		self.new_user_phone = tk.Entry(self.entry_frame, width = 35)

		# Places all the entry widgets on the frame
		self.new_user_first_name.grid(row = 0, columnspan = 2, column = 1, pady = 5)
		self.new_user_last_name.grid(row = 1, columnspan = 2, column = 1, pady = 5)
		self.new_user_role.grid(row = 2, columnspan = 2, column = 1, pady = 5)
		self.new_user_email.grid(row = 3, columnspan = 2, column = 1, pady = 5)
		self.new_user_phone.grid(row = 4, columnspan = 2, column = 1, pady = 5)

		# Creates a frame for the button
		self.new_user_button_frame = tk.Frame(self.new_user_window)
		self.new_user_button_frame.grid(row = 1, column = 0)

		# Adds a button for the user to press to run the add_user function
		self.create_user_button = tk.Button(self.new_user_button_frame, text = "Add User", width = 20, command = self.add_user)
		self.create_user_button.grid(row = 0, columnspan = 1, column = 0, pady = 5)

	def add_user(self):
		''' This is run when the button on the add_user_window page is pressed. It retrieves all the
			information in the entry widgets and checks to see if the three required fields
			(first name, last name, role) were filled. If they are not, notifies the user that
			the fields are required. If they are, adds the user to the database with the
			database.add_user function and updates the roles in the role selection widget before
			destroying the window'''

		# Retrieves the data from the four entry widgets and the one combobox selection widget
		# The four entry widget values are passed through the clean_input function
		first_name = self.clean_input(self.new_user_first_name.get())
		last_name =  self.clean_input(self.new_user_last_name.get())
		role = self.new_user_role_variable.get()
		email = self.clean_input(self.new_user_email.get())
		phone = self.clean_input(self.new_user_phone.get())

		# Checks to see that the first name, last name and role were not left empty
		if "" in [first_name, last_name, role]:

		# If they were, prompts the user that the fields are required
			self.error_window("Please Enter Required Fields")

		# Otherwise, calls the database.add_user function to add the user
		else:
			self.database.add_user(first_name, last_name, role, email, phone)

		# Updates the roles in the role selection dropdown
			self.get_roles()

		# Destroys the add_user_window
			self.new_user_window.destroy()

	def change_user_status(self, status):
		''' Takes the status to change the user to and updates the status of a user so they do or do not show up
			in the dropdown menus, without removing them completely from the database.'''

		# Checks to see which status was passed to the function and passes it along to the window to be built
		# along with the window and button title
		if status == 1:
			self.change_user_status_window("Activate User", 1)
		else:
			self.change_user_status_window("Deactivate User", 0)

	def change_user_status_window(self, title, status):
		''' Takes the window/button title and the status to change a user to
		and builds the window to allow the user to select the user to activate/ deactivate
				This window has:
					1) An entry box for the first name
					2) An entry box for the last name
					3) A dropdown selection for the role
					4) An entry box for the email
					5) An entry box for the phone number
					6) A button to find the user
					7) A dropdown selection for the filtered users
					8) A button to activate/ deactivate the selected user
			Any amount of information can be entered to help filter the user. The user selection
			dropdown loads with all relevant users'''

		# Checks to see if the status is 1 to activate users, sets the status_filter to 0 to select all
		# deactivated users. otherwise sets to 1 to find all activated users when trying to deactivate
		if status == 1:
			status_filter = 0
		else:
			status_filter = 1

		# Creates the pop-out window
		self.user_status_window = tk.Toplevel()
		self.user_status_window.title(title)

		# Creates a frame to house the entry boxes
		entry_frame = tk.Frame(self.user_status_window)
		entry_frame.grid(row = 0, column = 0)

		# Creates all the labels for the entry widgets
		tk.Label(entry_frame, text = "First Name").grid(row = 0, column = 0, padx = 5, stick = "w")
		tk.Label(entry_frame, text = "Last Name").grid(row = 1, column = 0, padx = 5, stick = "w")
		tk.Label(entry_frame, text = "Role").grid(row = 2, column = 0, padx = 5, stick = "w")
		tk.Label(entry_frame, text = "Email").grid(row = 3, column = 0, padx = 5, stick = "w")
		tk.Label(entry_frame, text = "Phone Number").grid(row = 4, column = 0, padx = 5, stick = "w")
		tk.Label(entry_frame, text = "Select User").grid(row = 7, column = 0, padx = 5, stick = "w")

		# Creates the two name entry boxes
		self.user_status_first_name = tk.Entry(entry_frame, width = 35)
		self.user_status_last_name = tk.Entry(entry_frame, width = 35)

		# Creates the variable and combobox for the roles, populates the roles with all possible options
		self.user_status_role_variable = tk.StringVar()
		self.user_status_role = ttk.Combobox(entry_frame, textvariable = self.user_status_role_variable, width = 33)
		self.user_status_role['values'] = ['OMS', 'Staff', 'Public Health Services', 'Volunteer']

		# Creates two entry boxes for the email and phone number
		self.user_status_email = tk.Entry(entry_frame, width = 35)
		self.user_status_phone = tk.Entry(entry_frame, width = 35)

		# Places the widgets on the grid
		self.user_status_first_name.grid(row = 0, columnspan = 2, column = 1, pady = 5)
		self.user_status_last_name.grid(row = 1, columnspan = 2, column = 1, pady = 5)
		self.user_status_role.grid(row = 2, columnspan = 2, column = 1, pady = 5)
		self.user_status_email.grid(row = 3, columnspan = 2, column = 1, pady = 5)
		self.user_status_phone.grid(row = 4, columnspan = 2, column = 1, pady = 5)

		# Creates a button to call the find_user function to retrieve the filters and update the list of users
		tk.Button(entry_frame, text = "Find user", width = 20, command = partial(self.find_user, status_filter)).grid(row = 5, columnspan = 3, column = 0, pady = 5)

		# Creates the variable and combobox for the list of users.
		self.user_status_selection_variable = tk.StringVar()
		self.user_status_selection = ttk.Combobox(entry_frame, textvariable = self.user_status_selection_variable, width = 33)

		# Sets the values of the dropdown selection as the list of all activated/ deactivated users
		self.user_status_list = self.database.get_names("status = {}".format(status_filter))
		self.user_status_selection['values'] = [i.get_label() for i in self.user_status_list]
		self.user_status_selection.grid(row = 7, columnspan = 2, column = 1, pady = 5)

		# Creates a button to run the execute_status_change function to update the user status
		tk.Button(entry_frame, text = title, width = 20, command = partial(self.execute_status_change, status)).grid(row = 8, columnspan = 3, column = 0, pady = 5)

	def find_user(self, status):
		''' Takes the filter_status and retrieves the data from the entry widgets and creates a filter string
			to pass to the database.filter_users function'''

		# Retrieves all the data from the four entry boxes and the dropdown selection.
		# The entry box data is passed through the clean_input function
		first_name = self.clean_input(self.user_status_first_name.get())
		last_name = self.clean_input(self.user_status_last_name.get())
		role = self.user_status_role.get()
		email = self.clean_input(self.user_status_email.get())
		phone = self.clean_input(self.user_status_phone.get())

		# Creates the filter string; starting with the user status which will always be supplied
		filter = "status = {} ".format(status)

		# Steps through a zipped list of labels and retrieved values
		for key, value in zip(['last_name', 'first_name', 'email', 'role', 'phone_number'], [last_name, first_name, email, role, phone]):

		# Checks that the retrieved value is not empty, if it isn't, add it to the filter string
			if value != "":
				filter += "AND {} LIKE '{}' ".format(key, value)

		# Removes the padded space that will be at the end
		filter = filter.strip(" ")

		# Passes the filter to database.filter_users, and retrieves the filtered list
		self.user_status_list = self.database.get_names(filter)

		# Updates the user selection  dropdown on the status update window with the list of filtered users
		self.user_status_selection['values'] = [i.get_label() for i in self.user_status_list]

	def execute_status_change(self, status):
		''' Called when the activate user/ deactivate user button is pressed on the change_user_status_window
			takes the status to change the user to, gets the user and compares them to the list of users and
			calls the database.update_status function to update the user'''

		# Retrieves the name from the dropdown selection
		name = self.user_status_selection.get()

		# Checks that a name was selected
		if name != "":

			# Checks the name against the labels in the stored user list (unique to the user status window)
			for i in self.user_status_list:

			# If the name matches the label, retrieves the table name and breaks the loop
				if name == i.get_label():
					table_name = i.get_table_name()
					break

			# Calls the database.update_status function with the table name and the status to update the user
			self.database.update_status(table_name, status)

			# Destroys the change_user_status_window
			self.user_status_window.destroy()

			# Updates the list of roles in the dropdown selection
			self.get_roles()

	def clean_input(self, input):
		''' Used to do a brief sanitization of the inputs in the entry boxes
			as a basic prevention of sql injection attacks.
			Takes a string and returns the updated string.

			It is intended that only admins would be using the entry boxes.
			The general users would be selecting names/ roles and using spinboxes for time entries'''

		# replaces single and double quotes with spaces
		return re.sub(r'[\'\"]', ' ', input)

	def reset_form(self):
		''' Clears the data in the form'''

		# Calls the build_page function to clear all entered data in the form.
		self.build_page()

	def error_window(self, message, window_title = "Error"):
		''' Takes a message and the window tittle and creates a window to notify the user'''

		# Creates a window
		window  = tk.Toplevel()
		window.title(window_title)

		# creates a message on the window with the given string
		tk.Label(window, text = '{}'.format(message)).grid(row = 0,  column = 0, pady = 5, padx = 20)

		# Creates a button to allow the user to close the window.
		tk.Button(window, text = 'OK', width = 10, command = lambda :window.destroy()).grid(row = 1, column = 0, pady = 5)

class Vaccine_Time_Log():
	def __init__(self):
		""" connects to the Vaccine_Time_Log database, sets-up a database cursor and runs the setup method """

		self.conn = sql.connect("Vaccine_Time_Log")
		self.cursor = self.conn.cursor()
		self.setup()

	def setup(self):
		'''Creates the users table if it does not exist with columns titled:
			table name as primary key, last name as text, first name as text,
			user status as an integer, email as text, role as text, phone Number
			as text, and the lifetime user total as an integer'''

		self.cursor.execute("CREATE TABLE IF NOT EXISTS users (table_name TEXT PRIMARY KEY, last_name TEXT, first_name TEXT, status INTEGER, email TEXT, role TEXT, phone_number TEXT, life_time_total INTEGER)")

	def add_user(self, first_name, last_name, role, email = 'NA', phone_number = 'NA'):
		''' Takes the first name, last name, role, email and phone number and adds them to the users table as an
			active user. Creates a new table to log that users hours'''

		# retrieves a list of names that match the name trying to be added
		# This listed is ordered in desending order by the table name
		name_list = self.check_name(first_name, last_name)

		# If the list of matched names is greater than 0
		if len(name_list) > 0:

		# Retrieves the first name from the list (the highest table_name indices)
		# and splits the name into its three parts 'first_last_xx'
			name = name_list[0].split('_')

		# Retrieves the indices portion of the name and adds 1 to it.
			name_ind = int(name[2]) + 1

		# Creates the table name for the new user with the first name, last name and the increased indices
			table_name = "{}_{}_{}{}".format(first_name, last_name, 0 if name_ind < 10 else "", name_ind)

		# If no other users are found creates the table name with the indices 00
		else:
			table_name = "{}_{}_00".format(first_name, last_name)

		# Inserts the user into the users table
		self.cursor.execute("INSERT INTO users (table_name, last_name, first_name, status, email, role, phone_number, life_time_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (table_name, last_name, first_name, 1, email, role, phone_number, 0))

		# Runs the create_user_table function to create a log for the users hours
		self.create_user_table(table_name)

	def check_name(self, first_name, last_name, status = '%'):
		''' returns a list of table_names from the users table that match the first and last name given.
			Defaults to returning a list of all active and deactive users'''

		name_list = self.cursor.execute('''SELECT table_name
											FROM users
											WHERE first_name LIKE ? AND last_name LIKE ?
											ORDER BY table_name DESC''', (first_name, last_name)).fetchall()
		return [i[0] for i in name_list]

	def create_user_table(self, table_name):
		''' Creates a table for the user with the title as the unique table_name of the user'''

		self.cursor.execute("CREATE TABLE {} (entry INTEGER PRIMARY KEY, date TEXT, in_time TEXT, out_time TEXT)".format(table_name))

	def get_role(self, status = 1):
		''' Returns a list of roles from the users table, defaults to returning only active roles'''

		role_list = self.cursor.execute('''SELECT DISTINCT role
											FROM users
											WHERE status = ?''', (status,))
		return [i[0] for i in role_list]

	def get_names(self, filter):
		''' Returns a list of user objects created from the users in the users table with the supplied filter'''

		# Retrieves the list of names from the table
		name_list = self.cursor.execute('''SELECT table_name, first_name, last_name, email
											FROM users
											WHERE {}'''.format(filter)).fetchall()

		# Creates a list to house the user objects
		user_sublist = []

		# For each entry in the table
		for table_name, first, last, email in name_list:

		# Creates a user with the first, name, last name and email
		# (these are used to create the user label that shows in the selection boxes)
			user_sublist += [User(table_name, first, last, email)]

		# returns the list of user objects
		return user_sublist

	def check_in(self, table_name, work_date, in_time, out_time):
		''' Takes the table_name of the user, the date, and the in and out times and
			logs the times into the users log and updates the users total hours in the users table'''

		# Finds the length of the shift
		time_difference = self.get_difference(in_time, out_time)

		# Enters the date and hours into the users log
		self.cursor.execute("INSERT INTO {} (date, in_time, out_time) VALUES (?, ?, ?)".format(table_name), (work_date, in_time, out_time))

		# Updates the users table with the number of hours worked
		self.cursor.execute("UPDATE users SET life_time_total = life_time_total + ? WHERE table_name = ?", (time_difference, table_name))

	def update_status(self, table_name, status):
		''' takes the table name for a user and the status to update that user to
			and updates the user to that status'''

		self.cursor.execute("UPDATE users SET status = ? WHERE table_name = ?", (status, table_name))

	def get_difference(self, in_time, out_time):
		''' finds the difference between two given times with formats hh:mm
			and returns the number of fractional hours '''

		# Splits the in time and out time into the hours and minutes
		in_hour, in_minute = in_time.split(":")
		out_hour, out_minute = out_time.split(":")

		# Creates timedelta objects with the in time and out time
		in_t = timedelta(hours = int(in_hour), minutes = int(in_minute))
		out_t = timedelta(hours = int(out_hour), minutes = int(out_minute))

		# retrieves the total time between the two times
		total_time = "{}".format(out_t - in_t)

		# Splits the duration into hours, minute, and seconds
		total_hours, total_minutes, total_seconds = total_time.split(":")

		# Returns the number of fractional hours
		return int(total_hours) + int(total_minutes) / 60

	def export_time(self):
		''' Called to export the number of hours for each user in the last week, last month and all time
			Also gives the total number of hours for all users for the last week, last month and all time'''

		# Finds the date from one week ago
		one_week = "{}".format(date.today() -  timedelta(7))

		# Finds the date from one month ago (30 days)
		one_month = "{}".format(date.today() - timedelta(30))

		# Sets variables for the total number of hours in the last week, last month and all time
		total_week = 0
		total_month = 0
		total_time = 0

		# retrieves a list of table names, first names and last names from the users table
		users_data = self.cursor.execute('''SELECT first_name, last_name, table_name
											FROM users
											ORDER BY last_name DESC''').fetchall()

		# Asks where to save the log
		with asksaveasfile(mode = 'w', defaultextension = '.txt') as file:

		# Writes the header for the file.
			file.write("Last Name\tFirst Name\tWeekly Total\tMonthly Total\tTotal Hours\n")

		# For each user in the users table
			for first_name, last_name, table_name in users_data:

		# Creates variables to track the individuals weekly, monthly and total hours
				user_weekly_total = 0
				user_monthly_total = 0
				user_total = 0

		# retrieves the list of hours from the users hour log table
				users_time_data = self.cursor.execute("SELECT date, in_time, out_time from {}".format(table_name)).fetchall()

		# for each entry in the log
				for work_date, in_time, out_time in users_time_data:

		# Finds the amount of time worked in the entry
					time_difference = self.get_difference(in_time, out_time)

		# Adds the time to the users total
					user_total += time_difference

		# If the date was less than a week ago; adds the total to the weeks total
					if work_date >= one_week:
						user_weekly_total += time_difference

		# If the date was less than 30 days ago; adds the total to the months total
					if work_date >= one_month:
						user_monthly_total += time_difference

		# Updates the corresponding all user totals with the individuals totals
				total_week += user_weekly_total
				total_month	+= user_monthly_total
				total_time += user_total

		# Writes the users data to the export file
				file.write("{}\t{}\t{}\t{}\t{}\n".format(last_name, first_name, user_weekly_total, user_monthly_total, user_total))

		# Finally, writes the totals to the bottom of the sheet
			file.write("\nWeekly Total\t{}\nMonthly total\t{}\nTotal\t{}".format(total_week, total_month, total_time))

	def close(self):
		''' Called on the closing of the application, commits all changes and closes the database'''

		self.conn.commit()
		self.conn.close()

	def save(self):
		''' Called to save the database, commits all changes'''

		self.conn.commit()

	def clear_database(self):
		''' Resets the database by stepping through the users table to drop all individual user logs and then
			dropping the users table'''

		# retrieves the list of user tables
		tables = self.cursor.execute('''SELECT table_name
										FROM users''').fetchall()

		# Drops all of the individual user tables
		for i in tables:
			self.cursor.execute("DROP TABLE {}".format(i[0]))

		# Drops the users table
		self.cursor.execute('DROP TABLE users')

class User():
	def __init__(self, table_name, first_name, last_name, email):
		''' Takes the table name, first name, last name, and email for a user
			and creates a label for that user from the first name, last name and email'''

		# Stores the table name, first name, last name, and email to the object
		self.table_name = table_name
		self.first_name = first_name
		self.last_name = last_name
		self.email = email

		# Creates a label for the selection dropdowns from the last name, first name, and email.
		self.label = "{}, {} {}".format(self.last_name, self.first_name, "({})".format(self.email) if self.email != "NA" and self.email != "" else "")

	def get_label(self):
		''' returns the users label'''
		return self.label

	def get_table_name(self):
		''' returns the users unique table name'''
		return self.table_name

class Drop_Down_Selection():
	def __init__(self, container, row, title, func, state = 'enabled'):
		''' creates a grouped label and selection box inside a given container at a given row
			with a title, a given function and a given state'''

		# Creates a label for the combobox with the given label
		self.label = tk.Label(container, text = title).grid(row = row, column = 0, padx = 5, stick = "w")

		# Creates a variable and combobox for the dropdown selection
		self.var = tk.StringVar()
		self.entry = ttk.Combobox(container, textvariable = self.var, width = 33)

		# places the combobox and adds the function
		self.entry.grid(row = row, column = 1, columnspan = 1, pady = 5)
		self.entry.bind("<<ComboboxSelected>>", func)

		# Sets the state of the widget
		self.entry.configure(state = state)

	def enable(self):
		'''Enables the dropdown selection widget'''

		self.entry.configure(state = 'enabled')

	def disable(self):
		'''Disables the dropdown selection widget'''

		self.entry.configure(state = 'disabled')

	def update_values(self, values):
		'''Updates the values in the dropdown selection widget'''

		self.entry['values'] = values

	def get(self):
		''' Returns the selected value from the widget'''

		return self.entry.get()

class Time_Entry():
	def __init__(self, container, row, column, title, padding = (5,5)):
		''' Creates a group with a label and two spinboxes to select the hours and minutes
			This grouping is created in a given container at a given row and column with a supplied padding
			around the label'''

		# Creates the hours in military time. The hours start at 8 and end at 7
		hours = ('08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '00', '01', '02', '03', '04', '05', '06', '07')

		# Creates a list of minutes. Decided to do 15 minute increments for speed of check-in.
		# This could be updated if finer control was needed
		minutes = ('00', '15', '30', '45')

		# Creates a label for the group
		self.label = tk.Label(container, text = title).grid(row = row, column = column, padx = padding, stick = "w")

		# Creates two spinboxes, one for the hours and one for the minutes
		self.hour = tk.Spinbox(container, values = hours, wrap = True, width = 3)
		self.minute = tk.Spinbox(container, values = minutes, wrap = True, width = 3)

		# Places the spinboxes on the grid
		self.hour.grid(row = row, column = column + 1, pady = 5, stick = "w")
		self.minute.grid(row = row, column = column + 2, pady = 5, stick = "e")

		# Disables the two spinboxes
		self.disable()

	def enable(self):
		''' enables the two spinboxes'''

		self.hour.configure(state = 'normal')
		self.minute.configure(state = 'normal')

	def disable(self):
		''' disables the two spinboxes'''

		self.hour.configure(state = 'disabled')
		self.minute.configure(state = 'disabled')

	def get(self):
		''' returns the hours and minutes from the two spinboxes in the format hh:mm'''

		return '{}:{}'.format(self.hour.get(), self.minute.get())

app = Application()
app.mainloop()
