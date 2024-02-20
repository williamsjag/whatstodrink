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

## In Progress

Port database to MySQL and look into SQLAlchemy
    Leaving all old code commented out, to be cleaned up once it's clear everything works
    - login route finished
    - register finished
    - manage ingredients finished
    - modify ingredient finished

bug: manage ingreds page can't scroll after redirect after editing an ingredient


## Todo 

user modifiability to all ingredients (incl. hide)

ingredient added flash message on add ingredients page

add request indicators for slow htmx requests
    - still need to do type to search in manage
    - and type to search in add cocktail

Color/Theme/Prettify

add notes field for cocktails

implement tags: https://stackoverflow.com/questions/51128832/what-is-the-best-way-to-design-a-tag-based-data-table-with-sqlite
    - Add grouping options for cocktail views

recipe share page that opens a url like /cocktails-userid-cocktailid.html that can be created dynamically from the url
    -button to login to save to your cocktails
    -once logged in replace with save to your cocktails

make navbar active class work