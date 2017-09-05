# Features

* Drill cards according to how well know them
* Drill cards on "hard mode" which only selects from your worst cards** Create your own card decks
* Share card decks with other users (enabled by default) or unpublish them to keep them private
* Clone other user's published decks, edit them, and even republish your customized version
* Tag decks to make them easier to find for other users
* Search for decks made by other users
* Sign up on the site by filling in information or by linking your Google account

# Installation

1. Clone the repository.

2. Install all dependencies. `pip install -r requirements.txt`

3. Install elasticsearch.

4. Put data into the search index. `python manage.py rebuild_index`

5. Run the server. `python manage.py runserver`

# Usage

Note that for entries from the database to show up in search results it will be necessary to refresh the search index periodically.

`python manage.py update_index`
