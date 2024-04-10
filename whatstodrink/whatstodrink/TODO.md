## DONE

Made cocktails and ingredients table
Made amounts table
Made made ratings table
LOGIN REGISTER and LOGOUT work as intended
Created Add Ingredient Page
Built manage stock page
Made add ingredient add to database
Built add cocktail page
Built add ingredient modal for add cocktail page
Made add ingredient modal refresh the ingredient select items in add cocktail
Made more ingredients button to copy ingredient select menu and made modal work
Made Manage stock update database - post method of manage stock
made amounts dialogue for each ingredient after add cocktail is submitted
Made add cocktail add to database - post method of add cocktail
Made index page load makeable cocktails
made common versions of every table to serve default options. User will add own on original tables.
Made default ingredients and cocktails.
Login, Logout, Register, Add Ingredients, Add Cocktail, Add Cocktail ingredient modal, and manage ingredients should all work. What's to drink Works.
Finished Starter List of cocktails - done but needs to finish second half of amounts
changed input method for add cocktail ingredients to autocomplete typing
Moved database add into amounts POST for add cocktail
Make sure they cant submit nothing on /amounts
Made 'modify ingredient' with rename and delete
Added option to see all cocktails
Made "modify cocktail" functionality with rename, delete, and change recipe
Implemented simplified name
Made viewcocktails default to all and added active class for buttons
Made option for all cocktails or my cocktails in what's to drink?
Made pages and backend for What's missing?
Made add ingredient in Add Cocktail update the search table without refreshing the page.
Updated modal design
started addcocktailWITHMODAL for switching amounts to a modal. Currently fades the page but doesn't open the mdoal.
fixed readonly on add cocktail
Made amounts a modal
Changed modify button to view in manage ingredients
moved form from modify modal to new html template and changed modal to viewModal
Capitalized Email in login and register
upgraded to bootstrap 5.3
moved modal in manageingredients to its own route to make it refresh every time it's opened. This will serve as a template for the others.
Fix location of modify button in view cocktails and switched layout to use bootstrap grid
Update whatsmissing pages to bootstrap grid
Convert all modals to htmx
Made names cleaner in db and added amaro type to amari
Made all accordions except whatstodrink? (not necessary) fit into the bootstrap grid
added rusty nail to cocktails
Added active search to manage ingredients
Added name and purpose headers to each page
Added notes field to ingredients
Moved explainer text into modals and added i icons to launch them
Changed margin of forms to max-width 500px
changed margin and height of modals
hid ingredient overview accordions on small viewports
moved modify button in view/edit farther right
Buy me a coffee link
Made clear search link appear when a search is in the url in manageingredients
Made about page and created about link on home page
Added dropdowns to menu bar
Implemented "hide common cocktails" and updated all cocktail views to account for this
Updated all cocktail views to load fragments of html with htmx by default instead of having it included in the page
Added spinners to all those views
All database interactions ported to sqlalchemy to enable mysql transition
Fix scroll by adding javascript to modals which gets rid of modal classes on click
fixed flash repeating bug
Added ingredient added flash message on add ingredients page
Switched to local mysql server and database for testing
Added short name to modify ingredient modal
Fixed no scroll bug: Add data-bs-dismiss="modal" to buttons that submit pushes from modals
Added flashes to rename and submit button in view ingredient modal
Finished fixing modal buttons to prevent scroll bug
Reduced payload of ingredients list in View Cocktail routes
Fixed amounts bug in user cocktails
Mysql transition complete. Now fixing bugs
Fixed the sql query problem in whatsmissing?
update database on button click in manage ingredients, remove submit button
Fixed spinner issues in the various view cocktail routes
Made Application into a package
Split off models and routes from init
Created forms.py and started converting to that for ease of use
Moved login and register to wtfforms
Moved addingredient and manageingredient-add to wtf
Moved Add cocktail to wtf
Added notes to cocktails
Added ingredient list and recipe columns to cocktails and common_cocktails for ease of loading
Changed View Common cocktails to use recipe and ingredient_list
Changed View User to use recipe and ingredient_list
Changed Viewall to use recipe and ingredient_list
Fixed bug in manageingredients search ba
Made amounts editable after selecting an ingredient in addcocktail
Changed Manage Ingredients-> View modal to use wtforms
Changed Manage->View->Modify to use wtforms and updated submit button to submit changes
Got rid of rename field and made name editable
Get new ingredient in Add cocktail to auto-add to the most recent ingredient and open a new one
Moved Whatstodrink and Whatsmissing to recipe/ingredient_list
Fixed rename cocktail for wtforms
Added sequence to database models and to write function in add cocktail
Added new modifycocktail.html
Added route for submitbutton
Added route for cancel, delete, and deleteconfirmed
Added view/edit My cocktails for wtforms
Fixed issue with eventHandlers in addcocktail
Made ingredient field in change recipe into search bar from add cocktail
Added reorder ingredients to change recipe and add cocktail
Made modify ingredient also modify recipe and ingredientlist for cocktails
Fixed modifycocktail to use short_name for ingredientlist
Fixed addcocktail to use short_name for ingredientlist
Fixed more ingredients in modify cocktail to correctly add drag handles to new field
Fixed view button in add ingredients when a search is typed but not entered
Fixed bug in whatsmissing that led to missing ingredients and duplicated cocktails
Added validation to modifyingredient by making a new route that renders the modal as a page
Did the same to modifycocktail
Added Ingredient name validators to addingredient modals
Fixed length of fields in modifyingredient

## In Progress

bug: next feature not working in login
bug: After creating a new ingredient in add cocktail cursor focus drops

## Todo 

Forgot password email

user modifiability to all ingredients (incl. hide)

Color/Theme/Prettify

implement tags: https://stackoverflow.com/questions/51128832/what-is-the-best-way-to-design-a-tag-based-data-table-with-sqlite
    - Add grouping options for cocktail views

recipe share page that opens a url like /cocktails-userid-cocktailid.html that can be created dynamically from the url
    -button to login to save to your cocktails
    -once logged in replace with save to your cocktails

make navbar active class work

Search Field for cocktail views