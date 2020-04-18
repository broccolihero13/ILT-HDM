# ILT-HDM
This is a CLI tool used to create Historical Data for Live Training enrollments for Bridge LMS. You'll need to have a CSV file with the appropriate format to process these historical enrollment records. Be sure to have the following Python modules (This version also works with Python 3.6 and 3.7)

Version 0.0.1 

----------Technologies Used----------
* Python 3.8.0
* Click 7.0
* Requests 2.22.0
* Pandas 0.25.3
* colorama 0.4.3


----------Usage----------

Bridge doesn't currently support a historical data migration for their Interactive Live Training (ILT) learning objects. So in order to move this ILT data from a previous LMS, this tool will take a CSV file of that data and creates a session (note: the ILT must already be created in Bridge and it's ID needs to be in the CSV file) for each unique concatenation of course-date*. Then it enrolls the user in each of those sessions*.
* note 1: Expects ISO 8601 date format (YYYY-MM-DD) and will grab the timezone from your Bridge database.
* note 2: this does not look for current dates in Bridge so it will create a brand new session for each of these dates and would create duplicates if you run this consecutively with the same file.


Author: broccolihero13