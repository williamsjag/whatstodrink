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
Added request password reset functionality with email
Updated layout of project to use blueprints
Changed project to use app factory model
Fixed bug in login page that eliminated flash messages
Fixed bug with next feature of login
Added cancel button to create ingredient modals and created addingredienterrors.html
Added validators to addingredient in addcocktail and made javascript ignore invalid ings when not in db
Added drag handle/remove icon/dragability to added ingredients in add cocktail
Fixed cancel button in areyousurecocktail to close modal to keep modifycocktailformerrors from loading view cocktails
Posted v 1.0 online!
Fixed another bug in whatsmissing where extra ingredients were being shown.
Fixed bug in settings not working due to moved route and hx-post
Added no cocktails indicator when a view is empty
Made ingredient list .9em to save space. Still need to deal with runover.
Made cocktail name verification only check user_id, not common, made sure cocktails are only ever accessed by id
Made cocktail views 2 column when screen wide enough
Made formatting change to make single column if only one family/sort in cocktail views
Combined viewcocktails and whatstodrink both user and common into cocktail_views
Fixed accordion headers to not overflow or cause name to split lines
Made ingredient_list ignore duplicates
Fixed notes and build in cocktail views to stay in column
Made missingone much more efficient in rendering.
Made notes field in modifyingredient fit the size of the field when rendered.
Made amounts fields in add and modify cocktail trim whitespace
Made addingredientmodal focus the first input on opening.
Shorten buttons on home screen and reduce margin when mobile screen.
Made it so capitalizing a letter in modify cocktail and ingredient doesn't trigger an error
Fixed problem with type in ingredienterrors form
Changed manageingredients to be case insensitive
Made altered ingredient selection carry over to modifycocktailerrors.
Made what's missing sort by number of cocktails in each ingredient.
Added search bar to whatstodrink and viewcocktails
Added search trigger for changing filter
Assured capitalization doesn't cause problems in cocktail search
Made cocktail filters persistent across button links in cocktail_views
Made view and wtd stay the same after enter is pressed instead of loading again.
Made it so modifycocktail redirects you to the branch you were on in the beginning.
Added punches to family options in modify-forms
Moved the flash message out of the for cocktail: loop in modifyingredient to eliminate duplicate flashes
Added cocktails list to view ingredient modal
Added back button to get from cocktails list to ingredient modal
Made flashed messages show the cocktail or ingredient being modified/deleted
Made cocktail accordions linkable and added view ingredient modal
Fixed ingredient_list so that it properly wraps when it reaches the name and doesn't add space to the button
Fixed error where session["defaults"] can be forgotten and left unhandled
Fix error where whatsmissing was not properly checking for the current user's stock
Formatted home screen for mobile
Formatted settings pane for mobile
Formatted explainers to disappear on mobile
Reduced gutter size on add cocktail to fit all elements on mobile
Made Modify Cocktail work on mobile

## In Progress

bug: Create new ingredient in add cocktail focuses x button
bug: Rename Aguil a azteca to Águil... 
    2024-06-05 18:01:20,251: TypeError: The view function did not return a valid response. The return type must be a string, dict, list, tuple with headers or status, Response instance, or WSGI callable, but it was a int.

figure out how to make search bar accent agnostic
    - works for ingredient search but not cocktail for some reason
  
Mobile formatting:
    - format cocktail accordions for mobile
    - check various modals for mobile formatting
        - Modify Cocktail done
    - check on [x] characters on mobile after clicking 'cocktails using'


## Todo 

user modifiability to all ingredients (incl. hide)

Color/Theme/Prettify

Cocktail filters:
    -Add plus button for additional filters

implement tags: https://stackoverflow.com/questions/51128832/what-is-the-best-way-to-design-a-tag-based-data-table-with-sqlite
    - Add grouping options for cocktail views
    - blended

recipe share page that opens a url like /cocktails-userid-cocktailid.html that can be created dynamically from the url
    -button to login to save to your cocktails
    -once logged in replace with save to your cocktails

Reports view- number of cocktails per ingredient, searchable using cocktail searches

user modifiability to all ingredients (incl. hide)