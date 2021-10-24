"""
Schedule
"""

import time
import os
import sqlite3
from datetime import date, timedelta
from calendar import monthrange
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class Schedule(toga.App):
    DATABASE_FILE = os.path.realpath(os.path.join(
        os.getcwd(),
        os.path.dirname(__file__),
        "schedule.db"))

    def year_selected(self, widget):
        self.year = widget.value
        self.update_day_select(self.year, self.month)
        self.update_assignments(self.year, self.month, self.day)

    def month_selected(self, widget):
        # update day select widget with correct number of days for chosen month
        self.month = widget.value
        self.update_day_select(self.year, self.month)
        self.update_assignments(self.year, self.month, self.day)

    def day_selected(self, widget):
        self.day = widget.value
        self.update_assignments(self.year, self.month, self.day)

    def update_day_select(self, year, month):
        # check that arguments are appropiate
        if not month: return
        if not year: return
        #updates the day select widget when month or year is changed
        year = int(year)
        month = int(month)
        all_days = [f"{day:0>2d}" for day in range(1, monthrange(year, month)[1] + 1)]
        self.day_select.items = all_days

    def update_assignments(self, year, month, day):
        if not month: return
        if not year: return
        if not day: return

        year = int(year)
        month = int(month)
        day = int(day)

        # calculate week starting monday including selected date
        selected_date = date(year, month, day)
        # monday = 0, if selected date = friday 4, this returns 4 days ago
        monday_date = selected_date + timedelta(days=-selected_date.weekday())
        sunday_date = monday_date + timedelta(days=6)

        # update the box with day labels
        if monday_date.month == sunday_date.month:
            spacer = monday_date.strftime("%b")
        else:
            spacer = f'{monday_date.strftime("%b")}-{sunday_date.strftime("%b")}'
        self.spacer_label.text = spacer
        for i, day_label in enumerate(self.date_box.children[1:]):
            day_label.text = f"{(monday_date + timedelta(days=i)).day}"


        # update assignments
        # connect to schedule database
        connection = sqlite3.connect(Schedule.DATABASE_FILE)
        cursor = connection.cursor()

        # get all the anesthesiologist names for date range
        anesthesiologists = cursor.execute(f'''
            SELECT DISTINCT anesthesiologist FROM assignments
            WHERE date BETWEEN "{monday_date}" AND "{sunday_date}"
            ''').fetchall()

        # update the assignments scaffolding
        for anes in self.assign_box.children:
            assign_labels = anes.children[1:]
            anes = anes.children[0].text
            # check that assignments exist for each date, add them
            dates = [monday_date + timedelta(days=i) for i in range(7)]
            for i, a_date in enumerate(dates):
                assign = cursor.execute(f'''
                    SELECT assignment FROM assignments
                    WHERE anesthesiologist = "{anes}"
                    AND date = "{a_date}"
                    ''').fetchone()
                assign = assign[0] if assign else "-"
                assign_labels[i].text = assign

    def next_clicked(self, widget):
        cur_date = date(int(self.year), int(self.month), int(self.day))
        next_week_date = cur_date + timedelta(weeks=1)
        self.year_select.value = f"{next_week_date.year:0>4d}"
        self.month_select.value = f"{next_week_date.month:0>2d}"
        self.day_select.value = f"{next_week_date.day:0>2d}"

    def prev_clicked(self, widget):
        cur_date = date(int(self.year), int(self.month), int(self.day))
        prev_week_date = cur_date + timedelta(weeks=-1)
        self.year_select.value = f"{prev_week_date.year:0>4d}"
        self.month_select.value = f"{prev_week_date.month:0>2d}"
        self.day_select.value = f"{prev_week_date.day:0>2d}"

    def startup(self):
        # connect to schedule database
        connection = sqlite3.connect(Schedule.DATABASE_FILE)
        cursor = connection.cursor()

        ## initial year month day
        self.year = date.today().year
        self.month = date.today().month

        # create box for row of weekdays, never changes for now
        weekday_box = toga.Box(style=Pack(direction=ROW))
        blank_label = toga.Label("", style=Pack(flex=2, padding=(5,5)))
        weekday_box.add(blank_label)
        for weekday in ['M','T','W','T','F','S','S']:
            weekday_label = toga.Label(weekday,
                    style=Pack(flex=1, text_align='center', padding=(5,5)))
            weekday_box.add(weekday_label)

        # create box for row of dates and labels for dates with initial dates
        self.date_box = toga.Box(style=Pack(direction=ROW))
        self.spacer_label = toga.Label('', style=Pack(flex=2, padding=(5,5)))
        self.date_box.add(self.spacer_label)
        for i in range(7):
            day_label = toga.Label("X",
                    style=Pack(flex=1, text_align='center', padding=(5,5)))
            self.date_box.add(day_label)

        # create box for assignments
        self.assign_box = toga.Box(style = Pack(direction=COLUMN))
        # get all the anesthesiologist names in the database
        anesthesiologists = cursor.execute(f'''
            SELECT DISTINCT anesthesiologist FROM assignments
            ''').fetchall()
        # create scaffolding for assignments
        for anes in anesthesiologists:
            # add the name of the anesthesiologist as a row
            anes = anes[0].strip()
            anes_label = toga.Label(anes, style=Pack(flex=2, padding=(5,5)))
            anes_box = toga.Box(style = Pack(direction=ROW))
            anes_box.add(anes_label)
            # add dummy assignments for each day
            for i in range(7):
                assign_label = toga.Label("X", style=Pack(flex=1,
                    text_align='center', padding=(5,5)))
                anes_box.add(assign_label)
            self.assign_box.add(anes_box)

        # get all dates in the database
        all_years = cursor.execute('''
            SELECT DISTINCT substr(date,1,4) FROM assignments
            ''').fetchall()
        all_years = [f"{year[0]:0>4s}" for year in all_years]
        all_months = [f"{month:0>2d}" for month in range(1,13)]
        all_days = [f"{day:0>2d}" for day in range(1,
            monthrange(self.year, self.month)[1] + 1)]
        # create initial select box and selections
        self.select_box = toga.Box(style=Pack(direction=ROW))
        self.year_select = toga.Selection(items=all_years,
                on_select=self.year_selected, style=Pack(flex=1))
        self.month_select = toga.Selection(items=all_months,
                on_select=self.month_selected, style=Pack(flex=1))
        self.day_select = toga.Selection(items=all_days,
                on_select=self.day_selected, style=Pack(flex=1))
        self.select_box.add(self.year_select)
        self.select_box.add(self.month_select)
        self.select_box.add(self.day_select)

        # create buttons for next and prev week
        button_box = toga.Box(style=Pack(direction=ROW))
        prev_button = toga.Button('Previous',
                on_press=self.prev_clicked, style=Pack(flex=1))
        next_button = toga.Button('Next',
                on_press=self.next_clicked, style=Pack(flex=1))
        button_box.add(prev_button)
        button_box.add(next_button)

        # create main box and add components
        main_box = toga.Box(style = Pack(direction=COLUMN))
        main_box.add(self.select_box)
        main_box.add(weekday_box)
        main_box.add(self.date_box)
        main_box.add(self.assign_box)
        main_box.add(button_box)

        # set selections to initial values, triggers update to assignments and day
        self.year_select.value = f"{self.year:0>4d}"
        self.month_select.value = f"{self.month:0>2d}"

        # set intial day, occurs here due to year and month select updates day select
        self.day = date.today().day
        self.day_select.value = f"{self.day:0>2d}"

        # create and show main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

def main():
    return Schedule()
